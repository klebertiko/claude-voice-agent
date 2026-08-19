"""Filtro de alucinação/ruído do STT — pura, testável, sem estado.

O Whisper em música/ruído de fundo alucina frases curtas e repetitivas
("o que é o que é", "o chá é o que é o chá") ou sílabas soltas. Deixar isso
virar turno faz o agente responder ao nada e (pior) interromper a própria fala.
``is_noise_transcript`` decide se um transcript é lixo que deve ser engolido.

Heurísticas (todas baratas, sem modelo):
- vazio/branco;
- token único muito curto (sílaba solta de ruído);
- baixa diversidade lexical: poucas palavras *distintas* numa fala repetitiva
  (o padrão de alucinação do whisper), exigindo um mínimo de repetição pra não
  pegar comandos curtos legítimos ("bom dia").
"""

from __future__ import annotations

import re
import unicodedata

# Palavra "de conteúdo" curta demais pra ser um comando sozinha.
_MIN_SOLO_LEN = 3
# A partir de quantos tokens a checagem de diversidade vale (evita punir "bom dia").
_REPETITION_MIN_TOKENS = 4
# Fração máxima de palavras distintas p/ considerar alucinação repetitiva.
_MAX_UNIQUE_RATIO = 0.5


def _norm_tokens(text: str) -> list[str]:
    """Minúsculas, sem acento, pontuação fora — tokens comparáveis."""
    nfkd = unicodedata.normalize("NFKD", text.lower())
    stripped = "".join(c for c in nfkd if not unicodedata.combining(c))
    return re.sub(r"[^\w\s]", " ", stripped).split()


def is_noise_transcript(text: str) -> bool:
    """True se o transcript é ruído/alucinação e NÃO deve virar turno."""
    tokens = _norm_tokens(text)
    if not tokens:
        return True
    if len(tokens) == 1:
        # sílaba/palavra solta e curta = ruído; palavra longa isolada pode valer
        return len(tokens[0]) < _MIN_SOLO_LEN
    if len(tokens) >= _REPETITION_MIN_TOKENS:
        unique_ratio = len(set(tokens)) / len(tokens)
        if unique_ratio <= _MAX_UNIQUE_RATIO:
            return True
    # 2–3 tokens: só é ruído se forem todos a mesma palavra repetida
    if len(set(tokens)) == 1:
        return True
    return False
