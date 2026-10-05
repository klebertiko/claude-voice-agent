"""Céu do Orion: as notas viram estrelas. Nada aqui lê o disco da pessoa.

O grafo sai só dos lembretes gravados. Palavras vazias não criam ligação.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

_STOP = {
    "para",
    "como",
    "isso",
    "esta",
    "esse",
    "essa",
    "pelo",
    "pela",
    "mais",
    "sobre",
    "entre",
    "depois",
    "antes",
    "senhor",
    "orion",
    "quando",
    "onde",
    "porque",
    "muito",
    "ainda",
    "tambem",
    "voce",
    "aqui",
    "hoje",
    "amanha",
}


def _plain(text: str) -> str:
    import unicodedata

    folded = unicodedata.normalize("NFKD", (text or "").lower())
    stripped = "".join(ch for ch in folded if not unicodedata.combining(ch))
    return " ".join(stripped.split())


def _load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    return data if isinstance(data, list) else []


def _words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]{4,}", _plain(text)) if w not in _STOP}


def memory_sky(path: Path) -> dict:
    """Estrelas e ligações das notas. Lista vazia se ainda não há nada anotado."""
    stars = []
    bags: list[set[str]] = []
    for index, item in enumerate(_load(path)[-24:]):
        if not isinstance(item, dict):
            continue
        text = " ".join(str(item.get("text") or "").split())
        if not text:
            continue
        star_id = f"n{index}"
        stars.append(
            {
                "id": star_id,
                "label": text if len(text) <= 42 else text[:39].rsplit(" ", 1)[0] + "…",
                "text": text,
                "kind": "nota",
            }
        )
        bags.append(_words(text))
    links = []
    for i in range(len(stars)):
        for j in range(i + 1, len(stars)):
            if bags[i] & bags[j]:
                links.append({"a": stars[i]["id"], "b": stars[j]["id"]})
    return {"stars": stars, "links": links}
