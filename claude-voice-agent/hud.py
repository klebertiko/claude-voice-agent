"""Painel de voz: decide o turno e fala em pt-BR, sem câmera.

A página só mostra o anel e o texto. O microfone, quando existe, é áudio.
Sem o CLI ``claude``, a resposta é local (hora, data, ou um aviso curto)
para a voz ainda poder ser ouvida.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo

from .llm_claude_cli import render_prompt
from .noise import is_noise_transcript
from .personas import Persona
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


def spoken_fallback(cleaned: str, name: str, moment: datetime) -> str:
    """Resposta curta quando o cérebro não está disponível. Pura."""
    norm = " ".join((cleaned or "").lower().split())
    if not norm:
        return f"Pois não, Senhor. {name} na escuta."
    if {"hora", "horas"} & set(norm.split()):
        return _speak_clock(moment)
    if "que dia" in norm or "qual a data" in norm or norm in {"data", "que data"}:
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


def ask_claude(
    cli: str,
    model: str | None,
    persona: Persona,
    cleaned: str,
    history: list[tuple[str, str]],
    *,
    timeout_s: float = 45.0,
) -> str:
    """Uma chamada bloqueante ao ``claude -p``. Levanta se o CLI falhar."""
    user = cleaned or "(o usuário chamou você pelo nome)"
    turns = [("system", persona.system_prompt()), *history, ("user", user)]
    prompt, system = render_prompt(turns, assistant_label=persona.name)
    args = [cli, "-p", prompt, "--output-format", "text"]
    if system:
        args += ["--append-system-prompt", system]
    if model:
        args += ["--model", model]
    proc = subprocess.run(
        args,
        capture_output=True,
        timeout=timeout_s,
        check=False,
    )
    text = proc.stdout.decode("utf-8", "replace").strip()
    if proc.returncode != 0 and not text:
        err = proc.stderr.decode("utf-8", "replace").strip() or "sem saída"
        raise RuntimeError(f"claude -p retornou {proc.returncode}: {err}")
    return text


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
) -> TurnResult:
    """Aplica ruído e wake-gate. ``reply_fn(cleaned, history) -> str``."""
    heard = (heard or "").strip()
    if not heard:
        return TurnResult("empty", "", "")
    if is_noise_transcript(heard):
        return TurnResult("noise", heard, "")

    if session.require_wake:
        should, cleaned = session.gate.process(heard, now)
        if not should:
            return TurnResult("ignored", heard, "")
    else:
        cleaned = heard

    reply = strip_for_speech(reply_fn(cleaned, list(session.history)))
    user_text = cleaned or "(o usuário chamou você pelo nome)"
    session.history.append(("user", user_text))
    session.history.append(("assistant", reply))
    if len(session.history) > 16:
        session.history = session.history[-16:]
    return TurnResult("replied", heard, reply)


def make_reply_fn(settings, persona: Persona, moment_fn=brazil_now):
    """Cérebro via CLI quando ``claude`` está no PATH; senão, fallback falado."""
    cli = settings.claude_cli
    model = settings.llm_model

    def reply(cleaned: str, history: list[tuple[str, str]]) -> str:
        if shutil.which(cli):
            try:
                text = ask_claude(cli, model, persona, cleaned, history)
                spoken = strip_for_speech(text)
                if spoken:
                    return spoken
            except (OSError, subprocess.TimeoutExpired, RuntimeError):
                pass
        return spoken_fallback(cleaned, persona.name, moment_fn())

    return reply
