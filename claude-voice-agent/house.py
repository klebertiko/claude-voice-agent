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


def _weather(place: str, fetch, *, day: str = "", field: str = "") -> str:
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
    if field == "umidade":
        url = (
            "https://api.open-meteo.com/v1/forecast?current=relative_humidity_2m"
            f"&latitude={lat}&longitude={lon}&timezone=America%2FSao_Paulo"
        )
        data = json.loads(fetch(url))
        humid = (data.get("current") or {}).get("relative_humidity_2m")
        if humid is None:
            return "Não alcancei o clima, Senhor."
        pct = int(round(float(humid)))
        return f"Em {label}, umidade de {pct} por cento, Senhor."
    if field == "sensacao":
        url = (
            "https://api.open-meteo.com/v1/forecast?current=apparent_temperature"
            f"&latitude={lat}&longitude={lon}&timezone=America%2FSao_Paulo"
        )
        data = json.loads(fetch(url))
        feels = (data.get("current") or {}).get("apparent_temperature")
        if feels is None:
            return "Não alcancei o clima, Senhor."
        graus = int(round(float(feels)))
        return f"Em {label}, sensação de {graus} graus, Senhor."
    if day == "amanha":
        url = (
            "https://api.open-meteo.com/v1/forecast?daily=temperature_2m_max,weather_code"
            f"&forecast_days=2&latitude={lat}&longitude={lon}&timezone=America%2FSao_Paulo"
        )
        data = json.loads(fetch(url))
        daily = data.get("daily") or {}
        highs = daily.get("temperature_2m_max") or []
        codes = daily.get("weather_code") or []
        if len(highs) < 2:
            return "Não alcancei o clima, Senhor."
        sky = _WX.get(int(codes[1] if len(codes) > 1 else 0), "instável")
        graus = int(round(float(highs[1])))
        return f"Amanhã em {label}, máxima de {graus} graus, {sky}, Senhor."
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
        if plain in {
            "ai", "isso", "que", "por favor", "por gentileza", "para mim", "pra mim", "o seguinte",
            "nas notas", "na nota", "uma nota", "amanha", "para amanha", "pra amanha",
        }:
            return ""
        for filler in (
            "ai ", "isso ", "que ", "por favor ", "por gentileza ",
            "para mim ", "pra mim ", "o seguinte ", "para amanha ", "pra amanha ",
            "amanha de ", "amanha ",
            "nas notas ", "na nota ", "uma nota ",
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
    "guarda isso nas notas ",
    "guarda isso na nota ",
    "adiciona nas notas ",
    "adiciona na nota ",
    "registra nas notas ",
    "registra na nota ",
    "escreve nas notas ",
    "escreve na nota ",
    "bota nas notas ",
    "bota na nota ",
    "poe nas notas ",
    "poe na nota ",
    "cria uma nota ",
    "cria um lembrete ",
    "novo lembrete ",
    "guarda nas notas ",
    "guarda na nota ",
    "salva nas notas ",
    "salva na nota ",
    "salva uma nota ",
    "salva a nota ",
    "coloca nas notas ",
    "coloca na nota ",
    "nao me deixa esquecer de ",
    "nao me deixa esquecer ",
    "nao esquece de ",
    "nao esquece ",
    "esquece de ",
    "esquece ",
    "me lembre de ",
    "me lembra de ",
    "me lembre ",
    "me lembra ",
    "lembrete ",
    "lembra de ",
    "lembra ",
    "quero anotar ",
    "queria anotar ",
    "preciso anotar ",
    "pode anotar ",
    "por favor anotar ",
    "favor anotar ",
    "anote ",
    "anota ",
)


