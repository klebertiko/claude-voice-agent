"""As assinaturas respondem na ordem Codex, Cursor, Claude, e sem escrever disco."""

from claude_agent_voice.brains import probe_subscriptions, subscription_reply
from claude_agent_voice.personas import get_persona
from claude_agent_voice.settings import Settings


def _bin(path, body: str):
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)


def _settings(tmp_path, **extra):
    env = {
        "CLAUDE_VOICE_CODEX_CLI": str(tmp_path / "missing-codex"),
        "CLAUDE_VOICE_CURSOR_CLI": str(tmp_path / "missing-cursor"),
        "CLAUDE_VOICE_CLAUDE_CLI": str(tmp_path / "missing-claude"),
    }
    env.update(extra)
    return Settings.from_env(env=env)


def test_absent_clis_are_down(tmp_path):
    rows = {row["id"]: row["up"] for row in probe_subscriptions(_settings(tmp_path))}
    assert rows == {"codex": False, "cursor": False, "claude": False}


def test_codex_answers_read_only_and_beats_claude(tmp_path):
    args = tmp_path / "codex-args"
    _bin(
        tmp_path / "codex",
        "#!/usr/bin/env python3\n"
        "import pathlib, sys\n"
        f"pathlib.Path({str(args)!r}).write_text('\\n'.join(sys.argv[1:]))\n"
        "print('Pelo Codex, Senhor.')\n",
    )
    _bin(tmp_path / "claude", "#!/bin/sh\necho 'Pelo Claude, Senhor.'\n")
    settings = _settings(
        tmp_path,
        CLAUDE_VOICE_CODEX_CLI=str(tmp_path / "codex"),
        CLAUDE_VOICE_CLAUDE_CLI=str(tmp_path / "claude"),
    )
    reply = subscription_reply(settings, get_persona("orion"), [], "conte uma coisa")
    assert reply == "Pelo Codex, Senhor."
    text = args.read_text(encoding="utf-8")
    assert "--sandbox" in text
    assert "read-only" in text
    assert "--force" not in text
    assert "--ephemeral" in text


def test_cursor_prints_without_force(tmp_path):
    args = tmp_path / "cursor-args"
    _bin(
        tmp_path / "cursor-agent",
        "#!/usr/bin/env python3\n"
        "import pathlib, sys\n"
        f"pathlib.Path({str(args)!r}).write_text('\\n'.join(sys.argv[1:]))\n"
        "print('Pelo Cursor, Senhor.')\n",
    )
    settings = _settings(tmp_path, CLAUDE_VOICE_CURSOR_CLI=str(tmp_path / "cursor-agent"))
    reply = subscription_reply(settings, get_persona("orion"), [], "conte uma coisa")
    assert reply == "Pelo Cursor, Senhor."
    text = args.read_text(encoding="utf-8")
    assert "-p" in text.splitlines()
    assert "--mode" in text.splitlines()
    assert "ask" in text.splitlines()
    assert "--force" not in text


def test_failed_codex_falls_through_to_claude(tmp_path):
    _bin(tmp_path / "codex", "#!/bin/sh\nexit 1\n")
    _bin(tmp_path / "claude", "#!/bin/sh\necho 'Pelo Claude, Senhor.'\n")
    settings = _settings(
        tmp_path,
        CLAUDE_VOICE_CODEX_CLI=str(tmp_path / "codex"),
        CLAUDE_VOICE_CLAUDE_CLI=str(tmp_path / "claude"),
    )
    assert (
        subscription_reply(settings, get_persona("orion"), [], "conte uma coisa")
        == "Pelo Claude, Senhor."
    )


def test_prefer_uses_only_that_brain(tmp_path):
    _bin(tmp_path / "codex", "#!/bin/sh\necho 'Pelo Codex, Senhor.'\n")
    _bin(tmp_path / "claude", "#!/bin/sh\necho 'Pelo Claude, Senhor.'\n")
    settings = _settings(
        tmp_path,
        CLAUDE_VOICE_CODEX_CLI=str(tmp_path / "codex"),
        CLAUDE_VOICE_CLAUDE_CLI=str(tmp_path / "claude"),
    )
    reply = subscription_reply(
        settings, get_persona("orion"), [], "conte uma coisa", prefer="claude"
    )
    assert reply == "Pelo Claude, Senhor."
    assert subscription_reply(
        settings, get_persona("orion"), [], "conte uma coisa", prefer="cursor"
    ) is None


def test_unlogged_brain_asks_for_login(tmp_path):
    from datetime import datetime
    from zoneinfo import ZoneInfo

    from claude_agent_voice.hud import make_reply_fn

    _bin(tmp_path / "codex", "#!/bin/sh\necho 'Not logged in'\nexit 1\n")
    settings = _settings(tmp_path, CLAUDE_VOICE_CODEX_CLI=str(tmp_path / "codex"))
    reply = make_reply_fn(
        settings,
        get_persona("orion"),
        lambda: datetime(2026, 10, 5, 15, 5, tzinfo=ZoneInfo("America/Sao_Paulo")),
        {"id": "codex"},
    )
    assert reply("conte uma coisa", []) == "Codex precisa de login, Senhor."


