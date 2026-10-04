"""Mãos do Orion: propõe uma ordem e só corre depois da permissão.

A fala pode pedir um comando. Nada é executado aqui sem um sim explícito
do painel. O texto da ordem volta inteiro para a pessoa ler.
"""

from __future__ import annotations

import subprocess
import unicodedata
from pathlib import Path

PERMIT_SPOKEN = "Posso executar isto, Senhor?"
DENY_SPOKEN = "Não fiz, Senhor."
_EXEC = ("execute ", "executa ", "executar ", "rode ", "roda ", "rodar ", "corra ")
_LIST = {
    "liste os arquivos",
    "liste a pasta",
    "listar arquivos",
    "o que tem aqui",
    "o que tem na pasta",
}


def _plain(text: str) -> str:
    folded = unicodedata.normalize("NFKD", (text or "").lower())
    stripped = "".join(ch for ch in folded if not unicodedata.combining(ch))
    return " ".join(stripped.split())


def clean_command(command: str) -> str | None:
    """Recusa ordem vazia, com quebra de linha ou longa demais."""
    cmd = (command or "").strip().strip("`").strip()
    if not cmd or "\n" in cmd or "\r" in cmd or len(cmd) > 400:
        return None
    return cmd


def local_command(text: str) -> str | None:
    """Pedido explícito de execução, sem passar pelo cérebro."""
    raw = (text or "").strip()
    plain = _plain(raw)
    if plain in _LIST:
        return "ls"
    for prefix in _EXEC:
        if plain.startswith(prefix):
            rest = plain[len(prefix) :].strip()
            return clean_command(rest)
    return None


def extract_proposal(reply: str) -> str | None:
    """A linha ``ACAO: comando`` é um pedido, não uma fala."""
    for line in (reply or "").splitlines():
        stripped = line.strip()
        if stripped.upper().startswith("ACAO:"):
            return clean_command(stripped.split(":", 1)[1])
    return None


def speak_result(code: int, output: str) -> str:
    """Uma linha falável. O resto fica no painel."""
    if code != 0:
        return "Falhou, Senhor."
    lines = [line.strip() for line in (output or "").splitlines() if line.strip()]
    if len(lines) == 1 and len(lines[0]) <= 80 and "://" not in lines[0]:
        return f"Feito, Senhor. {lines[0]}"
    return "Feito, Senhor."


def run_command(command: str, cwd: Path, timeout: float = 20.0) -> tuple[int, str]:
    """Corre a ordem já autorizada. Devolve código e texto combinado."""
    cmd = clean_command(command)
    if cmd is None:
        return 1, ""
    try:
        proc = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return 124, "tempo esgotado"
    out = ((proc.stdout or "") + (proc.stderr or "")).strip()
    if len(out) > 4000:
        out = out[:4000] + "\n…"
    return proc.returncode, out