def _remember_body(text: str) -> str:
    """O que anotar, sem o verbo. Os acentos do resto ficam."""
    norm = _plain(text)
    words = (text or "").strip().split()
    for prefix in _REMEMBER_PREFIXES:
        if norm.startswith(prefix):
            if prefix == "lembrete " and re.match(r"^(?:do|da|sobre)\b", norm[len(prefix) :]):
                return ""
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
        "alguma nota", "uma nota", "tem recado", "cade a nota", "cade o lembrete",
        "onde anotei", "onde eu anotei",
        "onde esta a nota", "onde esta o lembrete", "onde esta o recado",
        "onde ficou a nota", "onde ficou o lembrete", "onde ficou o recado",
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
    placed = re.match(
        r"^onde(?:\s+eu)?\s+anotei(?:\s+(?:o|a|os|as|sobre|de|do|da))?\s+(.+)$",
        norm,
    )
    if placed:
        return _clean_subject(placed.group(1))
    where = re.match(
        r"^onde(?:\s+eu)?\s+(?:esta|ficou|deixei)(?:\s+(?:a|o))?\s+(?:nota|lembrete|recado)"
        r"(?:\s+(?:do|da|de|sobre))?(?:\s+(.*))?$",
        norm,
    )
    if where:
        return _clean_subject(where.group(1) or "")
    lost = re.match(
        r"^cade(?:\s+(?:a|o))?\s+(?:nota|lembrete|recado)"
        r"(?:\s+(?:do|da|de|sobre))?(?:\s+(.*))?$",
        norm,
    )
    if lost:
        return _clean_subject(lost.group(1) or "")
    recado = re.match(
        r"^tem\s+recado(?:\s+(?:sobre|de|do|da))?(?:\s+(.*))?$",
        norm,
    )
    if recado:
        return _clean_subject(recado.group(1) or "")
    owned_note = re.match(
        r"^(?:o\s+)?lembrete(?:\s+(?:do|da|sobre))(?:\s+(.*))?$",
        norm,
    )
    if owned_note:
        return _clean_subject(owned_note.group(1) or "")
    bare_owned = re.match(
        r"^(?:(?:o|a)\s+)?(?:nota|recado)\s+(?:do|da|de|sobre)\s+(.+)$",
        norm,
    )
    if bare_owned:
        return _clean_subject(bare_owned.group(1))
    shown = re.match(
        r"^(?:me\s+)?(?:mostra|mostre|mostrar|ve|ver|le|leia|ler|qual)\s+"
        r"(?:(?:a|o)\s+)?(?:nota|lembrete|recado)"
        r"(?:\s+(?:do|da|de|sobre))?(?:\s+(.*))?$",
        norm,
    )
    if shown:
        return _clean_subject(shown.group(1) or "")
    lookup = re.match(
        r"^(?:buscar|busque|busca|procurar|procure|procura|pesquisar|pesquise|pesquisa)"
        r"\s+(?:(?:o|a|os|as|um|uma)\s+)?"
        r"(?:lembrete|nota|recado)s?"
        r"(?:\s+(?:do|da|de|sobre))?"
        r"(?:\s+(.*))?$",
        norm,
    )
    if lookup:
        return _clean_subject(lookup.group(1) or "")
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


def _last_note(path: Path) -> str:
    """A nota mais nova, a última que foi gravada. Não apaga nada."""
    spoken = []
    for item in _load(path):
        if not isinstance(item, dict):
            continue
        text = " ".join(str(item.get("text") or "").split())
        if text:
            spoken.append(text)
    if not spoken:
        return "Nada anotado, Senhor."
    return "A última nota, Senhor. " + spoken[-1] + "."


_LATEST_NOTE = re.compile(
    r"^(?:(?:me\s+)?(?:mostra|mostre|mostrar|le|leia|ler|qual(?:\s+(?:e|foi))?|cade)\s+)?"
    r"(?:(?:a|o)\s+)?"
    r"(?:(?:ultima|ultimo)\s+(?:nota|lembrete|recado)"
    r"|(?:nota|lembrete|recado)\s+mais\s+recente)$"
)


def _wants_latest_note(norm: str) -> bool:
    return _LATEST_NOTE.fullmatch(norm) is not None


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


_VAGUE_PLACE = {"cidade", "lugar", "ai", "la", "aqui", "hoje", "agora", "amanha", "depois", "mim"}


def _city_name(place: str) -> str:
    """Tira hoje, agora e um lugar vago. «curitiba hoje» fica «curitiba»."""
    place = (place or "").strip(" .")
    place = re.sub(
        r"^(?:hoje|agora|la|muito|amanha|depois)(?:\s+(?:em|no|na|de|do|da))?\s+",
        "",
        place,
    )
    place = re.sub(r"\s+(?:hoje|agora|amanha)$", "", place).strip()
    if not place or place in _VAGUE_PLACE:
        return ""
    return place


