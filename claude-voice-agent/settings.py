"""Configuração do agente de voz, lida do ambiente com defaults sensatos.

Um só lugar para 'qual voz / qual modelo / precisa de wake-word / onde está o
modelo kokoro'. Puro e testável (recebe um dict de env injetável).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

_CACHE = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "claude-voice"


@dataclass(frozen=True)
class Settings:
    # Persona ativa — seletor NEUTRO (não prefixado com nome de persona); traz o
    # kit inteiro (voz/engine/wake/prompt) via claude_agent_voice.personas.get_persona.
    persona: str = "gambit"
    # Voz (kokoro — persona Lilith)
    voice: str = "pf_dora"
    lang: str = "pt-br"
    speed: float = 1.0
    kokoro_model: Path = _CACHE / "kokoro-v1.0.onnx"
    kokoro_voices: Path = _CACHE / "voices-v1.0.bin"
    # Voz (Piper — persona Gambit): ONNX local + config no cache.
    piper_model: Path = _CACHE / "pt_BR-faber-medium.onnx"
    piper_config: Path = _CACHE / "pt_BR-faber-medium.onnx.json"
    # Ritmo da fala do Piper: >1.0 = mais lento (default do faber é rápido demais).
    piper_length_scale: float = 1.2
    # Ouvido (faster-whisper)
    whisper_model: str = "small"
    # CPU por padrão: o ctranslate2 GPU exige libs CUDA 12 (cublas64_12.dll) que
    # esta máquina (CUDA 13.1) não tem. GPU vira opt-in via CLAUDE_VOICE_WHISPER_DEVICE=cuda.
    whisper_device: str = "cpu"
    whisper_compute: str = "int8"
    whisper_lang: str = "pt"
    # Cérebro (Claude via subscription — CLI `claude -p`, sem API key)
    llm_model: str | None = None  # None => modelo default do CLI/assinatura
    claude_cli: str = "claude"
    # Wake-word
    require_wake: bool = True
    wake_window_s: float = 30.0
    # Robustez a ruído — VAD menos sensível que o default do silero (0.5), pra
    # ruído de fundo/cozinha não abrir turno nem interromper a fala dela.
    vad_threshold: float = 0.7
    vad_min_speech_s: float = 0.2
    # Barge-in exigente: só interrompe a fala dela com fala real e sustentada
    # (>=1s e >=3 palavras); ruído curto ou palavra solta não corta. Retoma se a
    # "interrupção" foi ruído sem transcrição (resume_false_interrupt).
    min_interrupt_words: int = 3
    min_interrupt_s: float = 1.0
    resume_false_interrupt: bool = True

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> Settings:
        e = os.environ if env is None else env

        def _bool(key: str, default: bool) -> bool:
            v = e.get(key)
            return (
                default
                if v is None
                else v.strip().lower() in ("1", "true", "yes", "sim")
            )

        return cls(
            persona=e.get("PERSONA", cls.persona),
            voice=e.get("CLAUDE_VOICE_VOICE", cls.voice),
            lang=e.get("CLAUDE_VOICE_LANG", cls.lang),
            speed=float(e.get("CLAUDE_VOICE_SPEED", cls.speed)),
            kokoro_model=Path(
                e.get("CLAUDE_VOICE_KOKORO_MODEL", str(cls.kokoro_model))
            ),
            kokoro_voices=Path(
                e.get("CLAUDE_VOICE_KOKORO_VOICES", str(cls.kokoro_voices))
            ),
            piper_model=Path(
                e.get("CLAUDE_VOICE_PIPER_MODEL", str(cls.piper_model))
            ),
            piper_config=Path(
                e.get("CLAUDE_VOICE_PIPER_CONFIG", str(cls.piper_config))
            ),
            piper_length_scale=float(
                e.get("CLAUDE_VOICE_PIPER_LENGTH_SCALE", cls.piper_length_scale)
            ),
            whisper_model=e.get("CLAUDE_VOICE_WHISPER_MODEL", cls.whisper_model),
            whisper_device=e.get("CLAUDE_VOICE_WHISPER_DEVICE", cls.whisper_device),
            whisper_compute=e.get("CLAUDE_VOICE_WHISPER_COMPUTE", cls.whisper_compute),
            whisper_lang=e.get("CLAUDE_VOICE_WHISPER_LANG", cls.whisper_lang),
            llm_model=e.get("CLAUDE_VOICE_LLM_MODEL") or None,
            claude_cli=e.get("CLAUDE_VOICE_CLAUDE_CLI", cls.claude_cli),
            require_wake=_bool("CLAUDE_VOICE_REQUIRE_WAKE", cls.require_wake),
            wake_window_s=float(e.get("CLAUDE_VOICE_WAKE_WINDOW_S", cls.wake_window_s)),
            vad_threshold=float(e.get("CLAUDE_VOICE_VAD_THRESHOLD", cls.vad_threshold)),
            vad_min_speech_s=float(
                e.get("CLAUDE_VOICE_VAD_MIN_SPEECH_S", cls.vad_min_speech_s)
            ),
            min_interrupt_words=int(
                e.get("CLAUDE_VOICE_MIN_INTERRUPT_WORDS", cls.min_interrupt_words)
            ),
            min_interrupt_s=float(
                e.get("CLAUDE_VOICE_MIN_INTERRUPT_S", cls.min_interrupt_s)
            ),
            resume_false_interrupt=_bool(
                "CLAUDE_VOICE_RESUME_FALSE_INTERRUPT", cls.resume_false_interrupt
            ),
        )
