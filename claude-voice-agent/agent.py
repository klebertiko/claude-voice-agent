"""claude-voice-agent — agente de voz LiveKit (console-first, local).

Pipeline: mic -> silero VAD -> Whisper (STT) -> [wake-gate] -> assinatura
(Codex, Cursor ou Claude) -> kokoro (TTS) -> alto-falante. Rode local:

    uv run python -m claude_agent_voice.agent console

O cérebro é o CLI já logado na assinatura. Sem esses binários o agente ainda
ouve e fala.
"""

from __future__ import annotations

import logging
import sys
import time
from collections.abc import Callable
from datetime import datetime
from zoneinfo import ZoneInfo

from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    StopResponse,
    WorkerOptions,
    cli,
)
from livekit.agents import stt as stt_mod
from livekit.plugins import silero

from .noise import is_noise_transcript
from .personas import Persona, get_persona
from .settings import Settings
from .stt_whisper import WhisperSTT
from .tts_kokoro import KokoroTTS
from .tts_piper import PiperTTS
from .wake import WakeGate

logger = logging.getLogger("claude_agent_voice")


def vad_kwargs(settings: Settings) -> dict:
    """Params do silero VAD a partir dos settings (menos sensível a ruído)."""
    return {
        "activation_threshold": settings.vad_threshold,
        "min_speech_duration": settings.vad_min_speech_s,
    }


def interruption_kwargs(settings: Settings) -> dict:
    """Opções de barge-in da AgentSession — ruído não corta a fala dela."""
    return {
        "min_interruption_words": settings.min_interrupt_words,
        "min_interruption_duration": settings.min_interrupt_s,
        "resume_false_interruption": settings.resume_false_interrupt,
    }


def make_tts(settings: Settings, persona: Persona):
    """Instancia o TTS da persona ativa (kokoro ou piper)."""
    if persona.tts_engine == "piper":
        return PiperTTS(
            model_path=settings.piper_model,
            config_path=settings.piper_config,
            voice=persona.voice,
            length_scale=settings.piper_length_scale,
        )
    return KokoroTTS(
        model_path=settings.kokoro_model,
        voices_path=settings.kokoro_voices,
        voice=persona.voice,
        lang=settings.lang,
        speed=settings.speed * persona.speech_rate,
    )


_TZ = ZoneInfo("America/Sao_Paulo")


def _greet_pool(address: str, hour: int) -> tuple[str, ...]:
    """Frases de mordomo. Nenhuma se apresenta nem ensina a wake-word."""
    # Só frases que esta voz consegue dizer por inteiro. Linha curta demais
    # ("Bom dia, Senhor.") o ataque some; frase esperta vira loop.
    if 5 <= hour < 12:
        return (
            f"Então, bom dia, {address}.",
            f"Pode dizer, {address}.",
            f"Diga, {address}.",
        )
    if 12 <= hour < 18:
        return (
            f"Boa tarde, {address}.",
            f"{address}. Boa tarde.",
            f"Pode dizer, {address}.",
        )
    if 18 <= hour < 23:
        return (
            f"Boa noite, {address}.",
            f"{address}. Boa noite.",
            f"Boa noite. Diga, {address}.",
        )
    return (
        f"Diga, {address}.",
        f"Pode dizer, {address}.",
        f"{address}. Boa noite.",
    )


def greeting(persona: Persona, when: datetime | None = None, salt: int = 0) -> str:
    """Saudação falada. Muda com a hora e com ``salt``, para não repetir a mesma linha."""
    moment = when or datetime.now(_TZ)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=_TZ)
    else:
        moment = moment.astimezone(_TZ)
    pool = _greet_pool(persona.form_of_address, moment.hour)
    return pool[salt % len(pool)]


