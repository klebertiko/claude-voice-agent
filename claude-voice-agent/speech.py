"""Limpeza do texto do cérebro antes do TTS: nada de emoji/markdown falado.

A Claude às vezes devolve emoji, ``**negrito**``, backticks — o kokoro tentaria
ler isso. ``strip_for_speech`` deixa só o que faz sentido em voz alta. Pura.
"""

from __future__ import annotations

import re

# Faixas de emoji/símbolos + seletores de variação e ZWJ.
_EMOJI = re.compile(
    "[\U0001f000-\U0001faff\U00002600-\U000027bf\U0001f1e6-\U0001f1ff"
    "\U00002190-\U000021ff\U00002b00-\U00002bff️‍]"
)
_MD = re.compile(r"[*_`#>]+")


def strip_for_speech(text: str) -> str:
    """Remove emoji e marcas de markdown; normaliza espaços."""
    text = _EMOJI.sub("", text)
    text = _MD.sub("", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"[ \t]*\n[ \t]*", "\n", text)  # sem espaço em volta das quebras
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()
