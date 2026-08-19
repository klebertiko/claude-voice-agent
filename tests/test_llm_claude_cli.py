"""Render do prompt pro `claude -p`: separa system, monta roteiro Usuário/Lilith."""

from claude_agent_voice.llm_claude_cli import _extract_turns, render_prompt


def test_system_is_separated_from_conversation():
    prompt, system = render_prompt(
        [("system", "Você é a Lilith."), ("user", "que horas são")]
    )
    assert system == "Você é a Lilith."
    assert "Lilith: Você é a Lilith" not in prompt  # system não entra no roteiro
    assert prompt == "Usuário: que horas são\nLilith:"


def test_multiturn_transcript_order():
    prompt, _ = render_prompt(
        [
            ("user", "oi"),
            ("assistant", "Olá, Kleber."),
            ("user", "tudo bem?"),
        ]
    )
    assert prompt == "Usuário: oi\nLilith: Olá, Kleber.\nUsuário: tudo bem?\nLilith:"


def test_empty_and_whitespace_turns_dropped():
    prompt, system = render_prompt(
        [("system", "  "), ("user", ""), ("user", "  fala  ")]
    )
    assert system == ""
    assert prompt == "Usuário: fala\nLilith:"


def test_multiple_system_messages_joined():
    _, system = render_prompt([("system", "A"), ("system", "B")])
    assert system == "A\n\nB"


def test_assistant_label_defaults_to_lilith():
    prompt, _ = render_prompt([("user", "oi")])
    assert prompt == "Usuário: oi\nLilith:"


def test_assistant_label_parametrized_for_gambit():
    prompt, _ = render_prompt(
        [("user", "oi"), ("assistant", "Pois não, Senhor.")],
        assistant_label="Gambit",
    )
    assert prompt == "Usuário: oi\nGambit: Pois não, Senhor.\nGambit:"
    assert "Lilith" not in prompt


class _Msg:
    def __init__(self, role, text):
        self.role = role
        self.text_content = text


class _Ctx:
    def __init__(self, items):
        self.items = items


def test_extract_turns_reads_items():
    ctx = _Ctx([_Msg("system", "persona"), _Msg("user", "oi")])
    assert _extract_turns(ctx) == [("system", "persona"), ("user", "oi")]