def _spoken_place(text: str) -> str:
    """A cidade da resposta curta, sem o dia, com o acento que a pessoa falou."""
    words = (text or "").strip(" .?").split()
    plain = [_plain(word) for word in words]
    while plain and plain[0] in {"hoje", "agora", "la", "muito", "amanha", "depois"}:
        plain.pop(0)
        words.pop(0)
        if plain and plain[0] in {"em", "no", "na", "de", "do", "da"}:
            plain.pop(0)
            words.pop(0)
    while plain and plain[-1] in {"hoje", "agora", "amanha"}:
        plain.pop()
        words.pop()
    place = " ".join(words).strip(" .?")
    if not place or _plain(place) in _VAGUE_PLACE:
        return ""
    return place


def _heat_place(norm: str) -> str | None:
    """Cidade numa frase de calor, frio, sol ou nuvem. None se não for essa frase."""
    match = re.match(
        r"^(?:(?:amanha|hoje|depois)\s+)?"
        r"(?:faz (?:calor|frio|sol)"
        r"|tem (?:sol|calor|frio)"
        r"|(?:esta|ta)(?:\s+fazendo)?(?:\s+muito)?\s+(?:calor|quente|frio|sol|nublado)"
        r"|vai (?:esfriar|esquentar|gear)"
        r"|vai fazer(?:\s+muito)?\s+(?:calor|frio|quente|sol))"
        r"(?:\s+(?:hoje|agora|la|muito|amanha|depois))?"
        r"(?:\s+(?:em|no|na)\s+(.+))?$",
        norm,
    )
    if match:
        return _city_name(match.group(1) or "")
    bare = re.match(r"^(?:calor|frio|sol|nublado)\s+(?:em|no|na)\s+(.+)$", norm)
    if bare:
        return _city_name(bare.group(1))
    return None


def _rain_place(norm: str) -> str | None:
    """Cidade numa frase de chuva, garoa ou trovoada. None se não for essa frase."""
    match = re.match(
        r"^(?:(?:amanha|hoje|depois)\s+)?"
        r"(?:vai chover|(?:esta|ta)\s+(?:chovendo|garoando)|chove|garoa"
        r"|vai dar(?:\s+uma)?\s+chuva|risco de chuva|pode chover)"
        r"(?:\s+(?:hoje|agora|la|muito|amanha|depois))?"
        r"(?:\s+(?:em|no|na)\s+(.+))?$",
        norm,
    )
    if match:
        return _city_name(match.group(1) or "")
    storm = re.match(
        r"^tem\s+(?:trovoada|chuva|garoa)(?:\s+(?:em|no|na)\s+(.+))?$",
        norm,
    )
    if storm:
        return _city_name(storm.group(1) or "")
    return None


def _graus_place(norm: str) -> str | None:
    """Cidade em «quantos graus faz em Recife». None se não for essa frase."""
    match = re.match(
        r"^quantos graus(?:\s+(?:faz|esta|ta|sao|tem))?(?:\s+fazendo)?"
        r"(?:\s+(?:agora|hoje|la|muito|amanha|depois))?"
        r"(?:\s+(?:em|no|na|de)\s+(.+))?$",
        norm,
    )
    if not match:
        return None
    return _city_name(match.group(1) or "")


def _quanto_place(norm: str) -> str | None:
    """Cidade em «tá quanto em Recife». None se não for essa frase."""
    match = re.match(
        r"^(?:(?:ta|esta)\s+quanto|quanto\s+(?:ta|esta|faz))"
        r"(?:\s+(?:agora|hoje|la|muito|amanha|depois))?"
        r"(?:\s+(?:em|no|na|de)\s+(.+))?$",
        norm,
    )
    if not match:
        return None
    return _city_name(match.group(1) or "")


