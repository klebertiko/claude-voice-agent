"""TTS kokoro: conversão PCM pura + wiring do engine injetável (sem áudio real)."""

import numpy as np

from claude_agent_voice.tts_kokoro import KokoroTTS, pcm16_bytes


def test_pcm16_silence_is_zero():
    out = pcm16_bytes(np.zeros(8, dtype=np.float32))
    assert out == b"\x00\x00" * 8


def test_pcm16_full_scale_and_clip():
    out = pcm16_bytes(np.array([1.0, -1.0, 2.0, -2.0], dtype=np.float32))
    vals = np.frombuffer(out, dtype="<i2")
    assert vals.tolist() == [32767, -32767, 32767, -32767]  # clip em ±1


def test_pcm16_is_little_endian_int16():
    out = pcm16_bytes(np.array([0.5], dtype=np.float32))
    assert len(out) == 2
    assert np.frombuffer(out, dtype="<i2")[0] == 16383  # round(0.5*32767)


class _FakeKokoro:
    def __init__(self):
        self.calls = []

    def create(self, text, voice, speed, lang):
        self.calls.append((text, voice, speed, lang))
        return np.zeros(4, dtype=np.float32), 24000


def test_create_passes_voice_lang_speed_to_engine():
    fake = _FakeKokoro()
    t = KokoroTTS(
        model_path="m.onnx",
        voices_path="v.bin",
        voice="pf_dora",
        lang="pt-br",
        speed=1.1,
        engine=fake,
    )
    _samples, sr = t.create("Olá")
    assert sr == 24000
    assert fake.calls == [("Olá", "pf_dora", 1.1, "pt-br")]


def test_capabilities_non_streaming():
    t = KokoroTTS(model_path="m", voices_path="v", engine=_FakeKokoro())
    assert t.capabilities.streaming is False
    assert t.sample_rate == 24000
    assert t.num_channels == 1
