"""Contrato do registry de personas (Lilith + Gambit) e do seletor."""

import pytest

from claude_agent_voice.personas import DEFAULT_PERSONA, PERSONAS, Persona, get_persona


def test_registry_has_lilith_and_gambit():
    assert set(PERSONAS) >= {"lilith", "gambit"}
    assert isinstance(PERSONAS["lilith"], Persona)
    assert isinstance(PERSONAS["gambit"], Persona)


def test_gambit_preset_is_piper_masculino():
    g = PERSONAS["gambit"]
    assert g.name == "Gambit"
    assert g.gender == "masculino"
    assert g.tts_engine == "piper"
    assert g.voice == "pt_BR-faber-medium"
    assert "gambit" in g.wake_words
    assert g.form_of_address == "Senhor"


def test_lilith_preset_is_kokoro_feminino():
    li = PERSONAS["lilith"]
    assert li.name == "Lilith"
    assert li.gender == "feminino"
    assert li.tts_engine == "kokoro"
    assert li.voice == "pf_dora"
    assert "lilith" in li.wake_words
    assert li.form_of_address == "Senhor"


def test_gambit_prompt_masculino_senhor_gambit():
    p = PERSONAS["gambit"].system_prompt()
    assert "Gambit" in p
    assert "Senhor" in p
    assert "um assistente" in p  # gênero masculino
    assert "uma assistente" not in p


def test_lilith_prompt_feminino_senhor_lilith():
    p = PERSONAS["lilith"].system_prompt()
    assert "Lilith" in p
    assert "Senhor" in p
    assert "uma assistente" in p  # gênero feminino


def test_default_persona_is_gambit():
    assert DEFAULT_PERSONA == "gambit"
    assert get_persona(None) is PERSONAS["gambit"]
    assert get_persona("") is PERSONAS["gambit"]


def test_get_persona_is_case_insensitive():
    assert get_persona("GAMBIT") is PERSONAS["gambit"]
    assert get_persona(" Lilith ") is PERSONAS["lilith"]


def test_unknown_persona_raises_clear_error():
    with pytest.raises(ValueError) as ei:
        get_persona("hal9000")
    assert "hal9000" in str(ei.value)


def test_namespaced_voice_override():
    # override de voz é por-persona (namespaced), nunca knob global
    li = get_persona("lilith", env={"LILITH_VOICE": "pf_alex"})
    assert li.voice == "pf_alex"
    g = get_persona("gambit", env={"GAMBIT_VOICE": "pt_BR-edresson-low"})
    assert g.voice == "pt_BR-edresson-low"
    # override da OUTRA persona não vaza
    li2 = get_persona("lilith", env={"GAMBIT_VOICE": "x"})
    assert li2.voice == "pf_dora"
