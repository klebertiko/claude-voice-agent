"""Funções da casa: clima, notícias, busca, lembrete e WhatsApp.

Nada disto abre o computador sozinho. Busca sem resposta e WhatsApp viram
uma ordem ``ACAO:`` e o painel pede permissão. Sem câmera e sem gerar imagem.
"""

from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

_SAO_PAULO = (-23.55, -46.63, "São Paulo")
_NEWS = "https://news.google.com/rss?hl=pt-BR&gl=BR&ceid=BR:pt-419"
_WX = {
    0: "céu limpo",
    1: "quase limpo",
    2: "parcialmente nublado",
    3: "nublado",
    45: "neblina",
    48: "neblina",
    51: "garoa",
    53: "garoa",
    55: "garoa forte",
    61: "chuva",
    63: "chuva",
    65: "chuva forte",
    71: "neve",
    80: "pancadas",
    81: "pancadas",
    82: "pancadas fortes",
    95: "trovoada",
}


def _plain(text: str) -> str:
    import unicodedata

    folded = unicodedata.normalize("NFKD", (text or "").lower())
    stripped = "".join(ch for ch in folded if not unicodedata.combining(ch))
    return " ".join(stripped.split())


def _http_get(url: str, timeout: float = 4.0) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "orion-house"})
    with urllib.request.urlopen(req, timeout=timeout) as res:
        return res.read().decode("utf-8", "replace")


def _load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    return data if isinstance(data, list) else []


def _save(path: Path, items: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")


def _weather(place: str, fetch) -> str:
    name = place.strip() or _SAO_PAULO[2]
    lat, lon, label = _SAO_PAULO
    if place.strip():
        geo = json.loads(
            fetch(
                "https://geocoding-api.open-meteo.com/v1/search?count=1&language=pt&format=json&name="
                + urllib.parse.quote(place.strip())
            )
        )
        hit = (geo.get("results") or [None])[0]
        if not hit:
            return "Não achei essa cidade, Senhor."
        lat, lon, label = hit["latitude"], hit["longitude"], hit.get("name") or name
    url = (
        "https://api.open-meteo.com/v1/forecast?current=temperature_2m,weather_code"
        f"&latitude={lat}&longitude={lon}&timezone=America%2FSao_Paulo"
    )
    data = json.loads(fetch(url))
    current = data.get("current") or {}
    temp = current.get("temperature_2m")
    if temp is None:
        return "Não alcancei o clima, Senhor."
    sky = _WX.get(int(current.get("weather_code") or 0), "instável")
    graus = int(round(float(temp)))
    return f"Em {label}, {graus} graus, {sky}, Senhor."


def _news(fetch) -> str:
    raw = fetch(_NEWS)
    root = ET.fromstring(raw)
    titles = []
    for node in root.iter("title"):
        text = " ".join((node.text or "").split())
        if not text or text.lower().startswith("google news"):
            continue
        titles.append(text)
        if len(titles) == 2:
            break
    if not titles:
        return "Não alcancei as notícias, Senhor."
    return "Nas notícias, Senhor. " + ". ".join(titles) + "."


def _search(query: str, fetch) -> str:
    query = query.strip(" ?.")
    if not query:
        return "O que devo procurar, Senhor?"
    url = "https://api.duckduckgo.com/?format=json&no_html=1&skip_disambig=1&q=" + urllib.parse.quote(query)
    data = json.loads(fetch(url))
    abstract = (data.get("AbstractText") or data.get("Answer") or "").strip()
    if abstract:
        sentence = abstract.split(". ")[0].strip().rstrip(".")
        if len(sentence) > 160:
            sentence = sentence[:157].rsplit(" ", 1)[0]
        return f"{sentence}, Senhor."
    opened = "https://duckduckgo.com/?q=" + urllib.parse.quote(query)
    return f"ACAO: xdg-open '{opened}'"


def _remember(note: str, path: Path, moment: datetime) -> str:
    note = note.strip(" .")
    if not note:
        return "O que devo anotar, Senhor?"
    items = _load(path)
    items.append({"text": note, "at": moment.isoformat(timespec="minutes")})
    _save(path, items[-20:])
    return "Anotado, Senhor."


def _list_notes(path: Path) -> str:
    items = _load(path)
    if not items:
        return "Nada anotado, Senhor."
    last = items[-2:]
    spoken = ". ".join(item["text"] for item in last)
    return f"Lembretes, Senhor. {spoken}."


def _wants_weather(norm: str) -> bool:
    if "faz tempo" in norm:
        return False
    if norm.startswith(("tempo em ", "clima em ", "clima ", "previsao ")):
        return True
    if norm in {
        "clima", "tempo", "previsao", "o tempo", "o clima", "tempo agora",
        "qual o tempo", "qual e o tempo",
    }:
        return True
    if "que tempo" in norm or "previsao" in norm or "qual o tempo" in norm:
        return True
    return (
        "como esta o tempo" in norm
        or "como esta o clima" in norm
        or "como ta o tempo" in norm
    )


def _whatsapp(text: str) -> str:
    plain = _plain(text)
    number = re.search(r"(\d{10,13})", plain)
    if not number:
        return "Diga o número, Senhor."
    said_match = re.search(r"dizendo\s+(.+)$", text, flags=re.IGNORECASE)
    said = said_match.group(1).strip(" .") if said_match else ""
    if not said:
        return "O que devo escrever, Senhor?"
    link = "https://wa.me/" + number.group(1) + "?text=" + urllib.parse.quote(said)
    return f"ACAO: xdg-open '{link}'"


def house_reply(
    text: str,
    moment: datetime,
    *,
    reminders_path: Path,
    fetch=None,
) -> str | None:
    """Resposta da casa, ou None se o pedido não é uma destas funções."""
    norm = _plain(text)
    if not norm:
        return None
    fetch = fetch or _http_get
    try:
        if re.search(r"\bcamera\b", norm):
            return "Não uso câmera, Senhor."
        if "gere uma imagem" in norm or "crie uma imagem" in norm or "gere a imagem" in norm:
            return "Ainda não gero imagem aqui, Senhor."
        if "whatsapp" in norm or norm.startswith("zap ") or " no zap " in f" {norm} ":
            return _whatsapp(text)
        if norm in {"resumo do dia", "briefing", "como esta o dia", "como vai o dia"}:
            clock_h = moment.hour
            sky = _weather("", fetch)
            return f"São {clock_h} horas, Senhor. {sky}"
        if norm.startswith(("lembrete ", "me lembre de ", "me lembra de ", "anote ", "anota ")):
            match = re.search(
                r"(?:me lembre de|me lembra de|lembrete|anote|anota)\s+(.+)$",
                text.strip(),
                flags=re.IGNORECASE,
            )
            return _remember(match.group(1) if match else "", reminders_path, moment)
        if norm in {"quais lembretes", "meus lembretes", "o que anotei"}:
            return _list_notes(reminders_path)
        if norm.startswith(("tempo em ", "clima em ")):
            place = norm.split(" em ", 1)[1]
            return _weather(place, fetch)
        if _wants_weather(norm):
            return _weather("", fetch)
        if "noticia" in norm or "noticias" in norm or "o que esta acontecendo" in norm:
            return _news(fetch)
        for prefix in ("pesquise ", "busque ", "procure "):
            if norm.startswith(prefix):
                return _search(norm[len(prefix) :], fetch)
    except (OSError, ValueError, json.JSONDecodeError, ET.ParseError, KeyError, TimeoutError):
        return "Não alcancei isso agora, Senhor."
    return None
