"""Wake-word gating do agente de voz.

MVP: a "wake-word" é detectada por *keyword-spotting* no transcript do STT —
não há modelo dedicado (Porcupine/openWakeWord) nesta fatia. Isso evita treinar
um modelo de "Lilith" e roda com o Whisper que já temos.

Comportamento estilo JARVIS: dizer "Lilith" abre uma *janela de conversa*; dentro
dela os turnos seguintes NÃO precisam repetir o nome (até expirar por silêncio).
Toda decisão é pura e o relógio é injetado (``now``), então é 100% testável.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

_DEFAULT_WAKE = ("lilith", "lilit", "lili", "lilis", "lilith,")
# Janela em que, após o wake, a conversa segue sem repetir o nome.
_DEFAULT_WINDOW_S = 30.0


def _normalize(text: str) -> str:
    """Minúsculas, sem acento, pontuação virando espaço — p/ casar 'Lilith!'."""
    nfkd = unicodedata.normalize("NFKD", text.lower())
    stripped = "".join(c for c in nfkd if not unicodedata.combining(c))
    return re.sub(r"[^\w\s]", " ", stripped)


@dataclass
class WakeGate:
    """Decide, a cada transcript, se o agente deve responder.

    - Fora da janela: só responde se a wake-word aparecer; devolve o texto com o
      nome removido do início.
    - Dentro da janela: responde a qualquer fala e renova a janela.
    """

    wake_words: tuple[str, ...] = _DEFAULT_WAKE
    window_s: float = _DEFAULT_WINDOW_S
    _active_until: float = field(default=0.0, init=False)

    def is_active(self, now: float) -> bool:
        return now < self._active_until

    def _strip_wake(self, tokens: list[str]) -> str:
        """Remove a wake-word (e um vocativo à frente) e devolve o resto."""
        i = 0
        while i < len(tokens) and tokens[i] in self.wake_words:
            i += 1
        return " ".join(tokens[i:]).strip()

    def process(self, transcript: str, now: float) -> tuple[bool, str]:
        """Retorna ``(deve_responder, texto_limpo)``.

        ``texto_limpo`` é o comando sem a wake-word. Se a fala foi só o nome
        ("Lilith?"), o texto vem vazio mas ``deve_responder`` é True (ela
        atende, tipo "Pois não?").
        """
        norm = _normalize(transcript)
        tokens = norm.split()
        if not tokens:
            return (self.is_active(now), transcript.strip())

        has_wake = any(w in self.wake_words for w in tokens)

        if self.is_active(now):
            self._active_until = now + self.window_s
            cleaned = self._strip_wake(tokens) if tokens[0] in self.wake_words else norm
            return (True, cleaned.strip())

        if has_wake:
            self._active_until = now + self.window_s
            # remove a primeira ocorrência do nome onde quer que esteja
            idx = next(i for i, t in enumerate(tokens) if t in self.wake_words)
            rest = tokens[:idx] + tokens[idx + 1 :]
            return (True, " ".join(rest).strip())

        return (False, "")

    def close(self) -> None:
        """Fecha a janela imediatamente (ex.: após 'tchau, Lilith')."""
        self._active_until = 0.0
