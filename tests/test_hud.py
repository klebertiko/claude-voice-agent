"""Painel de voz: fallback falado, wake-gate e página sem vídeo."""

import json
import urllib.request
from datetime import datetime

from claude_agent_voice.hud import (
    HudSession,
    make_reply_fn,
    spoken_fallback,
    take_turn,
)
from claude_agent_voice.hud_page import render_page
from claude_agent_voice.personas import get_persona
from claude_agent_voice.settings import Settings
from claude_agent_voice.wake import WakeGate
from claude_agent_voice.web import VoiceHud, serve, wav_bytes


WHEN = datetime(2026, 10, 2, 15, 5)


def _session() -> HudSession:
    persona = get_persona("orion")
    return HudSession(
        persona=persona,
        gate=WakeGate(wake_words=persona.wake_words, window_s=30),
    )


def _reply(cleaned, _history):
    return spoken_fallback(cleaned, "Orion", WHEN)


def test_spoken_clock_and_date():
    assert spoken_fallback("que horas são", "Orion", WHEN) == (
        "São 15 horas e 5 minutos, Senhor."
    )
    assert spoken_fallback("hora", "Orion", datetime(2026, 10, 2, 1, 0)) == (
        "São 1 hora, Senhor."
    )
    assert "sexta-feira, 2 de outubro" in spoken_fallback("que dia é hoje", "Orion", WHEN)
    assert spoken_fallback("", "Orion", WHEN).startswith("Pois não")


def test_turn_without_wake_is_ignored():
    result = take_turn(_session(), "que horas são", 10.0, _reply)
    assert result.status == "ignored"
    assert result.reply == ""


def test_turn_with_wake_answers_and_remembers():
    session = _session()
    result = take_turn(session, "Orion, que horas são", 10.0, _reply)
    assert result.status == "replied"
    assert "15 horas" in result.reply
    assert session.history[0][0] == "user"
    assert "horas" in session.history[0][1]


def test_noise_does_not_open_a_turn():
    result = take_turn(_session(), "o que é o que é o que é", 10.0, _reply)
    assert result.status == "noise"


def test_missing_brain_uses_spoken_fallback():
    settings = Settings.from_env(env={"CLAUDE_VOICE_CLAUDE_CLI": "claude-does-not-exist"})
    reply = make_reply_fn(settings, get_persona("orion"), lambda: WHEN)
    assert "15 horas" in reply("que horas", [])


def test_page_has_microphone_and_no_camera():
    page = render_page("Orion", "Orion")
    assert "Orion" in page
    assert "<video" not in page.lower()
    assert "video: true" not in page
    assert "getUserMedia({ audio: true, video: false })" in page
    assert "sem câmera" not in page
    assert 'id="field"' in page
    assert 'id="log"' in page


def test_wav_bytes_header():
    wav = wav_bytes(b"\x00\x00" * 4, 24000)
    assert wav.startswith(b"RIFF")
    assert wav[8:12] == b"WAVE"


def test_http_turn_greeting_and_ignore():
    calls = []

    def synth(text: str):
        calls.append(text)
        return b"\x00\x00" * 4, 24000

    hud = VoiceHud(
        session=_session(),
        reply_fn=_reply,
        synth_fn=synth,
        transcribe_fn=lambda pcm, rate: "Orion ola",
        clock=lambda t={"n": 0.0}: t.__setitem__("n", t["n"] + 100) or t["n"],
    )
    httpd = serve(hud, "127.0.0.1", 0)
    port = httpd.server_address[1]
    try:
        page = urllib.request.urlopen(f"http://127.0.0.1:{port}/").read().decode()
        assert "video: false" in page

        def post(path, payload):
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}{path}",
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req) as res:
                return json.load(res)

        greeted = post("/api/greeting", {})
        again = post("/api/greeting", {})
        assert greeted["reply"]
        assert "Orion aqui" not in greeted["reply"]
        assert "chamar pelo nome" not in greeted["reply"]
        assert again["reply"] != greeted["reply"]
        assert greeted["audio_b64"]

        answered = post("/api/turn", {"text": "Orion, que horas são"})
        assert answered["status"] == "replied"
        assert "15 horas" in answered["reply"]
        assert answered["audio_b64"]

        ignored = post("/api/turn", {"text": "somente isso"})
        assert ignored["status"] == "ignored"
        assert ignored["audio_b64"] is None

        heard = post("/api/turn", {"pcm_b64": "AAAA", "sample_rate": 16000})
        assert heard["heard"] == "Orion ola"
        assert heard["status"] == "replied"
    finally:
        httpd.shutdown()
