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
    name = place.strip(" .?")
    if not name:
        return "De qual lugar, Senhor."
    geo = json.loads(
        fetch(
            "https://geocoding-api.open-meteo.com/v1/search?count=1&language=pt&format=json&name="
            + urllib.parse.quote(name)
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


def _news(topic: str, fetch) -> str:
    topic = topic.strip(" .?")
    if not topic:
        return "Sobre o que, Senhor."
    url = (
        "https://news.google.com/rss/search?hl=pt-BR&gl=BR&ceid=BR:pt-419&q="
        + urllib.parse.quote(topic)
    )
    raw = fetch(url)
    root = ET.fromstring(raw)
    titles = []
    for item in root.iter("item"):
        node = item.find("title")
        text = " ".join(((node.text if node is not None else "") or "").split())
        if not text or "google not" in text.lower():
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


def note_query_of(heard: str, reply: str) -> str:
    """Assunto que o céu destaca. Vazio quando a fala não buscou nas notas."""
    if reply != "Não há nota com isso, Senhor." and not (reply or "").startswith("Nas notas, Senhor."):
        return ""
    norm = _plain(heard)
    if norm.startswith("buscar nota "):
        return norm.split(" ", 2)[-1].strip()
    if norm.startswith("notas sobre "):
        return norm[len("notas sobre ") :].strip()
    return norm


def _find_notes(query: str, path: Path) -> str:
    """Busca nas notas, como a busca do Obsidian. Não abre a web."""
    needle = _plain(query)
    if not needle:
        return "O que devo buscar nas notas, Senhor?"
    hits = []
    for item in _load(path):
        if not isinstance(item, dict):
            continue
        text = " ".join(str(item.get("text") or "").split())
        if text and needle in _plain(text):
            hits.append(text)
    if not hits:
        return "Não há nota com isso, Senhor."
    return "Nas notas, Senhor. " + ". ".join(hits[:3]) + "."


def _list_notes(path: Path) -> str:
    spoken = []
    for item in _load(path):
        if not isinstance(item, dict):
            continue
        text = " ".join(str(item.get("text") or "").split())
        if text:
            spoken.append(text)
    if not spoken:
        return "Nada anotado, Senhor."
    return "Lembretes, Senhor. " + ". ".join(spoken) + "."


def _place_of(norm: str) -> str:
    for prefix in (
        "tempo em ", "clima em ", "previsao em ", "previsao para ",
        "clima de ", "tempo de ", "clima no ", "tempo no ", "clima na ", "tempo na ",
    ):
        if norm.startswith(prefix):
            return norm[len(prefix) :].strip(" .")
    match = re.search(r"\b(?:tempo|clima|previsao)\s+em\s+(.+)$", norm)
    if match:
        return match.group(1).strip(" .")
    return ""


def _topic_of(norm: str) -> str:
    for prefix in (
        "noticias sobre ", "noticia sobre ",
        "noticias de ", "noticia de ",
        "noticias do ", "noticia do ",
        "noticias da ", "noticia da ",
        "o que esta acontecendo em ",
        "o que esta acontecendo sobre ",
    ):
        if norm.startswith(prefix):
            return norm[len(prefix) :].strip(" .")
    match = re.search(r"noticias?\s+(?:sobre|de|do|da)\s+(.+)$", norm)
    if match:
        return match.group(1).strip(" .")
    return ""


def _answer_text(text: str) -> str:
    norm = _plain(text)
    for prefix in ("em ", "no ", "na ", "de ", "sobre ", "do ", "da "):
        if norm.startswith(prefix):
            return text.strip()[len(prefix) :].strip() or norm[len(prefix) :].strip()
    return text.strip()


def continue_house(
    kind: str,
    text: str,
    *,
    fetch=None,
    reminders_path: Path | None = None,
    moment: datetime | None = None,
) -> str:
    """A resposta curta depois de Orion pedir lugar, assunto, busca ou nota."""
    fetch = fetch or _http_get
    said = _answer_text(text)
    try:
        if kind == "weather":
            return _weather(said, fetch)
        if kind == "news":
            return _news(said, fetch)
        if kind == "search":
            return _search(said, fetch)
        if kind == "note" and reminders_path is not None and moment is not None:
            return _remember(text, reminders_path, moment)
        if kind == "notes" and reminders_path is not None:
            return _find_notes(text, reminders_path)
    except (OSError, ValueError, json.JSONDecodeError, ET.ParseError, KeyError, TimeoutError):
        return "Não alcancei isso agora, Senhor."
    return "Não entendi, Senhor."


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


def whatsapp_number(text: str) -> str:
    """Telefone de 10 a 13 dígitos, com espaço, traço ou parêntese."""
    raw = _plain(text)
    match = re.search(r"\d(?:[\d\s().-]{8,20})\d", raw)
    if not match:
        return ""
    digits = re.sub(r"\D", "", match.group(0))
    if 10 <= len(digits) <= 13:
        return digits
    return ""


def continue_whatsapp(stage: str, text: str, number: str) -> tuple[str, str]:
    """A frase seguinte depois de Orion pedir o número ou o texto."""
    if stage == "zap-number":
        found = whatsapp_number(text)
        if not found:
            return "Diga o número, Senhor.", ""
        said_match = re.search(r"dizendo\s+(.+)$", text, flags=re.IGNORECASE)
        said = said_match.group(1).strip(" .") if said_match else ""
        if said:
            link = "https://wa.me/" + found + "?text=" + urllib.parse.quote(said)
            return f"ACAO: xdg-open '{link}'", ""
        return "O que devo escrever, Senhor?", found
    said = (text or "").strip(" .")
    if not said or not number:
        return "O que devo escrever, Senhor?", number
    link = "https://wa.me/" + number + "?text=" + urllib.parse.quote(said)
    return f"ACAO: xdg-open '{link}'", ""


def _whatsapp(text: str) -> str:
    number = whatsapp_number(text)
    if not number:
        return "Diga o número, Senhor."
    said_match = re.search(r"dizendo\s+(.+)$", text, flags=re.IGNORECASE)
    said = said_match.group(1).strip(" .") if said_match else ""
    if not said:
        return "O que devo escrever, Senhor?"
    link = "https://wa.me/" + number + "?text=" + urllib.parse.quote(said)
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
            sky = _weather("São Paulo", fetch)
            return f"São {clock_h} horas, Senhor. {sky}"
        if norm in {"anote", "anota", "lembrete"}:
            return "O que devo anotar, Senhor?"
        if norm.startswith(("lembrete ", "me lembre de ", "me lembra de ", "anote ", "anota ")):
            match = re.search(
                r"(?:me lembre de|me lembra de|lembrete|anote|anota)\s+(.+)$",
                text.strip(),
                flags=re.IGNORECASE,
            )
            return _remember(match.group(1) if match else "", reminders_path, moment)
        if norm in {"quais lembretes", "meus lembretes", "o que anotei"}:
            return _list_notes(reminders_path)
        if _wants_weather(norm):
            place = _place_of(norm)
            if not place:
                return "De qual lugar, Senhor."
            return _weather(place, fetch)
        if "noticia" in norm or norm == "o que esta acontecendo":
            topic = _topic_of(norm)
            if not topic:
                return "Sobre o que, Senhor."
            return _news(topic, fetch)
        if norm in {"busque", "pesquise", "procure", "busca", "pesquisa"}:
            return "O que devo procurar, Senhor?"
        if norm in {"buscar nota", "notas sobre"}:
            return "O que devo buscar nas notas, Senhor?"
        if norm.startswith("buscar nota ") or norm.startswith("notas sobre "):
            query = norm.split(" ", 2)[-1] if norm.startswith("buscar nota ") else norm[len("notas sobre ") :]
            return _find_notes(query, reminders_path)
        for prefix in ("pesquise ", "busque ", "procure "):
            if norm.startswith(prefix):
                return _search(norm[len(prefix) :], fetch)
    except (OSError, ValueError, json.JSONDecodeError, ET.ParseError, KeyError, TimeoutError):
        return "Não alcancei isso agora, Senhor."
    return None
