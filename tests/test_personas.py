"""Contrato do registry de personas (Lilith + Orion) e do seletor."""

import pytest

from claude_agent_voice.personas import DEFAULT_PERSONA, PERSONAS, Persona, get_persona


def test_registry_has_lilith_and_orion():
    assert set(PERSONAS) >= {"lilith", "orion"}
    assert isinstance(PERSONAS["lilith"], Persona)
    assert isinstance(PERSONAS["orion"], Persona)


def test_orion_preset_is_kokoro_masculino_ptbr():
    g = PERSONAS["orion"]
    assert g.name == "Orion"
    assert g.gender == "masculino"
    assert g.tts_engine == "kokoro"
    assert g.voice == "bm_george*0.7+pm_santa*0.3"
    assert g.speech_rate == 0.84
    assert "orion" in g.wake_words
    assert g.form_of_address == "Senhor"


def test_lilith_preset_is_kokoro_feminino():
    li = PERSONAS["lilith"]
    assert li.name == "Lilith"
    assert li.gender == "feminino"
    assert li.tts_engine == "kokoro"
    assert li.voice == "pf_dora"
    assert "lilith" in li.wake_words
    assert li.form_of_address == "Senhor"


def test_orion_prompt_masculino_senhor_orion():
    p = PERSONAS["orion"].system_prompt()
    assert "Orion" in p
    assert "Senhor" in p
    assert "um assistente" in p  # gênero masculino
    assert "uma assistente" not in p


def test_lilith_prompt_feminino_senhor_lilith():
    p = PERSONAS["lilith"].system_prompt()
    assert "Lilith" in p
    assert "Senhor" in p
    assert "uma assistente" in p  # gênero feminino


def test_default_persona_is_orion():
    assert DEFAULT_PERSONA == "orion"
    assert get_persona(None) is PERSONAS["orion"]
    assert get_persona("") is PERSONAS["orion"]


def test_get_persona_is_case_insensitive():
    assert get_persona("ORION") is PERSONAS["orion"]
    assert get_persona(" Lilith ") is PERSONAS["lilith"]


def test_unknown_persona_raises_clear_error():
    with pytest.raises(ValueError) as ei:
        get_persona("hal9000")
    assert "hal9000" in str(ei.value)


def test_namespaced_voice_override():
    # override de voz é por-persona (namespaced), nunca knob global
    li = get_persona("lilith", env={"LILITH_VOICE": "pf_alex"})
    assert li.voice == "pf_alex"
    g = get_persona("orion", env={"ORION_VOICE": "pt_BR-edresson-low"})
    assert g.voice == "pt_BR-edresson-low"
    # override da OUTRA persona não vaza
    li2 = get_persona("lilith", env={"ORION_VOICE": "x"})
    assert li2.voice == "pf_dora"
