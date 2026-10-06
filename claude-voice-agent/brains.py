"""Cérebros por assinatura: Codex, Cursor e Claude. Sem chave de API.

Cada um só entra se o CLI já está no PATH e logado na conta. Codex fica em
sandbox só de leitura. O Cursor imprime a fala e não recebe ``--force``.
O Claude continua no ``claude -p``, sem ferramentas extras.
"""

from __future__ import annotations

import json
import os
import pty
import re
import shutil
import signal
import subprocess
import threading
import time
from pathlib import Path

from .llm_claude_cli import render_prompt
from .personas import Persona
from .settings import Settings
from .speech import strip_for_speech

_ACT = (
    "\nSe precisar agir no computador, termine com uma única linha "
    "ACAO: seguida do comando. Não diga que já fez. Sem essa linha, só a fala. "
    "Não use ferramentas. Não edite arquivos."
)
_cursor_cache: dict[str, str | None] = {}


def _which(name: str) -> str | None:
    if not name:
        return None
    if os.path.sep in name:
        return name if os.access(name, os.X_OK) else None
    found = shutil.which(name)
    if found:
        return found
    home_bin = Path.home() / ".local" / "bin" / name
    if os.access(home_bin, os.X_OK):
        return str(home_bin)
    return None


_session_cache: dict[str, tuple[float, bool]] = {}
_login_lock = threading.Lock()
_logins: dict[str, dict] = {}
_ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]|\x1b\][^\x07]*\x07")
_URL = re.compile(r"https://[^\s<>\"')\]]+")
_CODE = re.compile(r"\b[A-Z0-9]{4,8}-[A-Z0-9]{4,8}\b")


def clear_session(path: str) -> None:
    """A próxima consulta de conta fala com o CLI de novo."""
    prefix = path + "\0"
    for key in list(_session_cache):
        if key.startswith(prefix):
            _session_cache.pop(key, None)


def _session_ready(kind: str, path: str) -> bool:
    """O CLI existe e a conta já está aberta. O resultado vale por alguns segundos."""
    now = time.monotonic()
    hit = _session_cache.get(path + "\0" + kind)
    if hit and now - hit[0] < 20:
        return hit[1]
    ok = False
    try:
        if kind == "claude":
            args = [path, "auth", "status"]
        elif kind == "codex":
            args = [path, "login", "status"]
        else:
            args = [path, "status"]
        proc = subprocess.run(args, capture_output=True, timeout=4, check=False)
        raw = (proc.stdout + proc.stderr).decode("utf-8", "replace")
        if kind == "claude" and proc.returncode == 0:
            try:
                ok = bool(json.loads(proc.stdout.decode("utf-8", "replace")).get("loggedIn"))
            except json.JSONDecodeError:
                ok = "not logged in" not in raw.lower()
        elif proc.returncode == 0:
            ok = "not logged in" not in raw.lower()
    except (OSError, subprocess.TimeoutExpired):
        ok = False
    _session_cache[path + "\0" + kind] = (now, ok)
    return ok


def brain_paths(settings: Settings) -> dict[str, str | None]:
    return {
        "codex": _which(settings.codex_cli),
        "cursor": cursor_binary(settings.cursor_cli),
        "claude": _which(settings.claude_cli),
    }


def brain_presence(settings: Settings) -> dict[str, str]:
    """``ready`` responde, ``login`` está instalado sem conta, ``down`` não está."""
    out: dict[str, str] = {}
    for key, path in brain_paths(settings).items():
        if not path:
            out[key] = "down"
        elif _session_ready(key, path):
            out[key] = "ready"
        else:
            out[key] = "login"
    return out


