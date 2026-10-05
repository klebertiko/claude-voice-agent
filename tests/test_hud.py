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
    assert "sexta-feira, 2 de outubro" in spoken_fallback("qual é a data", "Orion", WHEN)
    assert "sexta-feira, 2 de outubro" in spoken_fallback("me diz a data", "Orion", WHEN)
    assert "sexta-feira, 2 de outubro" in spoken_fallback("data de hoje", "Orion", WHEN)
    amanha = spoken_fallback("que dia é amanhã", "Orion", WHEN)
    assert amanha.startswith("Amanhã é")
    assert "sábado, 3 de outubro" in amanha
    ontem = spoken_fallback("que dia foi ontem", "Orion", WHEN)
    assert ontem.startswith("Ontem foi")
    assert "quinta-feira, 1 de outubro" in ontem
    depois = spoken_fallback("que dia é depois de amanhã", "Orion", WHEN)
    assert depois.startswith("Depois de amanhã é")
    assert "domingo, 4 de outubro" in depois
    ante = spoken_fallback("que dia foi anteontem", "Orion", WHEN)
    assert ante.startswith("Anteontem foi")
    assert "quarta-feira, 30 de setembro" in ante
    assert spoken_fallback("que horas são amanhã", "Orion", WHEN).startswith("Entendido")
    assert spoken_fallback("", "Orion", WHEN).startswith("Pois não")
    assert spoken_fallback("bom dia", "Orion", WHEN) == "Bom dia, Senhor."
    assert spoken_fallback("boa tarde", "Orion", WHEN) == "Boa tarde, Senhor."
    assert spoken_fallback("boa noite", "Orion", WHEN) == "Boa noite, Senhor."
    assert spoken_fallback("obrigado", "Orion", WHEN) == "Disponha, Senhor."
    assert spoken_fallback("valeu", "Orion", WHEN) == "Disponha, Senhor."
    assert spoken_fallback("obrigada", "Orion", WHEN) == "Disponha, Senhor."
    assert spoken_fallback("bom dia para o projeto", "Orion", WHEN).startswith("Entendido")
    assert spoken_fallback("tudo bem", "Orion", WHEN) == "Estou pronto, Senhor."
    assert spoken_fallback("como está você", "Orion", WHEN) == "Estou pronto, Senhor."
    assert spoken_fallback("até logo", "Orion", WHEN) == "Até logo, Senhor."
    assert spoken_fallback("como está", "Orion", WHEN).startswith("Entendido")


def test_turn_without_wake_is_ignored():
    result = take_turn(_session(), "que horas são", 10.0, _reply)
    assert result.status == "ignored"
    assert result.reply == ""


def test_repeat_says_the_last_answer(tmp_path, monkeypatch):
    reply = make_reply_fn(
        Settings.from_env(
            env={
                "CLAUDE_VOICE_CODEX_CLI": "missing-codex",
                "CLAUDE_VOICE_CURSOR_CLI": "missing-cursor",
                "CLAUDE_VOICE_CLAUDE_CLI": "missing-claude",
                "OLLAMA_HOST": "",
                "CLAUDE_VOICE_OLLAMA_HOST": "",
                "CLAUDE_VOICE_REMINDERS": str(tmp_path / "n.json"),
            }
        ),
        get_persona("orion"),
        lambda: WHEN,
    )
    assert reply("repete", []) == "Não tenho o que repetir, Senhor."
    clock = reply("que horas são", [])
    heard = [("user", "que horas são"), ("assistant", clock)]
    assert reply("repete", heard) == clock
    assert reply("repita isso", heard) == clock
    assert reply("pode repetir", heard) == clock
    assert reply(
        "repete",
        [
            ("user", "que horas são"),
            ("assistant", clock),
            ("user", "liste os arquivos"),
            ("assistant", "ACAO: xdg-open 'https://exemplo'"),
        ],
    ) == clock
    assert reply("tempo", []) == "De qual lugar, Senhor."
    assert reply("repete", [("user", "tempo"), ("assistant", "De qual lugar, Senhor.")]) == (
        "De qual lugar, Senhor."
    )

    def fake_weather(place, _fetch, day="", field=""):
        return f"Em {place}, 19 graus, nublado, Senhor."

    monkeypatch.setattr("claude_agent_voice.house._weather", fake_weather)
    assert reply("recife", [("user", "repete"), ("assistant", "De qual lugar, Senhor.")]) == (
        "Em recife, 19 graus, nublado, Senhor."
    )


def test_undo_removes_only_a_note_just_saved(tmp_path):
    path = tmp_path / "n.json"
    path.write_text('[{"text": "entregar o projeto"}]', encoding="utf-8")
    reply = make_reply_fn(
        Settings.from_env(
            env={
                "CLAUDE_VOICE_CODEX_CLI": "missing-codex",
                "CLAUDE_VOICE_CURSOR_CLI": "missing-cursor",
                "CLAUDE_VOICE_CLAUDE_CLI": "missing-claude",
                "OLLAMA_HOST": "",
                "CLAUDE_VOICE_OLLAMA_HOST": "",
                "CLAUDE_VOICE_REMINDERS": str(path),
            }
        ),
        get_persona("orion"),
        lambda: WHEN,
    )
    clock = reply("que horas são", [])
    assert reply("desfaz", [("user", "que horas são"), ("assistant", clock)]) == (
        "Nada para desfazer, Senhor."
    )
    assert "entregar o projeto" in path.read_text(encoding="utf-8")
    assert reply("anote prova de desfazer", []) == "Anotado, Senhor."
    assert "prova de desfazer" in path.read_text(encoding="utf-8")
    assert reply(
        "desfaz",
        [("user", "anote prova de desfazer"), ("assistant", "Anotado, Senhor.")],
    ) == "Desfeito, Senhor. prova de desfazer."
    saved = path.read_text(encoding="utf-8")
    assert "prova de desfazer" not in saved
    assert "entregar o projeto" in saved


