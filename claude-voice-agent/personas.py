"""Registry de personas selecionáveis (Lilith + Orion).

Cada persona é um **preset autocontido**: nome, gênero, forma de tratamento, voz,
engine de TTS, wake-words e o system prompt. Um só seletor (``PERSONA=…``) troca o
KIT INTEIRO — não se mistura env var entre personas. Overrides pontuais de voz são
namespaced por persona (``ORION_VOICE`` / ``LILITH_VOICE``), nunca um knob global.

Módulo ``claude_agent_voice/``; aqui só a
persona vira selecionável.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from .persona import CREATOR
from .persona import system_prompt as _system_prompt

DEFAULT_PERSONA = "orion"


@dataclass(frozen=True)
class Persona:
    key: str
    name: str
    gender: str  # "feminino" | "masculino"
    tts_engine: str  # "kokoro" | "piper"
    voice: str
    wake_words: tuple[str, ...]
    form_of_address: str = "Senhor"
    # 1.0 = ritmo do modelo. <1 deixa a fala mais medida (mordomo).
    speech_rate: float = 1.0

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

# Daniel carrega a frase; Lewis só clareia. George puro embaçava "Não fiz".
# A 1.2 o Whisper small float32 (beam 5) ainda ouve o nome, as 15 horas e 5
# minutos, a permissão e "Não fiz, Senhor". A 1.24 a recusa vira "senhora".
ORION = Persona(
    key="orion",
    name="Orion",
    gender="masculino",
    tts_engine="kokoro",
    voice="bm_daniel*0.7+bm_lewis*0.3",
    # variantes que o Whisper costuma ouvir no lugar de "Orion".
    # "Orião" chega já sem acento: o portão compara "oriao", não "orion".
    wake_words=("orion", "oriom", "orian", "orions", "oreon", "oriao"),
    speech_rate=1.2,
)


def spoken_voice(spec: str) -> str:
    """Nome falado da voz dominante. ``bm_daniel*0.7+bm_lewis*0.3`` vira daniel."""
    head = spec.split("+", 1)[0].split("*", 1)[0].strip()
    return head.rsplit("_", 1)[-1] or head


PERSONAS: dict[str, Persona] = {p.key: p for p in (LILITH, ORION)}


def get_persona(key: str | None, env: dict[str, str] | None = None) -> Persona:
    """Resolve o preset da persona a partir do seletor.

    ``key`` vazio/None cai no ``DEFAULT_PERSONA``. ``env`` (opcional) permite um
    override de voz namespaced por persona: ``{KEY}_VOICE`` (ex.: ``ORION_VOICE``).
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
