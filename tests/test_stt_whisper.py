"""STT whisper: DSP puro (mono/16k) + wiring do engine injetável (sem modelo real)."""

import numpy as np

from claude_agent_voice.stt_whisper import WhisperSTT, to_mono16k


def _pcm16(floats) -> bytes:
    return (np.asarray(floats, dtype=np.float32) * 32767).astype("<i2").tobytes()


def test_mono16k_passthrough_when_already_16k_mono():
    out = to_mono16k(_pcm16([0.0, 0.5, -0.5, 1.0]), sample_rate=16000, num_channels=1)
    assert out.dtype == np.float32
    assert out.shape == (4,)
    assert abs(out[1] - 0.5) < 1e-3


def test_stereo_is_downmixed_to_mono():
    # L=1.0 R=-1.0 -> média 0.0 ; L=0.5 R=0.5 -> 0.5
    out = to_mono16k(_pcm16([1.0, -1.0, 0.5, 0.5]), sample_rate=16000, num_channels=2)
    assert out.shape == (2,)
    assert abs(out[0]) < 1e-3
    assert abs(out[1] - 0.5) < 1e-3


def test_resample_halves_length_from_32k_to_16k():
    x = np.sin(np.linspace(0, 6.28, 320)).astype(np.float32)
    out = to_mono16k(_pcm16(x), sample_rate=32000, num_channels=1)
    assert out.shape == (160,)  # 320 * 16000/32000


def test_empty_pcm_yields_empty():
    out = to_mono16k(b"", sample_rate=48000, num_channels=1)
    assert out.size == 0


class _Seg:
    def __init__(self, text):
        self.text = text


class _FakeWhisper:
    def __init__(self):
        self.calls = []
        self.kwargs = []

    def transcribe(self, audio, language, beam_size, **kwargs):
        self.calls.append((len(audio), language, beam_size))
        self.kwargs.append(kwargs)
        return [_Seg(" olá"), _Seg(" mundo")], {"language": language}


def test_transcribe_array_joins_segments_and_strips():
    fake = _FakeWhisper()
    s = WhisperSTT(language="pt", engine=fake)
    text = s.transcribe_array(np.zeros(16000, dtype=np.float32))
    assert text == "olá mundo"
    assert fake.calls == [(16000, "pt", 1)]


def test_transcribe_uses_anti_hallucination_params():
    # ruído/música fazem o whisper alucinar em loop; params endurecidos cortam isso
    fake = _FakeWhisper()
    s = WhisperSTT(language="pt", engine=fake)
    s.transcribe_array(np.zeros(16000, dtype=np.float32))
    kw = fake.kwargs[0]
    assert kw["condition_on_previous_text"] is False
    assert kw["temperature"] == 0.0
    assert kw["vad_filter"] is True


def test_capabilities_non_streaming():
    s = WhisperSTT(engine=_FakeWhisper())
    assert s.capabilities.streaming is False