def test_spoken_name_when_asked():
    assert spoken_fallback("Qual seu nome?", "Orion", WHEN) == "O nome é Orion, Senhor."
    assert spoken_fallback("Quem é você?", "Orion", WHEN) == "O nome é Orion, Senhor."
    assert spoken_fallback("o que é você", "Orion", WHEN) == "O nome é Orion, Senhor."


def test_typed_name_is_answered_and_opens_the_window():
    session = _session()
    hud = VoiceHud(
        session=session,
        reply_fn=_reply,
        synth_fn=lambda text: (b"\x00\x00" * 4, 24000),
        transcribe_fn=lambda pcm, rate: "que horas são",
        clock=lambda: 1.0,
    )
    named = hud.handle(text="Qual seu nome?", typed=True)
    assert named["status"] == "replied"
    assert named["reply"] == "O nome é Orion, Senhor."
    assert named["audio_b64"]
    follow = take_turn(session, "que horas são", 5.0, _reply)
    assert follow.status == "replied"
    assert "15 horas" in follow.reply


def test_microphone_without_wake_stays_ignored():
    hud = VoiceHud(
        session=_session(),
        reply_fn=_reply,
        synth_fn=lambda text: (b"\x00\x00" * 4, 24000),
        transcribe_fn=lambda pcm, rate: "que horas são",
        clock=lambda: 1.0,
    )
    mic = hud.handle(pcm=b"\x00\x00", sample_rate=16000)
    assert mic["status"] == "ignored"
    assert mic["reply"] == ""


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
    assert 'id="brain"' in page
    assert 'id="permit"' in page
    assert "permitir" in page
    assert "recusar" in page
    assert "reator" not in page.lower()
    assert "iron" not in page.lower()
    assert "Glorious" not in page
    assert "Betelgeuse" not in page
    assert "Meissa" not in page
    assert "M20 6 L7 18" not in page
    assert "M22.5 3.4C8.8 7.4 7.4 12.2 9.4 16" in page
    assert "constelação" in page
    assert "Notas" in page
    assert "Sistemas" in page
    assert 'id="note"' in page
    assert 'data-brain="codex"' in page
    assert 'data-brain="cursor"' in page
    assert 'data-brain="claude"' in page
    assert "buscar nota" in page
    assert "quietLink ? 0.16 : 1" in page
    assert "[8, 10]" in page
    assert 'id="sky"' in page
    assert 'id="brain-codex"' in page
    assert 'id="brain-cursor"' in page
    assert 'id="brain-claude"' in page


def test_turn_tells_the_sky_which_notes_match(tmp_path):
    notes = tmp_path / "n.json"
    notes.write_text(
        json.dumps(
            [
                {"text": "entregar o projeto na sexta"},
                {"text": "constelação de lembretes"},
            ]
        ),
        encoding="utf-8",
    )
    reply = make_reply_fn(
        Settings.from_env(
            env={
                "CLAUDE_VOICE_CODEX_CLI": "missing-codex",
                "CLAUDE_VOICE_CURSOR_CLI": "missing-cursor",
                "CLAUDE_VOICE_CLAUDE_CLI": "missing-claude",
                "OLLAMA_HOST": "",
                "CLAUDE_VOICE_OLLAMA_HOST": "",
                "CLAUDE_VOICE_REMINDERS": str(notes),
            }
        ),
        get_persona("orion"),
        lambda: WHEN,
    )
    hud = VoiceHud(
        session=_session(),
        reply_fn=reply,
        synth_fn=lambda text: (b"\x00\x00", 24000),
        transcribe_fn=lambda pcm, rate: "",
        clock=lambda: 1.0,
        reminders_path=notes,
    )
    found = hud.handle(text="Orion, buscar nota projeto", typed=True)
    assert found["note_query"] == "projeto"
    assert "entregar o projeto" in found["reply"]
    clock = hud.handle(text="que horas são", typed=True)
    assert "horas" in clock["reply"]
    assert clock["note_query"] == ""
    assert hud.handle(text="buscar nota", typed=True)["note_query"] == ""
    follow = hud.handle(text="lembretes", typed=True)
    assert follow["note_query"] == "lembretes"
    assert "constelação" in follow["reply"]
    listed = hud.handle(text="liste os arquivos", typed=True)
    assert listed["status"] == "permit"
    assert listed["note_query"] == ""


def test_status_notes_count_follows_the_file(tmp_path):
    path = tmp_path / "n.json"
    path.write_text("[]", encoding="utf-8")
    hud = VoiceHud(
        session=_session(),
        reply_fn=_reply,
        synth_fn=lambda text: (b"\x00\x00", 24000),
        transcribe_fn=lambda pcm, rate: "",
        clock=lambda: 0.0,
        reminders_path=path,
    )
    assert hud.status_payload()["notes"] == 0
    path.write_text(json.dumps([{"text": "comprar pao"}]), encoding="utf-8")
    assert hud.status_payload()["notes"] == 1


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

        named = post("/api/turn", {"text": "Qual seu nome?"})
        assert named["status"] == "replied"
        assert named["reply"] == "O nome é Orion, Senhor."
        assert named["audio_b64"]

        typed = post("/api/turn", {"text": "somente isso"})
        assert typed["status"] == "replied"
        assert typed["audio_b64"]

        heard = post("/api/turn", {"pcm_b64": "AAAA", "sample_rate": 16000})
        assert heard["heard"] == "Orion ola"
        assert heard["status"] == "replied"
    finally:
        httpd.shutdown()
