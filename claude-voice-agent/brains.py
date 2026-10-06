"""Cérebros por assinatura: Codex, Cursor e Claude. Sem chave de API.

Cada um só entra se o CLI já está no PATH e logado na conta. Codex fica em
sandbox só de leitura. O Cursor imprime a fala e não recebe ``--force``.
O Claude continua no ``claude -p``, sem ferramentas extras.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
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
