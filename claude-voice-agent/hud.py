"""Painel de voz: decide o turno e fala em pt-BR.

A página só mostra o anel e o texto. O microfone, quando existe, é áudio.
Sem o CLI ``claude``, a resposta é local (hora, data, ou um aviso curto)
para a voz ainda poder ser ouvida.
"""

from __future__ import annotations

import json
import os
import subprocess
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo

from .actions import local_command
from .brains import subscription_reply
from .house import continue_house, continue_whatsapp, house_reply, whatsapp_number
from .llm_ollama import ask_ollama, probe_ollama
from .noise import is_noise_transcript
from .personas import Persona, spoken_voice
from .speech import strip_for_speech
from .wake import WakeGate

_WEEKDAYS = (
    "segunda-feira",
    "terça-feira",
    "quarta-feira",
    "quinta-feira",
    "sexta-feira",
    "sábado",
    "domingo",
)
_MONTHS = (
    "janeiro",
    "fevereiro",
    "março",
    "abril",
    "maio",
    "junho",
    "julho",
    "agosto",
    "setembro",
    "outubro",
    "novembro",
    "dezembro",
)


def brazil_now() -> datetime:
    """Relógio falado no fuso de Brasília."""
    return datetime.now(ZoneInfo("America/Sao_Paulo"))


def _plain(text: str) -> str:
    folded = unicodedata.normalize("NFKD", (text or "").lower())
    stripped = "".join(ch for ch in folded if not unicodedata.combining(ch))
    return " ".join(stripped.split())


def spoken_fallback(cleaned: str, name: str, moment: datetime) -> str:
    """Resposta curta quando o cérebro não está disponível. Pura."""
    norm = _plain(cleaned)
    if not norm:
        return "Pois não, Senhor."
    if "seu nome" in norm or "se chama" in norm or "quem e voce" in norm or "o que e voce" in norm:
        return f"O nome é {name}, Senhor."
    if {"hora", "horas"} & set(norm.split()):
        return _speak_clock(moment)
    if (
        "que dia" in norm
        or "qual a data" in norm
        or "qual e a data" in norm
        or "qual e o dia" in norm
        or norm in {"data", "que data", "data de hoje", "a data"}
        or norm.startswith(("me diz a data", "me fala a data"))
    ):
        return _speak_date(moment)
    return (
        "Entendido, Senhor. Ainda não consigo fazer isso "
        "sem o cérebro ligado."
    )


def _speak_clock(moment: datetime) -> str:
    hour = moment.hour
    minute = moment.minute
    horas = "hora" if hour == 1 else "horas"
    if minute == 0:
        return f"São {hour} {horas}, Senhor."
    minutos = "minuto" if minute == 1 else "minutos"
    return f"São {hour} {horas} e {minute} {minutos}, Senhor."


def _speak_date(moment: datetime) -> str:
    weekday = _WEEKDAYS[moment.weekday()]
    month = _MONTHS[moment.month - 1]
    return f"Hoje é {weekday}, {moment.day} de {month}, Senhor."


