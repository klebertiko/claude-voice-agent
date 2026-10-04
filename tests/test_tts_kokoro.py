"""TTS kokoro: conversão PCM pura + wiring do engine injetável (sem áudio real)."""

import numpy as np

from claude_agent_voice.tts_kokoro import KokoroTTS, mix_voice, parse_voice_spec, pcm16_bytes


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


def test_parse_voice_spec_single_and_blend():
    assert parse_voice_spec("pm_alex") == [("pm_alex", 1.0)]
    mixed = parse_voice_spec("bm_george*0.7+pm_santa*0.3")
    assert mixed[0][0] == "bm_george" and abs(mixed[0][1] - 0.7) < 1e-9
    assert mixed[1][0] == "pm_santa" and abs(mixed[1][1] - 0.3) < 1e-9
    equal = parse_voice_spec("a+b")
    assert abs(equal[0][1] - 0.5) < 1e-9 and abs(equal[1][1] - 0.5) < 1e-9


def test_mix_voice_sends_weighted_style_to_engine():
    class _Styles:
        def __init__(self):
            self.calls = []

        def get_voice_style(self, name):
            return np.array([1.0, 0.0] if name == "bm_george" else [0.0, 1.0], dtype=np.float32)

        def create(self, text, voice, speed, lang):
            self.calls.append(voice.copy())
            return np.zeros(2, dtype=np.float32), 24000

    engine = _Styles()
    t = KokoroTTS(
        model_path="m.onnx",
        voices_path="v.bin",
        voice="bm_george*0.7+pm_santa*0.3",
        lang="pt-br",
        speed=0.84,
        engine=engine,
    )
    t.create("Senhor")
    got = engine.calls[0]
    assert np.allclose(got, np.array([0.7, 0.3], dtype=np.float32))
    assert mix_voice(engine, "pm_alex") == "pm_alex"


def test_capabilities_non_streaming():
    t = KokoroTTS(model_path="m", voices_path="v", engine=_FakeKokoro())
    assert t.capabilities.streaming is False
    assert t.sample_rate == 24000
    assert t.num_channels == 1
