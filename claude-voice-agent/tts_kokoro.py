"""TTS kokoro-onnx plugado no LiveKit Agents (voz local pt-BR).

kokoro devolve float32 mono em 24 kHz; o LiveKit quer PCM16. A conversão vive em
``pcm16_bytes`` — pura, sem áudio, testável. A carga do modelo é TARDIA (só no
primeiro synth) e roda em thread (``asyncio.to_thread``) pra não travar o loop.
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

SAMPLE_RATE = 24000  # kokoro-v1.0


def parse_voice_spec(spec: str) -> list[tuple[str, float]]:
    """``bm_george*0.7+pm_santa*0.3`` vira pesos que somam 1.

    Um nome só (``pm_alex``) continua uma voz inteira. Os pesos são
    normalizados, então ``a*2+b*1`` equivale a 2/3 e 1/3.
    """
    if "*" not in spec and "+" not in spec:
        return [(spec, 1.0)]
    parts: list[tuple[str, float]] = []
    for piece in spec.split("+"):
        name, sep, weight = piece.partition("*")
        name = name.strip()
        if not name:
            raise ValueError(f"voz inválida: {spec!r}")
        parts.append((name, float(weight) if sep else 1.0))
    total = sum(weight for _, weight in parts)
    if total <= 0:
        raise ValueError(f"voz inválida: {spec!r}")
    return [(name, weight / total) for name, weight in parts]


def mix_voice(engine, spec: str):
    """Nome de voz, ou a matriz de estilo misturada quando o spec tem ``+``."""
    parts = parse_voice_spec(spec)
    if len(parts) == 1 and abs(parts[0][1] - 1.0) < 1e-9:
        return parts[0][0]
    mixed = None
    for name, weight in parts:
        style = np.asarray(engine.get_voice_style(name), dtype=np.float32)
        mixed = style * weight if mixed is None else mixed + style * weight
    return mixed


def pcm16_bytes(samples) -> bytes:
    """float32/64 em [-1,1] -> PCM16 little-endian. Pura e determinística."""
    arr = np.asarray(samples, dtype=np.float32)
    arr = np.clip(arr, -1.0, 1.0)
    return (arr * 32767.0).astype("<i2").tobytes()


class KokoroTTS(tts.TTS):
    def __init__(
        self,
        *,
        model_path: Path,
        voices_path: Path,
        voice: str = "pf_dora",
        lang: str = "pt-br",
        speed: float = 1.0,
        engine: object | None = None,
    ) -> None:
        super().__init__(
            capabilities=tts.TTSCapabilities(streaming=False),
            sample_rate=SAMPLE_RATE,
            num_channels=1,
        )
        self._model_path = Path(model_path)
        self._voices_path = Path(voices_path)
        self._voice = voice
        self._lang = lang
        self._speed = speed
        self._engine = engine  # injetável nos testes

    def _get_engine(self) -> object:
        if self._engine is None:
            from kokoro_onnx import Kokoro  # import tardio

            self._engine = Kokoro(str(self._model_path), str(self._voices_path))
        return self._engine

    def create(self, text: str):
        """Síntese crua -> (samples float32, sample_rate). Usada pelo stream."""
        engine = self._get_engine()
        return engine.create(
            text,
            voice=mix_voice(engine, self._voice),
            speed=self._speed,
            lang=self._lang,
        )

    def synthesize(
        self,
        text: str,
        *,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
    ) -> KokoroChunkedStream:
        return KokoroChunkedStream(tts=self, input_text=text, conn_options=conn_options)


class KokoroChunkedStream(tts.ChunkedStream):
    async def _run(self, output_emitter: tts.AudioEmitter) -> None:
        engine_tts: KokoroTTS = self._tts  # type: ignore[assignment]
        samples, sample_rate = await asyncio.to_thread(
            lambda: engine_tts.create(self._input_text)
        )
        output_emitter.initialize(
            request_id=utils.shortuuid(),
            sample_rate=int(sample_rate),
            num_channels=1,
            mime_type="audio/pcm",
        )
        output_emitter.push(pcm16_bytes(samples))
        output_emitter.flush()
