"""Contrato do WakeGate: quando a Lilith responde e o que ela 'ouve' de comando."""

from claude_agent_voice.personas import get_persona
from claude_agent_voice.wake import WakeGate, _normalize


def test_gambit_wake_activates_with_its_own_words():
    gate = WakeGate(wake_words=get_persona("gambit").wake_words, window_s=30.0)
    should, text = gate.process("Gambit que horas são", now=100.0)
    assert should is True
    assert text == "que horas sao"


def test_gambit_gate_ignores_other_personas_wake():
    # a wake-word da Lilith NÃO deve abrir a janela do Gambit
    gate = WakeGate(wake_words=get_persona("gambit").wake_words, window_s=30.0)
    should, _ = gate.process("Lilith oi", now=100.0)
    assert should is False


def test_normalize_strips_accents_and_punct():
    assert _normalize("Lilith, tudo bem?") == "lilith  tudo bem "


def test_ignores_speech_without_wake_word_when_cold():
    gate = WakeGate(window_s=30.0)
    should, text = gate.process("que horas são", now=100.0)
    assert should is False
    assert text == ""


def test_wake_word_activates_and_strips_name():
    gate = WakeGate(window_s=30.0)
    should, text = gate.process("Lilith que horas são", now=100.0)
    assert should is True
    assert text == "que horas sao"


def test_bare_name_answers_with_empty_command():
    gate = WakeGate(window_s=30.0)
    should, text = gate.process("Lilith?", now=100.0)
    assert should is True
    assert text == ""


def test_window_keeps_conversation_open_without_repeating_name():
    gate = WakeGate(window_s=30.0)
    gate.process("Lilith oi", now=100.0)
    # 10s depois, sem repetir o nome, ela ainda responde
    should, text = gate.process("e o clima amanha", now=110.0)
    assert should is True
    assert text == "e o clima amanha"


def test_window_expires_after_silence():
    gate = WakeGate(window_s=30.0)
    gate.process("Lilith oi", now=100.0)
    should, _ = gate.process("alguem ai", now=200.0)  # 100s depois: janela fechou
    assert should is False


def test_wake_word_mid_sentence_is_removed():
    gate = WakeGate(window_s=30.0)
    should, text = gate.process("ei Lilith toca musica", now=5.0)
    assert should is True
    assert text == "ei toca musica"


def test_close_ends_window_immediately():
    gate = WakeGate(window_s=30.0)
    gate.process("Lilith oi", now=100.0)
    gate.close()
    should, _ = gate.process("continua", now=101.0)
    assert should is False


def test_within_window_name_still_stripped_if_leading():
    gate = WakeGate(window_s=30.0)
    gate.process("Lilith oi", now=100.0)
    should, text = gate.process("Lilith obrigado", now=105.0)
    assert should is True
    assert text == "obrigado"
