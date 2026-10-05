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


def _note_text(note: str) -> str:
    """Tira o convite. «aí comprar leite» vira «comprar leite»."""
    raw = (note or "").strip(" .")
    while raw:
        plain = _plain(raw)
        dropped = False
        if plain in {"ai", "isso", "que", "por favor", "por gentileza", "para mim", "pra mim", "o seguinte"}:
            return ""
        for filler in (
            "ai ", "isso ", "que ", "por favor ", "por gentileza ",
            "para mim ", "pra mim ", "o seguinte ", "amanha de ",
        ):
            if plain.startswith(filler):
                words = len(filler.split())
                raw = " ".join(raw.split()[words:]).strip(" .")
                dropped = True
                break
        if not dropped:
            break
    return raw


_REMEMBER_PREFIXES = (
    "nao me deixa esquecer de ",
    "nao esquece de ",
    "esquece de ",
    "me lembre de ",
    "me lembra de ",
    "me lembre ",
    "me lembra ",
    "lembrete ",
    "lembra de ",
    "lembra ",
    "anote ",
    "anota ",
)


def _remember_body(text: str) -> str:
    """O que anotar, sem o verbo. Os acentos do resto ficam."""
    norm = _plain(text)
    words = (text or "").strip().split()
    for prefix in _REMEMBER_PREFIXES:
        if norm.startswith(prefix):
            return " ".join(words[len(prefix.split()) :])
    return ""


def _remember(note: str, path: Path, moment: datetime) -> str:
    note = _note_text(note)
    if not note:
        return "O que devo anotar, Senhor?"
    items = _load(path)
    items.append({"text": note, "at": moment.isoformat(timespec="minutes")})
    _save(path, items[-20:])
    return "Anotado, Senhor."


def _clean_subject(subject: str) -> str:
    """Tira o convite e o artigo. «alguma coisa sobre o projeto» vira «projeto»."""
    subject = (subject or "").strip()
    changed = True
    while subject and changed:
        changed = False
        for prefix in (
            "alguma coisa sobre ", "alguma coisa de ", "alguma coisa do ", "alguma coisa da ",
            "algo sobre ", "algo de ", "algo do ", "algo da ",
            "alguma coisa ", "algo ",
            "o ", "a ", "os ", "as ", "um ", "uma ",
        ):
            if subject.startswith(prefix):
                rest = subject[len(prefix) :].strip()
                if rest:
                    subject = rest
                    changed = True
                    break
    if subject in {"alguma coisa", "algo", "sobre", "de", "do", "da"}:
        return ""
    return subject


def _note_subject(norm: str) -> str | None:
    """Assunto da busca nas notas. None quando a fala não é essa busca."""
    if norm in {
        "buscar nota", "notas sobre", "notas de", "notas do", "notas da",
        "buscar nas notas", "busque nas notas", "busca nas notas",
        "procurar nas notas", "procure nas notas", "procura nas notas",
        "pesquisar nas notas", "pesquise nas notas", "pesquisa nas notas",
        "buscar nas minhas notas", "busque nas minhas notas", "busca nas minhas notas",
        "procurar nas minhas notas", "procure nas minhas notas", "procura nas minhas notas",
        "pesquisar nas minhas notas", "pesquise nas minhas notas", "pesquisa nas minhas notas",
        "nas notas", "tem nota", "tem nota sobre", "tem alguma nota",
        "alguma nota", "uma nota",
        "tem alguma coisa nas notas", "tem algo nas notas",
        "nas minhas notas", "nas minhas notas tem",
        "o que anotei sobre", "o que eu anotei sobre",
    }:
        return ""
    if norm.startswith("buscar nota "):
        return _clean_subject(norm.split(" ", 2)[-1])
    owned = re.match(r"^notas\s+(?:sobre|de|do|da)\s+(.+)$", norm)
    if owned:
        return _clean_subject(owned.group(1))
    verb = r"(?:buscar|busque|busca|procurar|procure|procura|pesquisar|pesquise|pesquisa)"
    found = re.match(
        rf"^{verb}\s+nas\s+(?:minhas\s+)?notas(?:\s+(.*))?$",
        norm,
    )
    if found:
        return _clean_subject(found.group(1) or "")
    tail = re.match(
        rf"^{verb}\s+(.+?)\s+nas\s+(?:minhas\s+)?notas$",
        norm,
    )
    if tail:
        return _clean_subject(tail.group(1))
    plain = re.match(r"^nas\s+notas(?:\s+(.*))?$", norm)
    if plain:
        return _clean_subject(plain.group(1) or "")
    held = re.match(
        r"^tem\s+(?:alguma\s+)?nota(?:\s+(?:sobre|de|do|da))?(?:\s+(.*))?$",
        norm,
    )
    if held:
        return _clean_subject(held.group(1) or "")
    thing = re.match(
        r"^tem\s+(?:alguma\s+coisa|algo)"
        r"(?:\s+(?:sobre|de|do|da))?"
        r"(?:\s+(.+?))?"
        r"\s+nas\s+(?:minhas\s+)?notas$",
        norm,
    )
    if thing:
        return _clean_subject(thing.group(1) or "")
    named = re.match(
        r"^(?:alguma|uma)\s+nota(?:\s+(?:sobre|de|do|da))?(?:\s+(.*))?$",
        norm,
    )
    if named:
        return _clean_subject(named.group(1) or "")
    mine = re.match(r"^nas minhas notas(?:\s+tem)?(?:\s+(.*))?$", norm)
    if mine:
        return _clean_subject(mine.group(1) or "")
    asked = re.match(r"^o que (?:eu )?anotei\s+(?:sobre|de|do|da)\s+(.+)$", norm)
    if asked:
        return _clean_subject(asked.group(1))
    return None