def _cursor_if_cursor(path: str) -> str | None:
    cached = _cursor_cache.get(path)
    if path in _cursor_cache:
        return cached
    try:
        proc = subprocess.run(
            [path, "--version"],
            capture_output=True,
            timeout=3,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        _cursor_cache[path] = None
        return None
    text = (proc.stdout + proc.stderr).decode("utf-8", "replace").lower()
    found = path if "cursor" in text else None
    _cursor_cache[path] = found
    return found


def cursor_binary(preferred: str) -> str | None:
    """O CLI do Cursor. Um binário chamado ``agent`` só vale se a versão diz Cursor."""
    found = _which(preferred) if preferred else None
    if found and Path(found).name != "agent":
        return found
    named = _which("cursor-agent")
    if named:
        return named
    agent = found if found and Path(found).name == "agent" else _which("agent")
    if agent:
        return _cursor_if_cursor(agent)
    return None


def probe_subscriptions(settings: Settings) -> list[dict]:
    """Presença dos três CLIs. ``up`` só quando a conta já responde."""
    labels = {"codex": "Codex", "cursor": "Cursor", "claude": "Claude"}
    presence = brain_presence(settings)
    return [
        {"id": key, "label": labels[key], "up": presence[key] == "ready", "auth": presence[key]}
        for key in ("codex", "cursor", "claude")
    ]


def _clean_login(text: str) -> str:
    return _ANSI.sub("", text)


def _harvest_login(slot: dict, line: str) -> None:
    text = _clean_login(line)
    slot["blob"] += text + "\n"
    if not slot["url"]:
        found = _URL.search(text)
        if found:
            slot["url"] = found.group(0).rstrip(".,")
    if not slot["code"]:
        found = _CODE.search(text)
        if found:
            slot["code"] = found.group(0)
    if "paste code" in text.lower():
        slot["needs_code"] = True


def _read_login(slot: dict) -> None:
    fd = slot["fd"]
    buf = ""
    try:
        while True:
            try:
                chunk = os.read(fd, 4096)
            except OSError:
                break
            if not chunk:
                break
            buf += chunk.decode("utf-8", "replace")
            buf = buf.replace("\r\n", "\n").replace("\r", "\n")
            while "\n" in buf:
                line, buf = buf.split("\n", 1)
                with _login_lock:
                    _harvest_login(slot, line)
            if buf and "paste code" in _clean_login(buf).lower():
                with _login_lock:
                    slot["needs_code"] = True
        if buf:
            with _login_lock:
                _harvest_login(slot, buf)
    finally:
        clear_session(slot.get("cli") or "")
        try:
            os.close(fd)
        except OSError:
            pass
        slot["fd"] = -1


def _login_stale(slot: dict) -> bool:
    if slot["kind"] != "codex":
        return False
    return time.monotonic() - slot["started"] > 14 * 60


def _stop_login(slot: dict) -> None:
    proc = slot["proc"]
    if proc.poll() is not None:
        return
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except OSError:
        proc.terminate()
    try:
        proc.wait(timeout=2)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except OSError:
            proc.kill()


def _spawn_login(kind: str, cli: str) -> dict:
    if kind == "codex":
        args = [cli, "login", "--device-auth"]
    elif kind == "claude":
        args = [cli, "auth", "login", "--claudeai"]
    else:
        args = [cli, "login"]
    env = os.environ.copy()
    env["NO_OPEN_BROWSER"] = "1"
    master, slave = pty.openpty()
    try:
        proc = subprocess.Popen(
            args,
            stdin=slave,
            stdout=slave,
            stderr=slave,
            env=env,
            start_new_session=True,
        )
    except OSError:
        os.close(master)
        os.close(slave)
        raise
    os.close(slave)
    slot = {
        "kind": kind,
        "cli": cli,
        "proc": proc,
        "fd": master,
        "url": "",
        "code": "",
        "needs_code": False,
        "blob": "",
        "started": time.monotonic(),
    }
    threading.Thread(target=_read_login, args=(slot,), name=f"login-{kind}", daemon=True).start()
    return slot


def _wait_login(slot: dict, seconds: float) -> None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        with _login_lock:
            if slot["kind"] == "codex":
                ready = bool(slot["url"] and slot["code"])
            elif slot["kind"] == "claude":
                ready = bool(slot["url"] and (slot["needs_code"] or slot["code"]))
            else:
                ready = bool(slot["url"])
            dead = slot["proc"].poll() is not None
        if ready or dead:
            return
        time.sleep(0.05)


def _login_view(slot: dict) -> dict[str, str | bool]:
    return {
        "url": slot["url"],
        "code": slot["code"],
        "needs_code": bool(slot["needs_code"] and slot["proc"].poll() is None and not slot["code"]),
    }


def begin_login(kind: str, cli: str) -> dict[str, str | bool]:
    """Abre o login do CLI e devolve o endereço. O mesmo processo vale até expirar."""
    empty: dict[str, str | bool] = {"url": "", "code": "", "needs_code": False}
    try:
        with _login_lock:
            slot = _logins.get(kind)
            if slot and slot["proc"].poll() is None and not _login_stale(slot):
                pending = slot
            else:
                if slot:
                    _stop_login(slot)
                pending = _spawn_login(kind, cli)
                _logins[kind] = pending
    except OSError:
        return empty
    _wait_login(pending, 8.0)
    with _login_lock:
        return _login_view(pending)


def login_snapshot() -> dict[str, dict[str, str | bool]]:
    """Logins já abertos, sem disparar outro processo."""
    out: dict[str, dict[str, str | bool]] = {}
    with _login_lock:
        for kind, slot in _logins.items():
            if _login_stale(slot):
                continue
            if not slot["url"] and slot["proc"].poll() is not None:
                continue
            out[kind] = _login_view(slot)
    return out


def submit_login_code(kind: str, code: str) -> bool:
    """Entrega o código que o Claude pediu para colar."""
    token = (code or "").strip()
    if not token or any(ch.isspace() for ch in token) or len(token) > 400:
        return False
    with _login_lock:
        slot = _logins.get(kind)
        fd = slot["fd"] if slot else -1
        if not slot or fd < 0 or slot["proc"].poll() is not None:
            return False
        try:
            os.write(fd, (token + "\n").encode("utf-8"))
        except OSError:
            return False
        slot["needs_code"] = False
        return True


def _prompt(persona: Persona, history: list[tuple[str, str]], cleaned: str) -> tuple[str, str]:
    user = cleaned or "(o usuário chamou você pelo nome)"
    turns = [("system", persona.system_prompt() + _ACT), *history, ("user", user)]
    return render_prompt(turns, assistant_label=persona.name)


def _run(args: list[str], *, stdin: bytes | None, timeout: float) -> str:
    proc = subprocess.run(
        args,
        input=stdin,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    text = proc.stdout.decode("utf-8", "replace").strip()
    if proc.returncode != 0:
        err = proc.stderr.decode("utf-8", "replace").strip() or text or "sem saída"
        raise RuntimeError(f"{args[0]} retornou {proc.returncode}: {err}")
    return text


def ask_codex(cli: str, prompt: str, system: str, *, timeout: float = 40.0) -> str:
    """``codex exec`` na assinatura do ChatGPT. Sandbox só de leitura."""
    body = (system + "\n\n" + prompt).strip().encode("utf-8")
    return _run(
        [
            cli,
            "exec",
            "--ephemeral",
            "--skip-git-repo-check",
            "--sandbox",
            "read-only",
            "-",
        ],
        stdin=body,
        timeout=timeout,
    )


def ask_cursor(cli: str, prompt: str, system: str, *, timeout: float = 40.0) -> str:
    """CLI do Cursor, modo impressão, sem ``--force``."""
    body = (system + "\n\n" + prompt).strip()
    return _run(
        [cli, "-p", "--mode", "ask", "--trust", "--output-format", "text", body],
        stdin=None,
        timeout=timeout,
    )


def ask_claude_cli(
    cli: str,
    prompt: str,
    system: str,
    model: str | None,
    *,
    timeout: float = 40.0,
) -> str:
    """``claude -p`` na assinatura da Anthropic."""
    args = [cli, "-p", prompt, "--output-format", "text"]
    if system:
        args += ["--append-system-prompt", system]
    if model:
        args += ["--model", model]
    return _run(args, stdin=None, timeout=timeout)


def subscription_reply(
    settings: Settings,
    persona: Persona,
    history: list[tuple[str, str]],
    cleaned: str,
    *,
    timeout: float = 40.0,
    prefer: str | None = None,
) -> str | None:
    """A primeira assinatura que responder. Codex, depois Cursor, depois Claude.

    Com ``prefer``, só aquele cérebro responde. Ausente devolve None.
    """
    prompt, system = _prompt(persona, history, cleaned)
    paths = brain_paths(settings)
    order = (
        ("codex", paths["codex"], lambda cli: ask_codex(cli, prompt, system, timeout=timeout)),
        ("cursor", paths["cursor"], lambda cli: ask_cursor(cli, prompt, system, timeout=timeout)),
        (
            "claude",
            paths["claude"],
            lambda cli: ask_claude_cli(
                cli, prompt, system, settings.llm_model, timeout=timeout
            ),
        ),
    )
    if prefer:
        order = tuple(row for row in order if row[0] == prefer)
    for name, path, call in order:
        if not path or not _session_ready(name, path):
            continue
        try:
            spoken = strip_for_speech(call(path))
        except (OSError, subprocess.TimeoutExpired, RuntimeError):
            continue
        if spoken:
            return spoken
    return None