def _later_place(norm: str) -> str | None:
    """Cidade em «tempo para amanhã em Curitiba». None se não for essa frase."""
    match = re.match(
        r"^(?:tempo|clima)\s+para\s+(?:amanha|hoje|depois)"
        r"(?:\s+(?:em|no|na|de)\s+(.+))?$",
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
    later = _later_place(norm)
    if later is not None:
        return later
    graus = _graus_place(norm)
    if graus is not None:
        return graus
    quanto = _quanto_place(norm)
    if quanto is not None:
        return quanto
    day_city = re.search(
        r"\b(?:tempo|clima|previsao)\s+(?:para\s+)?(?:amanha|hoje|depois)\s+(?:em|no|na|de)\s+(.+)$",
        norm,
    )
    if day_city:
        place = _city_name(day_city.group(1))
        if place and place not in {"tempo"}:
            return place
    for prefix in (
        "tempo em ", "clima em ", "previsao em ", "previsao para ",
        "clima de ", "tempo de ", "clima do ", "tempo do ", "clima da ", "tempo da ",
        "clima no ", "tempo no ", "clima na ", "tempo na ",
    ):
        if norm.startswith(prefix):
            rest = norm[len(prefix) :].strip(" .")
            if prefix == "previsao para ":
                return _city_name(rest)
            return rest
    match = re.search(
        r"\b(?:tempo|clima|previsao)\s+(?:la\s+)?(?:em|no|na|de)\s+(.+)$",
        norm,
    )
    if match:
        place = _city_name(match.group(1))
        if place and place not in {"tempo"}:
            return place
    heat = re.search(
        r"\btemperatura(?:\s+(?:agora|hoje|la|muito))?\s+(?:em|no|na|de|do|da)\s+(.+)$",
        norm,
    )
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
        return _city_name(forecast.group(1))
    if re.search(r"\b(?:tempo|clima|previsao|temperatura|graus)\b", norm):
        anchored = re.search(r"\b(?:em|no|na)\s+(.+)$", norm)
        if anchored:
            place = _city_name(anchored.group(1))
            if place and place not in {"tempo", "semana"}:
                return place
    return _bare_sky_place(norm)


def _usable_topic(topic: str) -> str:
    topic = topic.strip(" .")
    if topic in {"sobre", "de", "do", "da"}:
        return ""
    return topic


def _topic_of(norm: str) -> str:
    headlines = re.fullmatch(
        r"(?:(?:quais|me\s+(?:da|fala|diz|conta|passa))\s+(?:as|os)\s+)?"
        r"(?:as\s+)?manchetes?(?:\s+(?:sobre|de|do|da)\s+(.+))?",
        norm,
    )
    if headlines:
        return _usable_topic(headlines.group(1) or "") or "brasil"
    norm = norm.replace("novidades", "noticias").replace("novidade", "noticia")
    brief = re.fullmatch(
        r"(?:me\s+da\s+(?:(?:um|o)\s+)?)?resumo\s+(?:das|de|dos)\s+noticias"
        r"(?:\s+(?:sobre|de|do|da)\s+(.+))?",
        norm,
    )
    if brief:
        return _usable_topic(brief.group(1) or "") or "brasil"
    for prefix in (
        "noticias sobre ", "noticia sobre ",
        "noticias de ", "noticia de ",
        "noticias do ", "noticia do ",
        "noticias da ", "noticia da ",
        "o que esta acontecendo em ",
        "o que esta acontecendo no ",
        "o que esta acontecendo na ",
        "o que esta acontecendo sobre ",
        "o que aconteceu em ",
        "o que aconteceu no ",
        "o que aconteceu na ",
        "o que aconteceu sobre ",
    ):
        if norm.startswith(prefix):
            return _usable_topic(norm[len(prefix) :])
    match = re.search(r"noticias?\s+(?:sobre|de|do|da)\s+(.+)$", norm)
    if match:
        return _usable_topic(match.group(1))
    fresh = re.match(
        r"^(?:me\s+(?:conta|fala|diz)\s+)?o que (?:ha|houve) de novo"
        r"(?:\s+(?:sobre|de|do|da)\s+(.+?))?(?:\s+(?:hoje|agora))?$",
        norm,
    )
    if fresh:
        return _usable_topic(fresh.group(1) or "") or "brasil"
    rolling = re.match(
        r"^(?:me\s+(?:conta|fala|diz)\s+)?o que (?:esta|ta) rolando"
        r"(?:\s+(?:sobre|de|do|da|em|no|na)\s+(.+?))?(?:\s+(?:hoje|agora))?$",
        norm,
    )
    if rolling:
        return _usable_topic(rolling.group(1) or "") or "brasil"
    if re.fullmatch(
        r"(?:(?:quais|me da|me fala|me conta)\s+(?:as|os)\s+)?(?:as\s+)?ultimas\s+noticias",
        norm,
    ):
        return "brasil"
    if re.fullmatch(
        r"(?:me\s+)?(?:da|conta|fala|diz|passa)\s+(?:as\s+|os\s+|uma\s+)?(?:ultimas\s+)?noticias",
        norm,
    ):
        return "brasil"
    fresh_bit = re.match(
        r"^(?:(?:tem(?:\s+alguma)?|alguma)\s+noticias?(?:\s+novas?)?|noticias?\s+novas?)"
        r"(?:\s+(?:sobre|de|do|da)\s+(.+))?$",
        norm,
    )
    if fresh_bit:
        return _usable_topic(fresh_bit.group(1) or "") or "brasil"
    bare = re.match(r"^noticias?\s+(?!sobre\s|de\s|do\s|da\s)(.+)$", norm)
    if bare:
        topic = _usable_topic(bare.group(1))
        if topic in {"ultimas", "nova", "novas"}:
            return "brasil"
        return topic
    happening = re.match(r"^o que (?:esta acontecendo|aconteceu)\s+(.+)$", norm)
    if happening:
        rest = happening.group(1).strip()
        if rest in {"de novo", "novo"}:
            return "brasil"
        return _usable_topic(rest)
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
    day: str = "",
    field: str = "",
) -> str:
    """A resposta curta depois de Orion pedir lugar, assunto, busca ou nota.

    ``day="amanha"`` vale quando a pergunta do lugar veio de uma frase de amanhã.
    """
    fetch = fetch or _http_get
    said = _answer_text(text)
    try:
        if kind == "weather":
            place = _spoken_place(said)
            if not place:
                return "De qual lugar, Senhor."
            return _weather(place, fetch, day=day, field=field)
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