def note_query_of(heard: str, reply: str) -> str:
    """Assunto que o céu destaca. Vazio quando a fala não buscou nas notas."""
    if reply != "Não há nota com isso, Senhor." and not (reply or "").startswith("Nas notas, Senhor."):
        return ""
    subject = _note_subject(_plain(heard))
    if subject is not None:
        return subject
    return _plain(heard)


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


def _bare_sky_place(norm: str) -> str:
    """Cidade depois de tempo, clima ou previsão, sem a preposição."""
    match = re.match(
        r"^(?:tempo|clima|previsao)\s+(?!em\s|no\s|na\s|de\s|do\s|da\s|para\s)(.+)$",
        norm,
    )
    if not match:
        return ""
    place = match.group(1).strip(" .?")
    if not place or place in {"agora", "hoje", "amanha", "aqui", "o tempo"}:
        return ""
    if re.search(r"\b(?:para|que|com|quando|porque|fazer|faz)\b", place):
        return ""
    if len(place.split()) > 4:
        return ""
    return place


_VAGUE_PLACE = {"cidade", "lugar", "ai", "la", "aqui", "hoje", "agora", "amanha", "mim"}


def _city_name(place: str) -> str:
    """Tira hoje, agora e um lugar vago. «curitiba hoje» fica «curitiba»."""
    place = (place or "").strip(" .")
    place = re.sub(r"^(?:hoje|agora|la|muito)\s+", "", place)
    place = re.sub(r"\s+(?:hoje|agora|amanha)$", "", place).strip()
    if not place or place in _VAGUE_PLACE:
        return ""
    return place


def _heat_place(norm: str) -> str | None:
    """Cidade numa frase de calor ou frio. None se não for essa frase."""
    match = re.match(
        r"^(?:faz calor"
        r"|(?:esta|ta)(?:\s+fazendo)?(?:\s+muito)?\s+(?:calor|quente|frio)"
        r"|vai fazer(?:\s+muito)?\s+(?:calor|frio|quente))"
        r"(?:\s+(?:hoje|agora|la|muito))?"
        r"(?:\s+(?:em|no|na)\s+(.+))?$",
        norm,
    )
    if match:
        return _city_name(match.group(1) or "")
    bare = re.match(r"^(?:calor|frio)\s+(?:em|no|na)\s+(.+)$", norm)
    if bare:
        return _city_name(bare.group(1))
    return None


def _rain_place(norm: str) -> str | None:
    """Cidade numa frase de chuva. None se não for essa frase."""
    match = re.match(
        r"^(?:vai chover|(?:esta|ta)\s+chovendo|chove)"
        r"(?:\s+(?:hoje|agora|la|muito))?"
        r"(?:\s+(?:em|no|na)\s+(.+))?$",
        norm,
    )
    if not match:
        return None
    return _city_name(match.group(1) or "")


def _place_of(norm: str) -> str:
    hot = _heat_place(norm)
    if hot is not None:
        return hot
    wet = _rain_place(norm)
    if wet is not None:
        return wet
    for prefix in (
        "tempo em ", "clima em ", "previsao em ", "previsao para ",
        "clima de ", "tempo de ", "clima do ", "tempo do ", "clima da ", "tempo da ",
        "clima no ", "tempo no ", "clima na ", "tempo na ",
    ):
        if norm.startswith(prefix):
            return norm[len(prefix) :].strip(" .")
    match = re.search(
        r"\b(?:tempo|clima|previsao)\s+(?:la\s+)?(?:em|no|na|de)\s+(.+)$",
        norm,
    )
    if match:
        place = _city_name(match.group(1))
        if place and place not in {"tempo"}:
            return place
    heat = re.search(r"\btemperatura\s+(?:em|no|na|de|do|da)\s+(.+)$", norm)
    if heat:
        return _city_name(heat.group(1))
    if "previsao" in norm:
        later = re.search(r"\bpara\s+(.+)$", norm)
        if later:
            place = later.group(1).strip(" .")
            if place and place not in {"hoje", "agora", "amanha", "aqui", "mim"}:
                return place
    forecast = re.search(r"\bprevisao\s+para\s+(.+)$", norm)
    if forecast:
        return forecast.group(1).strip(" .")
    return _bare_sky_place(norm)


def _usable_topic(topic: str) -> str:
    topic = topic.strip(" .")
    if topic in {"sobre", "de", "do", "da"}:
        return ""
    return topic