@dataclass
class HudSession:
    persona: Persona
    require_wake: bool = True
    gate: WakeGate = field(default_factory=WakeGate)
    history: list[tuple[str, str]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.gate.wake_words != self.persona.wake_words:
            self.gate = WakeGate(
                wake_words=self.persona.wake_words,
                window_s=self.gate.window_s,
            )


@dataclass(frozen=True)
class TurnResult:
    status: str
    heard: str
    reply: str


def take_turn(
    session: HudSession,
    heard: str,
    now: float,
    reply_fn,
    *,
    enforce_wake: bool | None = None,
) -> TurnResult:
    """Aplica ruído e wake-gate. ``reply_fn(cleaned, history) -> str``.

    ``enforce_wake=False`` é a barra de texto: a pessoa já está na conversa
    e a pergunta não pode morrer por falta do nome. O microfone deixa o
    argumento ausente e continua no portão.
    """
    heard = (heard or "").strip()
    if not heard:
        return TurnResult("empty", "", "")
    if is_noise_transcript(heard):
        return TurnResult("noise", heard, "")

    require = session.require_wake if enforce_wake is None else enforce_wake
    if require:
        should, cleaned = session.gate.process(heard, now)
        if not should:
            return TurnResult("ignored", heard, "")
    elif session.require_wake:
        cleaned = session.gate.admit(heard, now)
    else:
        cleaned = heard

    reply = strip_for_speech(reply_fn(cleaned, list(session.history)))
    user_text = cleaned or "(o usuário chamou você pelo nome)"
    session.history.append(("user", user_text))
    session.history.append(("assistant", reply))
    if len(session.history) > 16:
        session.history = session.history[-16:]
    return TurnResult("replied", heard, reply)


_BRAIN_LABEL = {
    "codex": "Codex",
    "cursor": "Cursor",
    "claude": "Claude",
}


def _panel_fact(cleaned: str, persona: Persona) -> str | None:
    """Fatos do painel. Não chamam assinatura."""
    norm = _plain(cleaned)
    if norm in {"qual o ritmo", "o ritmo"}:
        rate = persona.speech_rate
        shown = f"{rate:g}"
        return f"O ritmo é {shown}, Senhor."
    if norm in {"qual a carga", "a carga"}:
        try:
            load = os.getloadavg()[0]
        except OSError:
            return "Não li a carga, Senhor."
        return f"A carga está em {load}, Senhor."
    if norm in {"qual o fuso", "o fuso"}:
        return "O fuso é Brasília, Senhor."
    if norm in {"qual a voz", "a voz"}:
        return f"A voz é {spoken_voice(persona.voice)}, Senhor."
    return None


def make_reply_fn(settings, persona: Persona, moment_fn=brazil_now, choice: dict | None = None):
    """Ordem local, depois as assinaturas, depois o Ollama, depois a reserva.

    Hora, data, nome e ``execute …`` não dependem de rede. Sem escolha, tenta
    Codex, Cursor e Claude, e só então o Ollama. Com escolha, só aquele.
    """
    host = settings.ollama_host
    preferred = settings.ollama_model
    chosen = choice if choice is not None else {"id": ""}
    pending = {"kind": "", "number": ""}
    asked = {
        "De qual lugar, Senhor.": "weather",
        "Sobre o que, Senhor.": "news",
        "O que devo procurar, Senhor?": "search",
        "O que devo anotar, Senhor?": "note",
        "O que devo buscar nas notas, Senhor?": "notes",
        "Diga o número, Senhor.": "zap-number",
        "O que devo escrever, Senhor?": "zap-text",
    }

    def reply(cleaned: str, history: list[tuple[str, str]]) -> str:
        cmd = local_command(cleaned)
        if cmd:
            pending["kind"] = ""
            pending["number"] = ""
            return f"ACAO: {cmd}"
        moment = moment_fn()
        housed = house_reply(cleaned, moment, reminders_path=settings.reminders_path)
        if housed:
            pending["kind"] = asked.get(housed, "")
            if housed == "O que devo escrever, Senhor?":
                found = whatsapp_number(cleaned)
                if found:
                    pending["number"] = found
            else:
                pending["number"] = ""
            return housed
        if pending["kind"]:
            fact = _panel_fact(cleaned, persona)
            local = spoken_fallback(cleaned, persona.name, moment)
            if fact or not local.startswith("Entendido, Senhor. Ainda não"):
                pending["kind"] = ""
                pending["number"] = ""
                return fact or local
            kind = pending["kind"]
            pending["kind"] = ""
            if kind in {"zap-number", "zap-text"}:
                spoken, number = continue_whatsapp(kind, cleaned, pending["number"])
                pending["number"] = number
                pending["kind"] = asked.get(spoken, "")
                return spoken
            pending["number"] = ""
            try:
                spoken = continue_house(
                    kind,
                    cleaned,
                    reminders_path=settings.reminders_path,
                    moment=moment,
                )
            except (OSError, ValueError, json.JSONDecodeError, TimeoutError):
                return "Não alcancei isso agora, Senhor."
            pending["kind"] = asked.get(spoken, "")
            return spoken
        fact = _panel_fact(cleaned, persona)
        if fact:
            return fact
        local = spoken_fallback(cleaned, persona.name, moment)
        if not local.startswith("Entendido, Senhor. Ainda não"):
            return local
        prefer = str(chosen.get("id") or "")
        if prefer in _BRAIN_LABEL:
            label = _BRAIN_LABEL[prefer]
            try:
                spoken = subscription_reply(
                    settings, persona, history, cleaned, prefer=prefer
                )
                if spoken:
                    return spoken
            except (OSError, subprocess.TimeoutExpired):
                spoken = None
            from .brains import probe_subscriptions

            rows = {row["id"]: row["up"] for row in probe_subscriptions(settings)}
            if not rows.get(prefer):
                return f"{label} não está neste computador, Senhor."
            return f"{label} não respondeu, Senhor."
        if prefer == "ollama":
            if host:
                try:
                    info = probe_ollama(host)
                    model = preferred or info.get("model")
                    if info.get("up") and model:
                        text = ask_ollama(host, model, persona.system_prompt(), history, cleaned)
                        if text:
                            return text
                except (OSError, TimeoutError, json.JSONDecodeError, ValueError):
                    pass
            return "O cérebro local não está neste computador, Senhor."
        try:
            spoken = subscription_reply(settings, persona, history, cleaned)
            if spoken:
                return spoken
        except (OSError, subprocess.TimeoutExpired):
            pass
        if host:
            try:
                info = probe_ollama(host)
                model = preferred or info.get("model")
                if info.get("up") and model:
                    text = ask_ollama(host, model, persona.system_prompt(), history, cleaned)
                    if text:
                        return text
            except (OSError, TimeoutError, json.JSONDecodeError, ValueError):
                pass
        return local

    return reply
