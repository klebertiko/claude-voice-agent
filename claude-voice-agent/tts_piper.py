"""TTS do Gambit: Piper (ONNX local) plugado no LiveKit Agents — voz masculina BR.

Espelha ``tts_kokoro.KokoroTTS``: carga TARDIA do modelo (só no primeiro synth),
síntese em thread (``asyncio.to_thread``), engine injetável nos testes. Diferente
do kokoro (float32 24 kHz), o Piper já devolve **PCM16** — ``pcm16_from_chunks``
(pura, sem áudio) só concatena os chunks. ``pt_BR-faber-medium`` roda a 22050 Hz.

Runtime 100% offline: o modelo ONNX é local; o único fetch é o download único do
``.onnx``/``.onnx.json`` do HF pro cache (fora deste módulo).
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import numpy as np
from livekit.agents import (
    DEFAULT_API_CONNECT_OPTIONS,
    APIConnectOptions,
    tts,
    utils,
)

SAMPLE_RATE = 22050  # pt_BR-faber-medium


def pcm16_from_chunks(chunks) -> bytes:
    """Concatena os chunks do Piper em PCM16 little-endian. Pura e determinística.

    Aceita as formas que a API do piper pode emitir: bytes crus, ``AudioChunk``
    (com ``.audio_int16_bytes``, piper >=1.3) ou ``ndarray`` int16.
    """
    out = bytearray()
    for c in chunks:
        if isinstance(c, (bytes, bytearray)):
            out += bytes(c)
        elif isinstance(c, np.ndarray):
            out += c.astype("<i2").tobytes()
        elif hasattr(c, "audio_int16_bytes"):
            out += bytes(c.audio_int16_bytes)
        else:
            raise TypeError(f"chunk piper não reconhecido: {type(c)!r}")
    return bytes(out)


class PiperTTS(tts.TTS):
    def __init__(
        self,
        *,
        model_path: Path | str,
        config_path: Path | str | None = None,
        voice: str | None = None,
        sample_rate: int = SAMPLE_RATE,
        length_scale: float | None = None,
        engine: object | None = None,
    ) -> None:
        super().__init__(
            capabilities=tts.TTSCapabilities(streaming=False),
            sample_rate=sample_rate,
            num_channels=1,
        )
        self._model_path = Path(model_path)
        self._config_path = Path(config_path) if config_path else None
        self._voice = voice
        self._sample_rate = sample_rate
        # length_scale controla o ritmo da fala: >1.0 = mais lento. None = default do modelo.
        self._length_scale = length_scale
        self._engine = engine  # injetável nos testes

    def _syn_config(self):
        """SynthesisConfig do piper (só quando há tuning), senão None (default do modelo)."""
        if self._length_scale is None:
            return None
        from piper import SynthesisConfig  # import tardio

        return SynthesisConfig(length_scale=self._length_scale)

    def _get_engine(self) -> object:
        if self._engine is None:
            from piper import PiperVoice  # import tardio

            self._engine = PiperVoice.load(
                str(self._model_path),
                config_path=(str(self._config_path) if self._config_path else None),
            )
        return self._engine

    def create_pcm(self, text: str) -> bytes:
        """Texto -> PCM16 bytes. Bloqueante; chame via ``to_thread``."""
        return pcm16_from_chunks(
            self._get_engine().synthesize(text, self._syn_config())
        )

    def synthesize(
        self,
        text: str,
        *,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
    ) -> PiperChunkedStream:
        return PiperChunkedStream(tts=self, input_text=text, conn_options=conn_options)


class PiperChunkedStream(tts.ChunkedStream):
    async def _run(self, output_emitter: tts.AudioEmitter) -> None:
        engine_tts: PiperTTS = self._tts  # type: ignore[assignment]
        pcm = await asyncio.to_thread(lambda: engine_tts.create_pcm(self._input_text))
        output_emitter.initialize(
            request_id=utils.shortuuid(),
            sample_rate=engine_tts._sample_rate,
            num_channels=1,
            mime_type="audio/pcm",
        )
        output_emitter.push(pcm)
        output_emitter.flush()