def _humidity_place(norm: str) -> str | None:
    """None quando não é umidade. Vazio quando falta a cidade."""
    match = re.fullmatch(
        r"(?:qual\s+(?:e\s+)?)?(?:a\s+)?umidade(?:\s+do\s+ar)?"
        r"(?:\s+(?:agora|hoje))?(?:\s+(?:em|no|na|de)\s+(.+))?",
        norm,
    )
    if match:
        return _city_name(match.group(1) or "")
    damp = re.fullmatch(
        r"(?:(?:esta|ta)\s+)?(?:muito\s+)?umido"
        r"(?:\s+(?:agora|hoje))?(?:\s+(?:em|no|na|de)\s+(.+))?",
        norm,
    )
    if damp:
        return _city_name(damp.group(1) or "")
    return None


def _feels_place(norm: str) -> str | None:
    """None quando não é sensação térmica. Vazio quando falta a cidade."""
    match = re.fullmatch(
        r"(?:qual\s+(?:e\s+)?)?(?:a\s+)?sensacao\s+termica"
        r"(?:\s+(?:agora|hoje))?(?:\s+(?:em|no|na|de)\s+(.+))?",
        norm,
    )
    if not match:
        return None
    return _city_name(match.group(1) or "")


def _wants_weather(norm: str) -> bool:
    if "faz tempo" in norm:
        return False
    if (
        _heat_place(norm) is not None
        or _rain_place(norm) is not None
        or _later_place(norm) is not None
        or _graus_place(norm) is not None
        or _quanto_place(norm) is not None
    ):
        return True
    if "como vai o tempo" in norm or "como vai o clima" in norm:
        return True
    if norm in {"me fala o tempo", "me fala o clima", "me diz o tempo", "me diz o clima"}:
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
    changed = True
    while changed and query:
        changed = False
        for tail in (" no google", " no youtube"):
            if query.endswith(tail):
                query = query[: -len(tail)].strip()
                changed = True
        if query.startswith("youtube "):
            query = query[len("youtube ") :].strip()
            changed = True
        elif query == "youtube":
            query = ""
    return query


