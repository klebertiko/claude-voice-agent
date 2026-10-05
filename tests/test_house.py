"""Clima, notícias, busca, lembrete e WhatsApp, sem rede de verdade."""

from datetime import datetime
from zoneinfo import ZoneInfo

from claude_agent_voice.house import house_reply

WHEN = datetime(2026, 10, 5, 15, 5, tzinfo=ZoneInfo("America/Sao_Paulo"))


def _reply(text, fetch, path):
    return house_reply(text, WHEN, reminders_path=path, fetch=fetch)


def test_weather_asks_for_the_place(tmp_path):
    def fetch(_url):
        raise AssertionError("sem lugar, não busca o clima")

    assert _reply("que tempo faz", fetch, tmp_path / "n.json") == "De qual lugar, Senhor."
    assert _reply("qual o tempo", fetch, tmp_path / "n.json") == "De qual lugar, Senhor."


def test_weather_names_the_city(tmp_path):
    def fetch(url):
        if "geocoding" in url:
            return '{"results":[{"latitude":-22.9,"longitude":-43.2,"name":"Rio de Janeiro"}]}'
        return '{"current":{"temperature_2m":28.2,"weather_code":95}}'

    assert _reply("tempo em rio", fetch, tmp_path / "n.json") == (
        "Em Rio de Janeiro, 28 graus, trovoada, Senhor."
    )


def test_unrelated_tempo_is_not_weather(tmp_path):
    def fetch(_url):
        raise AssertionError("não devia buscar o clima")

    assert _reply("faz tempo que não falo", fetch, tmp_path / "n.json") is None


def test_news_asks_then_reads_the_topic(tmp_path):
    rss = (
        '<?xml version="1.0"?><rss><channel><title>economia - Google Notícias</title>'
        "<item><title>Alpha sobe</title></item>"
        "<item><title>Beta cai</title></item></channel></rss>"
    )
    seen = []

    def fetch(url):
        seen.append(url)
        return rss

    assert _reply("quais as noticias", fetch, tmp_path / "n.json") == "Sobre o que, Senhor."
    assert seen == []
    assert _reply("noticias sobre economia", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert "economia" in seen[0]


def test_search_speaks_the_abstract(tmp_path):
    def fetch(_url):
        return '{"AbstractText":"O café é uma bebida. O resto fica de fora."}'

    assert _reply("pesquise café", fetch, tmp_path / "n.json") == (
        "O café é uma bebida, Senhor."
    )


def test_search_without_abstract_asks_permission(tmp_path):
    def fetch(_url):
        return '{"AbstractText":""}'

    reply = _reply("busque reator arc", fetch, tmp_path / "n.json")
    assert reply.startswith("ACAO: xdg-open 'https://duckduckgo.com/?q=")


def test_reminder_roundtrip(tmp_path):
    path = tmp_path / "notes.json"

    def fetch(_url):
        raise AssertionError("lembrete não usa rede")

    assert _reply("anote comprar café", fetch, path) == "Anotado, Senhor."
    assert _reply("me lembre de voz do orion", fetch, path) == "Anotado, Senhor."
    listed = _reply("meus lembretes", fetch, path)
    assert "comprar café" in listed
    assert "voz do orion" in listed


def test_note_search_stays_in_the_vault(tmp_path):
    path = tmp_path / "notes.json"
    path.write_text(
        '[{"text": "entregar o projeto na sexta", "at": "a"}]',
        encoding="utf-8",
    )

    def fetch(_url):
        raise AssertionError("busca de nota não abre a web")

    found = _reply("buscar nota projeto", fetch, path)
    assert found == "Nas notas, Senhor. entregar o projeto na sexta."
    assert _reply("buscar nota marte", fetch, path) == "Não há nota com isso, Senhor."


def test_camera_and_image_are_refused(tmp_path):
    def fetch(_url):
        raise AssertionError("recusa não usa rede")

    path = tmp_path / "n.json"
    assert _reply("ligue a câmera", fetch, path) == "Não uso câmera, Senhor."
    assert _reply("gere uma imagem do reator", fetch, path) == (
        "Ainda não gero imagem aqui, Senhor."
    )


def test_whatsapp_is_a_link_with_permission(tmp_path):
    def fetch(_url):
        raise AssertionError("whatsapp não usa rede")

    path = tmp_path / "n.json"
    reply = _reply("mande whatsapp para 5511999998888 dizendo cheguei", fetch, path)
    assert reply.startswith("ACAO: xdg-open 'https://wa.me/5511999998888?text=cheguei'")
    assert _reply("mande um whatsapp", fetch, path) == "Diga o número, Senhor."


def test_the_next_lines_build_the_whatsapp(tmp_path):
    from claude_agent_voice.hud import make_reply_fn
    from claude_agent_voice.personas import get_persona
    from claude_agent_voice.settings import Settings

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
    assert reply("mande um whatsapp", []) == "Diga o número, Senhor."
    assert reply("5511999998888", []) == "O que devo escrever, Senhor?"
    assert reply("cheguei", []).startswith(
        "ACAO: xdg-open 'https://wa.me/5511999998888?text=cheguei'"
    )
    assert reply("mande whatsapp para 5511888777666", []) == "O que devo escrever, Senhor?"
    assert "5511888777666" in reply("estou na porta", [])
    assert reply("mande um whatsapp", []) == "Diga o número, Senhor."
    assert "horas" in reply("que horas são", [])
    assert not reply("5511999998888", []).startswith("ACAO:")


def test_the_next_line_answers_the_question(monkeypatch):
    from claude_agent_voice.hud import make_reply_fn
    from claude_agent_voice.personas import get_persona
    from claude_agent_voice.settings import Settings

    monkeypatch.setattr(
        "claude_agent_voice.house._weather",
        lambda place, fetch: f"Em {place}, 19 graus, nublado, Senhor.",
    )
    reply = make_reply_fn(
        Settings.from_env(
            env={
                "CLAUDE_VOICE_CODEX_CLI": "missing-codex",
                "CLAUDE_VOICE_CURSOR_CLI": "missing-cursor",
                "CLAUDE_VOICE_CLAUDE_CLI": "missing-claude",
                "OLLAMA_HOST": "",
                "CLAUDE_VOICE_OLLAMA_HOST": "",
            }
        ),
        get_persona("orion"),
        lambda: WHEN,
    )
    assert reply("qual o tempo", []) == "De qual lugar, Senhor."
    assert "15 horas" in reply("que horas são", [])
    assert reply("qual o tempo", []) == "De qual lugar, Senhor."
    assert reply("Campinas", []) == "Em Campinas, 19 graus, nublado, Senhor."


def test_the_next_line_is_the_note(tmp_path):
    from claude_agent_voice.hud import make_reply_fn
    from claude_agent_voice.personas import get_persona
    from claude_agent_voice.settings import Settings

    notes = tmp_path / "n.json"
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
    assert reply("anote", []) == "O que devo anotar, Senhor?"
    assert reply("comprar café", []) == "Anotado, Senhor."
    assert reply("buscar nota", []) == "O que devo buscar nas notas, Senhor?"
    assert "comprar café" in reply("café", [])


def test_network_failure_is_spoken(tmp_path):
    def fetch(_url):
        raise TimeoutError("off")

    assert _reply("noticias de hoje", fetch, tmp_path / "n.json") == (
        "Não alcancei isso agora, Senhor."
    )
