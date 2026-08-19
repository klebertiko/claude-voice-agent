"""STT do agente de voz: faster-whisper plugado no LiveKit Agents (ouvido local pt-BR).

faster-whisper é batch (não-streaming): implementamos ``_recognize_impl`` e o
LiveKit embrulha com ``stt.StreamAdapter`` + VAD (silero) pra fatiar a fala.
Whisper quer float32 mono 16 kHz; o mic vem em outra taxa/canais, então
``to_mono16k`` (pura, testável) faz downmix + resample linear.
"""

from __future__ import annotations

import asyncio

import numpy as np
from livekit import rtc
from livekit.agents import (
    DEFAULT_API_CONNECT_OPTIONS,
    NOT_GIVEN,
    APIConnectOptions,
    NotGivenOr,
    stt,
)
from livekit.agents.utils import AudioBuffer

WHISPER_RATE = 16000


def to_mono16k(pcm: bytes, sample_rate: int, num_channels: int) -> np.ndarray:
    """PCM16 (qualquer taxa/canais) -> float32 mono 16 kHz. Pura e determinística."""
    x = np.frombuffer(pcm, dtype="<i2").astype(np.float32) / 32768.0
    if num_channels > 1:
        x = x.reshape(-1, num_channels).mean(axis=1)
    if sample_rate != WHISPER_RATE and len(x) > 1:
        n_out = round(len(x) * WHISPER_RATE / sample_rate)
        if n_out <= 0:
            return np.zeros(0, dtype=np.float32)
        x = np.interp(
            np.linspace(0.0, len(x) - 1, n_out),
            np.arange(len(x)),
            x,
        )
    return x.astype(np.float32)


class WhisperSTT(stt.STT):
    def __init__(
        self,
        *,
        model: str = "small",
        device: str = "auto",
        compute_type: str = "int8",
        language: str = "pt",
        engine: object | None = None,
    ) -> None:
        super().__init__(
            capabilities=stt.STTCapabilities(streaming=False, interim_results=False)
        )
        self._name = model
        self._device = device
        self._compute = compute_type
        self._lang = language
        self._engine = engine  # injetável nos testes

    def _get_engine(self) -> object:
        if self._engine is None:
            from faster_whisper import WhisperModel  # import tardio

            self._engine = WhisperModel(
                self._name, device=self._device, compute_type=self._compute
            )
        return self._engine

    def transcribe_array(self, audio16k: np.ndarray) -> str:
        """float32 16 kHz -> texto. Bloqueante; chame via to_thread.

        Params anti-alucinação (ruído/música fazem o whisper delirar em loop):
        - ``condition_on_previous_text=False``: sem realimentar o próprio texto,
          quebra o loop de repetição ("o que é o que é...");
        - ``temperature=0.0``: decodificação determinística, sem fallback amostrado;
        - ``vad_filter=True``: o VAD interno corta trechos sem fala antes do decode.
        """
        segments, _info = self._get_engine().transcribe(
            audio16k,
            language=self._lang,
            beam_size=1,
            condition_on_previous_text=False,
            temperature=0.0,
            vad_filter=True,
        )
        # segmentos do whisper já trazem espaço à esquerda -> concatena direto.
        return "".join(seg.text for seg in segments).strip()

    async def _recognize_impl(
        self,
        buffer: AudioBuffer,
        *,
        language: NotGivenOr[str] = NOT_GIVEN,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
    ) -> stt.SpeechEvent:
        frame = rtc.combine_audio_frames(buffer)
        audio = to_mono16k(bytes(frame.data), frame.sample_rate, frame.num_channels)
        text = (
            ""
            if audio.size == 0
            else await asyncio.to_thread(self.transcribe_array, audio)
        )
        return stt.SpeechEvent(
            type=stt.SpeechEventType.FINAL_TRANSCRIPT,
            alternatives=[stt.SpeechData(language=self._lang, text=text)],
        )
