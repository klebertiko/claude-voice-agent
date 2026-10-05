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
    assert "1.08" in reply("qual o ritmo", [])


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
