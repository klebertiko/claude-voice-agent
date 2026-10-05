"""Cérebros por assinatura: Codex, Cursor e Claude. Sem chave de API.

Cada um só entra se o CLI já está no PATH e logado na conta. Codex fica em
sandbox só de leitura. O Cursor imprime a fala e não recebe ``--force``.
O Claude continua no ``claude -p``, sem ferramentas extras.
"""

from __future__ import annotations

import shutil
import subprocess
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
    return shutil.which(name)


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
    """Presença dos três CLIs. ``up`` é o binário, não uma prova de login."""
    rows = (
        ("codex", "Codex", _which(settings.codex_cli)),
        ("cursor", "Cursor", cursor_binary(settings.cursor_cli)),
        ("claude", "Claude", _which(settings.claude_cli)),
    )
    return [{"id": key, "label": label, "up": bool(path)} for key, label, path in rows]


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
    if proc.returncode != 0 and not text:
        err = proc.stderr.decode("utf-8", "replace").strip() or "sem saída"
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
        [cli, "-p", "--output-format", "text", body],
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
    order = (
        ("codex", _which(settings.codex_cli), lambda cli: ask_codex(cli, prompt, system, timeout=timeout)),
        ("cursor", cursor_binary(settings.cursor_cli), lambda cli: ask_cursor(cli, prompt, system, timeout=timeout)),
        (
            "claude",
            _which(settings.claude_cli),
            lambda cli: ask_claude_cli(
                cli, prompt, system, settings.llm_model, timeout=timeout
            ),
        ),
    )
    if prefer:
        order = tuple(row for row in order if row[0] == prefer)
    for _name, path, call in order:
        if not path:
            continue
        try:
            spoken = strip_for_speech(call(path))
        except (OSError, subprocess.TimeoutExpired, RuntimeError):
            continue
        if spoken:
            return spoken
    return None