def _wants_message(norm: str) -> bool:
    """Mensagem com verbo de enviar. O número, se faltar, é pedido depois."""
    if not re.search(r"\bmensagem\b", norm):
        return False
    return bool(
        re.search(
            r"\b(?:manda|mande|mandar|envia|envie|enviar|escreve|escreva|escrever)\b",
            norm,
        )
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


_ZAP_LEAD = {
    "mande", "manda", "mandar", "envie", "envia", "enviar",
    "escreve", "escreva", "escrever", "fala", "fale", "falar",
    "diz", "diga", "dizer", "por", "favor", "me", "um", "uma",
}
_ZAP_TRAIL = {"para", "pro", "pra", "no", "na", "de", "do", "da", "o", "a"}
_ZAP_DROP = {"whatsapp", "zap", "mensagem"}
_ZAP_PHRASES = (
    ("no", "whatsapp"), ("na", "whatsapp"), ("pelo", "whatsapp"), ("pela", "whatsapp"),
    ("no", "zap"), ("na", "zap"), ("pelo", "zap"), ("pela", "zap"),
    ("a", "mensagem"), ("o", "mensagem"), ("uma", "mensagem"), ("um", "mensagem"),
)


def _drop_phrase(pairs: list[tuple[str, str]], phrase: tuple[str, ...]) -> list[tuple[str, str]]:
    size = len(phrase)
    kept = []
    index = 0
    while index < len(pairs):
        if [word for word, _ in pairs[index : index + size]] == list(phrase):
            index += size
            continue
        kept.append(pairs[index])
        index += 1
    return kept


def _whatsapp_message(text: str) -> str:
    """O texto do Zap. «dizendo cheguei» e «um oi no zap» ficam a mensagem."""
    said = re.search(r"dizendo\s+(.+)$", text or "", flags=re.IGNORECASE)
    if said:
        return said.group(1).strip(" .")
    orig = (text or "").strip().split()
    plain_words = _plain(text).split()
    if not orig or len(orig) != len(plain_words):
        return ""
    plain = " ".join(plain_words)
    match = re.search(r"\d(?:[\d\s().-]{8,20})\d", plain)
    if not match:
        return ""
    occupied = set()
    cursor = 0
    for index, word in enumerate(plain_words):
        word_end = cursor + len(word)
        if word_end > match.start() and cursor < match.end():
            occupied.add(index)
        cursor = word_end + 1
    def side(indexes: list[int]) -> list[str]:
        pairs = [(plain_words[i], orig[i]) for i in indexes]
        for phrase in _ZAP_PHRASES:
            pairs = _drop_phrase(pairs, phrase)
        pairs = [(word, raw) for word, raw in pairs if word not in _ZAP_DROP]
        while pairs and pairs[0][0] in _ZAP_LEAD:
            pairs.pop(0)
        while pairs and pairs[-1][0] in _ZAP_TRAIL:
            pairs.pop()
        return [raw for _, raw in pairs]

    before = side([i for i in range(len(orig)) if i not in occupied and i < min(occupied)])
    after = side([i for i in range(len(orig)) if i not in occupied and i > max(occupied)])
    return " ".join(before + after).strip(" .")


def continue_whatsapp(stage: str, text: str, number: str) -> tuple[str, str]:
    """A frase seguinte depois de Orion pedir o número ou o texto."""
    if stage == "zap-number":
        found = whatsapp_number(text)
        if not found:
            return "Diga o número, Senhor.", ""
        said = _whatsapp_message(text)
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
    said = _whatsapp_message(text)
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
        if "whatsapp" in norm or re.search(r"\bzap\b", norm) or _wants_message(norm):
            return _whatsapp(text)
        if norm in {"resumo do dia", "briefing", "como esta o dia", "como vai o dia"}:
            clock_h = moment.hour
            sky = _weather("São Paulo", fetch)
            return f"São {clock_h} horas, Senhor. {sky}"
        if norm in {
            "anote", "anota", "lembrete", "lembra", "lembra de",
            "me lembre", "me lembra", "me lembre de", "me lembra de",
            "esquece de", "esquece", "nao esquece de", "nao esquece", "nao me deixa esquecer de",
            "guarda nas notas", "guarda na nota",
            "guarda isso nas notas", "guarda isso na nota",
            "adiciona nas notas", "adiciona na nota",
            "registra nas notas", "registra na nota",
            "escreve nas notas", "escreve na nota",
            "bota nas notas", "bota na nota",
            "poe nas notas", "poe na nota",
            "cria uma nota", "cria um lembrete", "novo lembrete",
            "quero anotar", "queria anotar", "preciso anotar",
            "pode anotar", "por favor anotar", "favor anotar",
            "nao me deixa esquecer",
            "salva nas notas", "salva na nota", "salva uma nota", "salva a nota",
            "coloca nas notas", "coloca na nota",
        }:
            return "O que devo anotar, Senhor?"
        if _wants_latest_note(norm):
            return _last_note(reminders_path)
        body = _remember_body(text)
        if body:
            return _remember(body, reminders_path, moment)
        if norm in {
            "quais lembretes", "meus lembretes", "o que anotei", "o que eu anotei",
            "o que tenho anotado", "o que eu tenho anotado",
            "quais sao os lembretes", "quais os lembretes",
            "lista os lembretes", "listar lembretes", "liste os lembretes",
            "mostra minhas notas", "mostra os lembretes", "mostra as notas",
            "le minhas notas", "leia minhas notas",
            "le os lembretes", "leia os lembretes", "ler os lembretes",
            "meus recados",
            "quais sao minhas notas", "quais sao as notas",
            "lista minhas notas", "lista as notas",
            "listar minhas notas", "listar as notas",
            "liste minhas notas", "liste as notas",
        } or re.fullmatch(
            r"(?:me\s+)?(?:mostra|mostre|mostrar|le|leia|ler)\s+"
            r"(?:as|os|minhas|meus)\s+(?:notas|lembretes|recados)",
            norm,
        ):
            return _list_notes(reminders_path)
        feels_place = _feels_place(norm)
        if feels_place is not None:
            if not feels_place:
                return "De qual lugar, Senhor."
            return _weather(feels_place, fetch, field="sensacao")
        humid_place = _humidity_place(norm)
        if humid_place is not None:
            if not humid_place:
                return "De qual lugar, Senhor."
            return _weather(humid_place, fetch, field="umidade")
        if _wants_weather(norm):
            place = _place_of(norm)
            if not place:
                return "De qual lugar, Senhor."
            day = "amanha" if re.search(r"\bamanha\b", norm) else ""
            return _weather(place, fetch, day=day)
        if (
            "noticia" in norm
            or "novidade" in norm
            or "manchete" in norm
            or norm in {"o que esta acontecendo", "o que aconteceu"}
            or norm.startswith(("o que esta acontecendo ", "o que aconteceu "))
            or re.match(
                r"^(?:me\s+(?:conta|fala|diz)\s+)?o que (?:ha|houve) de novo"
                r"(?:\s+(?:sobre|de|do|da)\s+\S.*)?(?:\s+(?:hoje|agora))?$",
                norm,
            )
            or re.match(
                r"^(?:me\s+(?:conta|fala|diz)\s+)?o que (?:esta|ta) rolando"
                r"(?:\s+(?:sobre|de|do|da|em|no|na)\s+\S.*)?(?:\s+(?:hoje|agora))?$",
                norm,
            )
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
        about = re.match(
            r"^(?:me\s+)?(?:fala|fale|falar|conta|conte|explica|explique)"
            r"\s+sobre(?:\s+(.*))?$",
            norm,
        )
        defined = re.match(
            r"^(?:o que|oq)\s+(?:e|eh|sao|significa)(?:\s+(.*))?$",
            norm,
        )
        told = re.match(
            r"^(?:me\s+)?(?:explica|explique|explicar)"
            r"\s+(?:o|a|os|as|um|uma|do|da|de)\s+(.*)$",
            norm,
        )
        of = re.match(
            r"^(?:me\s+)?(?:fala|fale|falar|conta|conte)\s+(?:do|da|de)\s+(.*)$",
            norm,
        )
        want = re.match(
            r"^(?:eu\s+)?(?:quero|queria)\s+saber"
            r"(?:\s+(?:sobre|do|da|de))?(?:\s+(.*))?$",
            norm,
        )
        who = re.match(r"^quem\s+(?:e|eh|foi|era|sao)(?:\s+(.*))?$", norm)
        gloss = re.match(
            r"^(?:define|defina|definicao)(?:\s+(?:de|do|da))?(?:\s+(.*))?$",
            norm,
        )
        if about or defined or told or of or want or who or gloss:
            asked = ""
            for match in (about, defined, told, of, want, who, gloss):
                if match:
                    asked = match.group(1) or ""
                    break
            query = _search_query(asked)
            if query not in {"voce", "senhor", "sr"}:
                return _search(query, fetch)
        found = _SEARCH_COMMAND.match(norm)
        if found:
            return _search(_search_query(found.group(1) or ""), fetch)
    except (OSError, ValueError, json.JSONDecodeError, ET.ParseError, KeyError, TimeoutError):
        return "Não alcancei isso agora, Senhor."
    return None
