"""O céu só contém notas de verdade, ligadas por palavra compartilhada."""

import json

from claude_agent_voice.sky import memory_sky


def test_missing_file_is_an_empty_sky(tmp_path):
    assert memory_sky(tmp_path / "ausente.json") == {"stars": [], "links": []}


def test_shared_word_draws_a_constellation(tmp_path):
    path = tmp_path / "notes.json"
    path.write_text(
        json.dumps(
            [
                {"text": "voz do reator", "at": "2026-10-05T15:00"},
                {"text": "reator em são paulo", "at": "2026-10-05T15:01"},
                {"text": "comprar pão", "at": "2026-10-05T15:02"},
            ]
        ),
        encoding="utf-8",
    )
    sky = memory_sky(path)
    assert [star["text"] for star in sky["stars"]] == [
        "voz do reator",
        "reator em são paulo",
        "comprar pão",
    ]
    assert sky["links"] == [{"a": "n0", "b": "n1"}]


def test_stopwords_do_not_link(tmp_path):
    path = tmp_path / "notes.json"
    path.write_text(
        json.dumps(
            [
                {"text": "para o dia", "at": "a"},
                {"text": "para a casa", "at": "b"},
            ]
        ),
        encoding="utf-8",
    )
    assert memory_sky(path)["links"] == []
