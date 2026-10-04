"""Cérebro local via Ollama. Sem chave, na máquina da pessoa.

Se o serviço não responde, o chamador segue para o outro cérebro.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request


def probe_ollama(host: str, timeout: float = 0.4) -> dict:
    """``{up, model, models}``. Model é o primeiro instalado, ou None."""
    url = host.rstrip("/") + "/api/tags"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as res:
            data = json.loads(res.read().decode("utf-8"))
    except (OSError, urllib.error.URLError, ValueError, json.JSONDecodeError, TimeoutError):
        return {"up": False, "model": None, "models": []}
    names = [m.get("name", "") for m in data.get("models") or [] if m.get("name")]
    return {"up": True, "model": names[0] if names else None, "models": names}


def ask_ollama(
    host: str,
    model: str,
    system: str,
    history: list[tuple[str, str]],
    user: str,
    timeout: float = 45.0,
) -> str:
    """Uma resposta. A última linha ``ACAO:`` pede uma ordem, não a executa."""
    messages = [
        {
            "role": "system",
            "content": (
                system
                + "\nSe precisar agir no computador, termine com uma única linha "
                "ACAO: seguida do comando. Não diga que já fez. Sem essa linha, só a fala."
            ),
        }
    ]
    for role, content in history:
        messages.append(
            {"role": "user" if role == "user" else "assistant", "content": content}
        )
    messages.append({"role": "user", "content": user or "Diga, Senhor."})
    body = json.dumps({"model": model, "messages": messages, "stream": False}).encode("utf-8")
    req = urllib.request.Request(
        host.rstrip("/") + "/api/chat",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as res:
        data = json.loads(res.read().decode("utf-8"))
    return ((data.get("message") or {}).get("content") or "").strip()
