"""Integração do wake-gate no Agent: suprime turno não-endereçado, limpa o nome."""

import asyncio

import pytest
from livekit.agents import StopResponse, llm

from claude_agent_voice.agent import (
    ClaudeAgentVoice,
    greeting,
    interruption_kwargs,
    make_tts,
    vad_kwargs,
)
from claude_agent_voice.personas import get_persona
from claude_agent_voice.settings import Settings
from claude_agent_voice.tts_kokoro import KokoroTTS
from claude_agent_voice.tts_piper import PiperTTS
from claude_agent_voice.wake import WakeGate


def _msg(text: str):
    return llm.ChatMessage(role="user", content=[text])


def _make(require_wake: bool = True, now: float = 100.0) -> ClaudeAgentVoice:
    s = Settings.from_env(
        env={"CLAUDE_VOICE_REQUIRE_WAKE": "true" if require_wake else "false"}
    )
    return ClaudeAgentVoice(s, gate=WakeGate(window_s=30.0), clock=lambda: now)


def test_unaddressed_turn_is_suppressed():
    agent = _make()
    with pytest.raises(StopResponse):
        asyncio.run(agent.on_user_turn_completed(None, _msg("que horas são")))


def test_addressed_turn_strips_name():
    agent = _make()
    msg = _msg("Lilith que horas são")
    asyncio.run(agent.on_user_turn_completed(None, msg))
    assert msg.text_content == "que horas sao"


def test_bare_name_gets_placeholder():
    agent = _make()
    msg = _msg("Lilith?")
    asyncio.run(agent.on_user_turn_completed(None, msg))
    assert "chamou" in msg.text_content


def test_require_wake_false_always_passes_untouched():
    agent = _make(require_wake=False)
    msg = _msg("qualquer coisa")
    asyncio.run(agent.on_user_turn_completed(None, msg))
    assert msg.text_content == "qualquer coisa"


def test_noise_transcript_suppressed_even_without_wake():
    # ruído/alucinação do whisper não deve virar turno, mesmo sem wake-word exigida
    agent = _make(require_wake=False)
    with pytest.raises(StopResponse):
        asyncio.run(agent.on_user_turn_completed(None, _msg("o que é o que é o que é")))


def test_noise_transcript_suppressed_with_wake_active():
    agent = _make(require_wake=True)
    # abre a janela com o nome, depois manda ruído: deve ser engolido
    asyncio.run(agent.on_user_turn_completed(None, _msg("Lilith")))
    with pytest.raises(StopResponse):
        asyncio.run(agent.on_user_turn_completed(None, _msg("é é é é")))


def test_make_tts_gambit_is_piper():
    s = Settings.from_env(env={"PERSONA": "gambit"})
    t = make_tts(s, get_persona("gambit"))
    assert isinstance(t, PiperTTS)
    assert t.sample_rate == 22050


def test_make_tts_lilith_is_kokoro():
    s = Settings.from_env(env={"PERSONA": "lilith"})
    t = make_tts(s, get_persona("lilith"))
    assert isinstance(t, KokoroTTS)
    assert t.sample_rate == 24000


def test_greeting_uses_active_persona_name():
    assert greeting(get_persona("gambit")).startswith("Gambit aqui")
    assert greeting(get_persona("lilith")).startswith("Lilith aqui")


def test_agent_uses_persona_wake_words_by_default():
    # sem gate explícito, o agente monta o WakeGate com as wake-words da persona
    s = Settings.from_env(env={"PERSONA": "gambit"})
    agent = ClaudeAgentVoice(s, clock=lambda: 100.0)
    msg = _msg("Gambit que horas são")
    asyncio.run(agent.on_user_turn_completed(None, msg))
    assert msg.text_content == "que horas sao"


def test_agent_default_gate_ignores_other_persona_wake():
    s = Settings.from_env(env={"PERSONA": "gambit"})
    agent = ClaudeAgentVoice(s, clock=lambda: 100.0)
    with pytest.raises(StopResponse):
        asyncio.run(agent.on_user_turn_completed(None, _msg("Lilith que horas são")))


def test_vad_kwargs_from_settings():
    s = Settings.from_env(env={"CLAUDE_VOICE_VAD_THRESHOLD": "0.7", "CLAUDE_VOICE_VAD_MIN_SPEECH_S": "0.25"})
    kw = vad_kwargs(s)
    assert kw["activation_threshold"] == 0.7
    assert kw["min_speech_duration"] == 0.25


def test_interruption_kwargs_from_settings():
    s = Settings.from_env(
        env={
            "CLAUDE_VOICE_MIN_INTERRUPT_WORDS": "3",
            "CLAUDE_VOICE_MIN_INTERRUPT_S": "0.8",
            "CLAUDE_VOICE_RESUME_FALSE_INTERRUPT": "false",
        }
    )
    kw = interruption_kwargs(s)
    assert kw["min_interruption_words"] == 3
    assert kw["min_interruption_duration"] == 0.8
    assert kw["resume_false_interruption"] is False
