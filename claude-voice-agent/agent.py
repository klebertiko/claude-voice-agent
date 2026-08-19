"""claude-voice-agent — agente de voz LiveKit (console-first, local).

Pipeline: mic -> silero VAD -> Whisper (STT) -> [wake-gate] -> Claude (LLM) ->
kokoro (TTS) -> alto-falante. Rode local, sem servidor:

    uv run python -m claude_agent_voice.agent console

O cérebro (Claude) é OPCIONAL: sem ``ANTHROPIC_API_KEY`` o agente ainda te ouve
e fala (greeting + eco de teste), o que prova voz+ouvido. Com a chave, ele pensa.
"""

from __future__ import annotations

import logging
import shutil
import sys
import time
from collections.abc import Callable

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
    """Instancia o TTS da persona ativa (Piper p/ Gambit, kokoro p/ Lilith)."""
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
        speed=settings.speed,
    )


def greeting(persona: Persona) -> str:
    """Saudação falada da persona ativa."""
    return f"{persona.name} aqui. É só me chamar pelo nome quando precisar."


class ClaudeAgentVoice(Agent):
    """O agente. O wake-gate decide, a cada turno, se ele deve responder.

    A classe é persona-agnóstica: a persona ativa vem de ``settings.persona`` —
    prompt, wake-words e saudação saem da persona (Lilith, Gambit, ...), não são
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
    """Monta a AgentSession. Cérebro = Claude via subscription (CLI `claude -p`)."""
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
    if shutil.which(settings.claude_cli):
        from .llm_claude_cli import ClaudeCliLLM

        kwargs["llm"] = ClaudeCliLLM(
            fallback_system=persona.system_prompt(),
            model=settings.llm_model,
            cli=settings.claude_cli,
            label=persona.name,
        )
        logger.info(
            "cérebro Claude via subscription (%s -p) — persona %s",
            settings.claude_cli,
            persona.name,
        )
    else:
        logger.warning(
            "CLI '%s' ausente: o agente ouve e fala, mas não pensa", settings.claude_cli
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
