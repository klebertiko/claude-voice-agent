"""strip_for_speech: tira emoji/markdown antes do TTS."""

from claude_agent_voice.speech import strip_for_speech


def test_removes_emoji():
    assert strip_for_speech("Oi, Kleber 👋") == "Oi, Kleber"


def test_removes_markdown_marks():
    assert (
        strip_for_speech("Isso é **importante** e `código`")
        == "Isso é importante e código"
    )


def test_collapses_whitespace():
    assert strip_for_speech("a    b\n\n\nc") == "a b\nc"


def test_plain_text_unchanged():
    assert strip_for_speech("Tudo certo por aqui.") == "Tudo certo por aqui."


def test_strips_heading_and_quote_marks():
    assert strip_for_speech("# Título\n> citação") == "Título\ncitação"
