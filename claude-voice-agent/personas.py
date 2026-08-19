"""Registry de personas selecionáveis (Lilith + Gambit).

Cada persona é um **preset autocontido**: nome, gênero, forma de tratamento, voz,
engine de TTS, wake-words e o system prompt. Um só seletor (``PERSONA=…``) troca o
KIT INTEIRO — não se mistura env var entre personas. Overrides pontuais de voz são
namespaced por persona (``GAMBIT_VOICE`` / ``LILITH_VOICE``), nunca um knob global.

Módulo ``claude_agent_voice/``; aqui só a
persona vira selecionável.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from .persona import CREATOR
from .persona import system_prompt as _system_prompt

DEFAULT_PERSONA = "gambit"


@dataclass(frozen=True)
class Persona:
    key: str
    name: str
    gender: str  # "feminino" | "masculino"
    tts_engine: str  # "kokoro" | "piper"
    voice: str
    wake_words: tuple[str, ...]
    form_of_address: str = "Senhor"

    def system_prompt(self, creator: str = CREATOR) -> str:
        return _system_prompt(
            self.name,
            creator,
            gender=self.gender,
            form_of_address=self.form_of_address,
        )


LILITH = Persona(
    key="lilith",
    name="Lilith",
    gender="feminino",
    tts_engine="kokoro",
    voice="pf_dora",
    # keyword-spotting no transcript do Whisper; variantes comuns de mishear.
    wake_words=("lilith", "lilit", "lili", "lilis", "lilith,"),
)

GAMBIT = Persona(
    key="gambit",
    name="Gambit",
    gender="masculino",
    tts_engine="piper",
    voice="pt_BR-faber-medium",
    wake_words=("gambit", "gambi", "gambito", "gamba", "gambe", "gambit,"),
)

PERSONAS: dict[str, Persona] = {p.key: p for p in (LILITH, GAMBIT)}


def get_persona(key: str | None, env: dict[str, str] | None = None) -> Persona:
    """Resolve o preset da persona a partir do seletor.

    ``key`` vazio/None cai no ``DEFAULT_PERSONA``. ``env`` (opcional) permite um
    override de voz namespaced por persona: ``{KEY}_VOICE`` (ex.: ``GAMBIT_VOICE``).
    Seletor inválido levanta ``ValueError`` com mensagem clara.
    """
    k = (key or DEFAULT_PERSONA).strip().lower()
    if k not in PERSONAS:
        raise ValueError(
            f"persona desconhecida: {key!r}. Opções: {sorted(PERSONAS)}"
        )
    persona = PERSONAS[k]
    if env is not None:
        override = env.get(f"{k.upper()}_VOICE")
        if override:
            persona = replace(persona, voice=override)
    return persona