class ClaudeAgentVoice(Agent):
    """O agente. O wake-gate decide, a cada turno, se ele deve responder.

    A classe é persona-agnóstica: a persona ativa vem de ``settings.persona`` —
    prompt, wake-words e saudação saem da persona (Lilith, Orion, ...), não são
    fixos na classe.
    """

    def __init__(
        self,
        settings: Settings,
        gate: WakeGate | None = None,
        clock: Callable[[], float] = time.monotonic,
        persona: Persona | None = None,
    ) -> None:
        self._persona = persona or get_persona(settings.persona)
        super().__init__(instructions=self._persona.system_prompt())
        self._settings = settings
        self._gate = gate or WakeGate(
            wake_words=self._persona.wake_words, window_s=settings.wake_window_s
        )
        self._clock = clock

    async def on_user_turn_completed(self, turn_ctx, new_message) -> None:
        text = new_message.text_content or ""
        logger.info("ouvi: %r", text)
        # Ruído/alucinação do whisper nunca vira turno (nem alimenta a janela).
        if is_noise_transcript(text):
            logger.info("ignorei (ruído/alucinação): %r", text)
            raise StopResponse()
        # Sem wake-word exigida: responde sempre.
        if not self._settings.require_wake:
            return
        should, cleaned = self._gate.process(text, self._clock())
        if not should:
            # Não fui chamada — engole o turno, sem resposta nem contexto.
            logger.info("ignorei (não ouvi a wake-word %r)", self._persona.name)
            raise StopResponse()
        # Entrega ao cérebro só o comando, sem o nome.
        logger.info("respondendo a: %r", cleaned)
        new_message.content = [cleaned or "(o usuário chamou você pelo nome)"]


def build_session(settings: Settings, vad) -> AgentSession:
    """Monta a AgentSession. Cérebro = Codex, Cursor ou Claude, pela assinatura."""
    persona = get_persona(settings.persona)
    whisper = WhisperSTT(
        model=settings.whisper_model,
        device=settings.whisper_device,
        compute_type=settings.whisper_compute,
        language=settings.whisper_lang,
    )
    kwargs = {
        "stt": stt_mod.StreamAdapter(stt=whisper, vad=vad),
        "vad": vad,
        "tts": make_tts(settings, persona),
    }
    from .brains import probe_subscriptions

    brains = [row["label"] for row in probe_subscriptions(settings) if row["up"]]
    if brains:
        from .llm_claude_cli import SubscriptionCliLLM

        kwargs["llm"] = SubscriptionCliLLM(settings=settings, persona=persona)
        logger.info("cérebro por assinatura (%s) — persona %s", ", ".join(brains), persona.name)
    else:
        logger.warning(
            "Codex, Cursor e Claude ausentes: o agente ouve e fala, mas não pensa"
        )
    kwargs.update(interruption_kwargs(settings))
    return AgentSession(**kwargs)


async def entrypoint(ctx: JobContext) -> None:
    settings = Settings.from_env()
    await ctx.connect()
    vad = ctx.proc.userdata.get("vad") if ctx.proc.userdata else None
    if vad is None:
        vad = silero.VAD.load(**vad_kwargs(settings))
    persona = get_persona(settings.persona)
    session = build_session(settings, vad)
    await session.start(agent=ClaudeAgentVoice(settings, persona=persona), room=ctx.room)
    await session.say(greeting(persona))


def prewarm(proc) -> None:
    proc.userdata["vad"] = silero.VAD.load(**vad_kwargs(Settings.from_env()))


def _force_utf8_stdio() -> None:
    """LiveKit imprime emoji; no Windows (cp1252) isso quebra. Força UTF-8."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (ValueError, OSError):
                pass


def _restore_terminal() -> None:
    """Reabilita o modo 'cozido' do console no Windows.

    O modo ``console`` do LiveKit põe o stdin em raw (echo/edição de linha
    desligados) e no Ctrl+C não restaura — o prompt do PowerShell fica 'maluco'
    (sem eco, sem edição). Repor ENABLE_PROCESSED/LINE/ECHO_INPUT conserta.
    """
    if sys.platform != "win32":
        return
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        std_input_handle = kernel32.GetStdHandle(-10)  # STD_INPUT_HANDLE
        cooked = 0x0001 | 0x0002 | 0x0004  # PROCESSED | LINE | ECHO
        kernel32.SetConsoleMode(std_input_handle, cooked)
    except Exception:
        pass


def main() -> None:
    """Entry point do console (`claude-agent-voice`) e do `python -m claude_agent_voice.agent`."""
    _force_utf8_stdio()
    try:
        cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
    finally:
        _restore_terminal()


if __name__ == "__main__":
    main()
