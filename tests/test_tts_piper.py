"""TTS Piper: concatenação de PCM16 pura + wiring do engine injetável (sem modelo)."""

import numpy as np

from claude_agent_voice.tts_piper import SAMPLE_RATE, PiperTTS, pcm16_from_chunks


def test_pcm16_from_chunks_raw_bytes():
    out = pcm16_from_chunks([b"\x01\x00", b"\x02\x00"])
    assert out == b"\x01\x00\x02\x00"


class _AudioChunk:
    """Espelha o AudioChunk do piper >=1.3 (expõe audio_int16_bytes)."""

    def __init__(self, b: bytes) -> None:
        self.audio_int16_bytes = b


def test_pcm16_from_chunks_audiochunk_objects():
    out = pcm16_from_chunks([_AudioChunk(b"\x10\x00"), _AudioChunk(b"\x20\x00")])
    assert out == b"\x10\x00\x20\x00"


def test_pcm16_from_chunks_ndarray_int16():
    out = pcm16_from_chunks([np.array([1, -1], dtype=np.int16)])
    assert np.frombuffer(out, dtype="<i2").tolist() == [1, -1]


class _FakePiper:
    def __init__(self) -> None:
        self.texts: list[str] = []
        self.syn_configs: list[object] = []

    def synthesize(self, text, syn_config=None):
        self.texts.append(text)
        self.syn_configs.append(syn_config)
        yield _AudioChunk(b"\x10\x00")
        yield _AudioChunk(b"\x20\x00")


def test_create_pcm_streams_engine_chunks():
    fake = _FakePiper()
    t = PiperTTS(model_path="m.onnx", config_path="m.onnx.json", engine=fake)
    pcm = t.create_pcm("olá senhor")
    assert pcm == b"\x10\x00\x20\x00"
    assert fake.texts == ["olá senhor"]


def test_no_length_scale_sends_no_syn_config():
    fake = _FakePiper()
    t = PiperTTS(model_path="m", config_path="c", engine=fake)
    t.create_pcm("oi")
    assert fake.syn_configs == [None]


def test_length_scale_slows_speech_via_syn_config():
    # length_scale maior = fala mais lenta; deve chegar no SynthesisConfig do piper
    fake = _FakePiper()
    t = PiperTTS(model_path="m", config_path="c", length_scale=1.3, engine=fake)
    t.create_pcm("oi")
    assert fake.syn_configs[0].length_scale == 1.3


def test_capabilities_non_streaming_22050_mono():
    t = PiperTTS(model_path="m", config_path="c", engine=_FakePiper())
    assert t.capabilities.streaming is False
    assert t.sample_rate == SAMPLE_RATE == 22050
    assert t.num_channels == 1
