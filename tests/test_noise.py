"""Filtro de alucinação/ruído: dropa transcrições degeneradas antes do cérebro.

Whisper alucina em música/ruído gerando frases curtas e repetitivas
("o que é o que é", "o chá é o que é o chá"). ``is_noise_transcript`` é pura e
decide se um transcript é lixo que NÃO deve virar turno.
"""

from claude_agent_voice.noise import is_noise_transcript


def test_empty_or_blank_is_noise():
    assert is_noise_transcript("") is True
    assert is_noise_transcript("   ") is True


def test_single_short_token_is_noise():
    # ruído vira uma sílaba solta
    assert is_noise_transcript("é") is True
    assert is_noise_transcript("ah") is True
    assert is_noise_transcript("o") is True


def test_repetitive_hallucination_is_noise():
    # padrão clássico de alucinação do whisper em ruído/música
    assert is_noise_transcript("o que é o que é o que é") is True
    assert is_noise_transcript("o chá é o que é o chá") is True
    assert is_noise_transcript("o mar é o que é o que é") is True


def test_same_word_repeated_is_noise():
    assert is_noise_transcript("obrigado obrigado obrigado") is True


def test_real_command_is_not_noise():
    assert is_noise_transcript("que horas são") is False
    assert is_noise_transcript("Lilith abre o navegador pra mim") is False
    assert is_noise_transcript("me conta uma piada") is False


def test_short_real_phrase_is_not_noise():
    # duas palavras distintas e com conteúdo não é ruído
    assert is_noise_transcript("bom dia") is False
    assert is_noise_transcript("obrigado Lilith") is False


def test_accents_and_case_do_not_fool_repetition():
    assert is_noise_transcript("Chá CHÁ chá") is True