def test_choice_does_not_fall_through(tmp_path):
    from datetime import datetime
    from zoneinfo import ZoneInfo

    from claude_agent_voice.hud import make_reply_fn

    _bin(tmp_path / "claude", "#!/bin/sh\necho 'Pelo Claude, Senhor.'\n")
    settings = _settings(tmp_path, CLAUDE_VOICE_CLAUDE_CLI=str(tmp_path / "claude"))
    choice = {"id": "codex"}
    reply = make_reply_fn(
        settings,
        get_persona("orion"),
        lambda: datetime(2026, 10, 5, 15, 5, tzinfo=ZoneInfo("America/Sao_Paulo")),
        choice,
    )
    assert reply("conte uma coisa", []) == "Codex não está neste computador, Senhor."
    choice["id"] = "claude"
    assert reply("conte uma coisa", []) == "Pelo Claude, Senhor."
    assert reply("qual o ritmo", []) == "O ritmo é 1.2, Senhor."


def test_login_offer_is_reused_and_shows_the_code(tmp_path):
    from claude_agent_voice.brains import begin_login, login_snapshot
    from claude_agent_voice.brains import _logins, _stop_login
    from claude_agent_voice.hud import HudSession
    from claude_agent_voice.wake import WakeGate
    from claude_agent_voice.web import VoiceHud

    count = tmp_path / "starts"
    count.write_text("0", encoding="utf-8")
    _bin(
        tmp_path / "codex",
        "#!/usr/bin/env python3\n"
        "import pathlib, sys, time\n"
        f"count = pathlib.Path({str(count)!r})\n"
        "args = sys.argv[1:]\n"
        "if args[:2] == ['login', 'status']:\n"
        "    print('Not logged in')\n"
        "    raise SystemExit(1)\n"
        "count.write_text(str(int(count.read_text() or '0') + 1))\n"
        "print('https://auth.example/codex/device', flush=True)\n"
        "print('one-time code ABCD-EF12', flush=True)\n"
        "time.sleep(30)\n",
    )
    settings = _settings(tmp_path, CLAUDE_VOICE_CODEX_CLI=str(tmp_path / "codex"))
    persona = get_persona("orion")
    hud = VoiceHud(
        session=HudSession(
            persona=persona,
            gate=WakeGate(wake_words=persona.wake_words, window_s=30),
        ),
        reply_fn=lambda cleaned, history: "não",
        synth_fn=lambda text: (b"\x00\x00" * 4, 24000),
        transcribe_fn=lambda pcm, rate: "",
        clock=lambda: 1.0,
        probe_fn=lambda: {"up": False, "models": []},
    )
    hud.settings = settings
    hud.choice = {"id": ""}
    try:
        first = begin_login("codex", str(tmp_path / "codex"))
        second = begin_login("codex", str(tmp_path / "codex"))
        assert first["url"] == "https://auth.example/codex/device"
        assert first["code"] == "ABCD-EF12"
        assert second["url"] == first["url"]
        assert count.read_text(encoding="utf-8") == "1"
        opened = hud.use("codex")
        assert opened["reply"] == "Codex precisa de login, Senhor."
        assert opened["login_url"] == "https://auth.example/codex/device"
        assert opened["login_code"] == "ABCD-EF12"
        assert login_snapshot()["codex"]["code"] == "ABCD-EF12"
        assert count.read_text(encoding="utf-8") == "1"
    finally:
        slot = _logins.get("codex")
        if slot:
            _stop_login(slot)


def test_claude_login_accepts_a_pasted_code(tmp_path):
    from claude_agent_voice.brains import begin_login, submit_login_code
    from claude_agent_voice.brains import _logins, _stop_login

    saved = tmp_path / "pasted"
    _bin(
        tmp_path / "claude",
        "#!/usr/bin/env python3\n"
        "import pathlib, sys\n"
        "args = sys.argv[1:]\n"
        "if args[:2] == ['auth', 'status']:\n"
        "    print('{\"loggedIn\": false}')\n"
        "    raise SystemExit(1)\n"
        "print('https://claude.example/oauth', flush=True)\n"
        "sys.stdout.write('Paste code here if prompted > ')\n"
        "sys.stdout.flush()\n"
        f"pathlib.Path({str(saved)!r}).write_text(sys.stdin.readline().strip())\n",
    )
    try:
        offer = begin_login("claude", str(tmp_path / "claude"))
        assert offer["url"] == "https://claude.example/oauth"
        assert offer["needs_code"] is True
        assert submit_login_code("claude", "abcDEF1234567890xyz_")
        for _ in range(50):
            if saved.exists():
                break
            import time
            time.sleep(0.05)
        assert saved.read_text(encoding="utf-8") == "abcDEF1234567890xyz_"
    finally:
        slot = _logins.get("claude")
        if slot:
            _stop_login(slot)


def test_reply_fn_uses_the_subscription_before_the_fallback(tmp_path):
    from datetime import datetime
    from zoneinfo import ZoneInfo

    from claude_agent_voice.hud import make_reply_fn

    _bin(tmp_path / "claude", "#!/bin/sh\necho 'Pelo Claude, Senhor.'\n")
    settings = _settings(tmp_path, CLAUDE_VOICE_CLAUDE_CLI=str(tmp_path / "claude"))
    reply = make_reply_fn(
        settings,
        get_persona("orion"),
        lambda: datetime(2026, 10, 5, 15, 5, tzinfo=ZoneInfo("America/Sao_Paulo")),
    )
    assert reply("conte uma coisa", []) == "Pelo Claude, Senhor."
    assert "15 horas" in reply("que horas são", [])
