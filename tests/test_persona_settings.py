"""Contrato da persona e da configuração da Lilith."""

from pathlib import Path

from claude_agent_voice.persona import system_prompt
from claude_agent_voice.settings import Settings


def test_persona_names_lilith_and_creator():
    p = system_prompt()
    assert "Lilith" in p
    assert "Kleber" in p


def test_persona_is_voice_optimized():
    p = system_prompt().lower()
    # deve instruir fala curta e proibir markdown/código
    assert "curt" in p
    assert "markdown" in p
    assert "português" in p or "portugues" in p


def test_persona_is_parametrizable():
    p = system_prompt(name="Aria", creator="Ana")
    assert "Aria" in p and "Ana" in p


def test_settings_defaults():
    s = Settings.from_env(env={})
    assert s.voice == "pf_dora"
    assert s.lang == "pt-br"
    assert s.whisper_model == "small"
    assert s.whisper_device == "cpu"  # GPU exige libs CUDA 12; opt-in
    assert s.require_wake is True
    assert s.llm_model is None
    assert s.kokoro_model.name == "kokoro-v1.0.onnx"


def test_settings_env_override():
    s = Settings.from_env(
        env={
            "CLAUDE_VOICE_VOICE": "pf_alex",
            "CLAUDE_VOICE_WHISPER_MODEL": "medium",
            "CLAUDE_VOICE_REQUIRE_WAKE": "false",
            "CLAUDE_VOICE_WAKE_WINDOW_S": "12.5",
            "CLAUDE_VOICE_LLM_MODEL": "claude-sonnet-5",
            "CLAUDE_VOICE_KOKORO_MODEL": r"C:\models\k.onnx",
        }
    )
    assert s.voice == "pf_alex"
    assert s.whisper_model == "medium"
    assert s.require_wake is False
    assert s.wake_window_s == 12.5
    assert s.llm_model == "claude-sonnet-5"
    assert s.kokoro_model == Path(r"C:\models\k.onnx")


def test_settings_empty_llm_model_is_none():
    s = Settings.from_env(env={"CLAUDE_VOICE_LLM_MODEL": ""})
    assert s.llm_model is None


def test_settings_persona_default_is_gambit():
    s = Settings.from_env(env={})
    assert s.persona == "gambit"
    assert s.piper_model.name == "pt_BR-faber-medium.onnx"
    assert s.piper_config.name == "pt_BR-faber-medium.onnx.json"


def test_settings_persona_env_override():
    s = Settings.from_env(env={"PERSONA": "lilith"})
    assert s.persona == "lilith"


def test_settings_piper_length_scale_default_slower():
    s = Settings.from_env(env={})
    assert s.piper_length_scale == 1.2  # >1.0 = fala mais lenta


def test_settings_piper_length_scale_env_override():
    s = Settings.from_env(env={"CLAUDE_VOICE_PIPER_LENGTH_SCALE": "1.35"})
    assert s.piper_length_scale == 1.35


def test_noise_robustness_defaults():
    s = Settings.from_env(env={})
    # VAD bem menos sensível que o default do silero (0.5) p/ não abrir turno
    # nem cortar a fala em ruído de fundo.
    assert s.vad_threshold == 0.7
    assert s.vad_min_speech_s == 0.2
    # barge-in exigente: só corta a fala com fala real e sustentada (>=1s, 3
    # palavras); ruído curto/uma palavra solta não interrompe.
    assert s.min_interrupt_words == 3
    assert s.min_interrupt_s == 1.0
    assert s.resume_false_interrupt is True


def test_noise_robustness_env_override():
    s = Settings.from_env(
        env={
            "CLAUDE_VOICE_VAD_THRESHOLD": "0.75",
            "CLAUDE_VOICE_VAD_MIN_SPEECH_S": "0.3",
            "CLAUDE_VOICE_MIN_INTERRUPT_WORDS": "3",
            "CLAUDE_VOICE_MIN_INTERRUPT_S": "0.8",
            "CLAUDE_VOICE_RESUME_FALSE_INTERRUPT": "false",
        }
    )
    assert s.vad_threshold == 0.75
    assert s.vad_min_speech_s == 0.3
    assert s.min_interrupt_words == 3
    assert s.min_interrupt_s == 0.8
    assert s.resume_false_interrupt is False