def _topic_of(norm: str) -> str:
    norm = norm.replace("novidades", "noticias").replace("novidade", "noticia")
    for prefix in (
        "noticias sobre ", "noticia sobre ",
        "noticias de ", "noticia de ",
        "noticias do ", "noticia do ",
        "noticias da ", "noticia da ",
        "o que esta acontecendo em ",
        "o que esta acontecendo no ",
        "o que esta acontecendo na ",
        "o que esta acontecendo sobre ",
    ):
        if norm.startswith(prefix):
            return _usable_topic(norm[len(prefix) :])
    match = re.search(r"noticias?\s+(?:sobre|de|do|da)\s+(.+)$", norm)
    if match:
        return _usable_topic(match.group(1))
    bare = re.match(r"^noticias?\s+(?!sobre\s|de\s|do\s|da\s)(.+)$", norm)
    if bare:
        return _usable_topic(bare.group(1))
    happening = re.match(r"^o que esta acontecendo\s+(.+)$", norm)
    if happening:
        return _usable_topic(happening.group(1))
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
    if _heat_place(norm) is not None or _rain_place(norm) is not None:
        return True
    if _place_of(norm):
        return True
    if norm.startswith(("tempo em ", "clima em ", "clima ", "previsao ")):
        return True
    if "qual a temperatura" in norm or "qual e a temperatura" in norm or norm.startswith("temperatura"):
        return True
    if norm.startswith("tempo ") and _bare_sky_place(norm):
        return True
    if re.search(r"\b(?:tempo|clima|previsao)\s+em\s+\S", norm):
        return True
    if norm in {
        "clima", "tempo", "previsao", "o tempo", "o clima", "tempo agora",
        "qual o tempo", "qual e o tempo",
    }:
        return True
    if "que tempo" in norm or "previsao" in norm or "qual o tempo" in norm:
        return True
    if "qual o clima" in norm or "qual e o clima" in norm or "como ta o clima" in norm:
        return True
    return (
        "como esta o tempo" in norm
        or "como esta o clima" in norm
        or "como ta o tempo" in norm
    )


_SEARCH_COMMAND = re.compile(
    r"^(?:(?:por favor|pode|posso|quero|queria|vamos|da)\s+(?:que\s+|uma\s+)?)*"
    r"(?:me\s+)?"
    r"(?:pesquisada|pesquisar|pesquise|pesquisa|buscar|busque|busca|procurar|procure|procura|google)"
    r"(?:\s+(.*))?$"
)
_QUERY_FILLERS = (
    "sobre ", "pelo ", "pela ", "para ", "pra mim ", "pra ", "por ",
    "o ", "a ", "os ", "as ", "um ", "uma ",
    "de ", "do ", "da ", "no google ", "no ", "na ", "me ", "mim ", "ai ",
)


def _search_query(rest: str) -> str:
    """Tira o convite da busca. «sobre o café» e «café no google» viram «café»."""
    query = (rest or "").strip(" ?.")
    while query:
        for prefix in _QUERY_FILLERS:
            if query.startswith(prefix):
                query = query[len(prefix) :].strip()
                break
        else:
            break
    if query.endswith(" no google"):
        query = query[: -len(" no google")].strip()
    return query


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
        if "whatsapp" in norm or re.search(r"\bzap\b", norm):
            return _whatsapp(text)
        if norm in {"resumo do dia", "briefing", "como esta o dia", "como vai o dia"}:
            clock_h = moment.hour
            sky = _weather("São Paulo", fetch)
            return f"São {clock_h} horas, Senhor. {sky}"
        if norm in {
            "anote", "anota", "lembrete", "lembra", "lembra de",
            "me lembre", "me lembra", "me lembre de", "me lembra de",
            "esquece de", "nao esquece de", "nao me deixa esquecer de",
        }:
            return "O que devo anotar, Senhor?"
        body = _remember_body(text)
        if body:
            return _remember(body, reminders_path, moment)
        if norm in {
            "quais lembretes", "meus lembretes", "o que anotei", "o que eu anotei",
            "quais sao os lembretes", "quais os lembretes",
            "lista os lembretes", "listar lembretes", "liste os lembretes",
        }:
            return _list_notes(reminders_path)
        if _wants_weather(norm):
            place = _place_of(norm)
            if not place:
                return "De qual lugar, Senhor."
            return _weather(place, fetch)
        if (
            "noticia" in norm
            or "novidade" in norm
            or norm == "o que esta acontecendo"
            or norm.startswith("o que esta acontecendo ")
        ):
            topic = _topic_of(norm)
            if not topic:
                return "Sobre o que, Senhor."
            return _news(topic, fetch)
        subject = _note_subject(norm)
        if subject is not None:
            if not subject:
                return "O que devo buscar nas notas, Senhor?"
            return _find_notes(subject, reminders_path)
        found = _SEARCH_COMMAND.match(norm)
        if found:
            return _search(_search_query(found.group(1) or ""), fetch)
    except (OSError, ValueError, json.JSONDecodeError, ET.ParseError, KeyError, TimeoutError):
        return "Não alcancei isso agora, Senhor."
    return None
