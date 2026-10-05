"""Clima, notícias, busca, lembrete e WhatsApp, sem rede de verdade."""

from datetime import datetime
from zoneinfo import ZoneInfo

from claude_agent_voice.house import house_reply

WHEN = datetime(2026, 10, 5, 15, 5, tzinfo=ZoneInfo("America/Sao_Paulo"))


def _reply(text, fetch, path):
    return house_reply(text, WHEN, reminders_path=path, fetch=fetch)


def test_weather_defaults_to_sao_paulo(tmp_path):
    def fetch(url):
        assert "forecast" in url
        return '{"current":{"temperature_2m":23.4,"weather_code":1}}'

    assert _reply("que tempo faz", fetch, tmp_path / "n.json") == (
        "Em São Paulo, 23 graus, quase limpo, Senhor."
    )
    assert _reply("qual o tempo", fetch, tmp_path / "n.json") == (
        "Em São Paulo, 23 graus, quase limpo, Senhor."
    )


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


def test_news_reads_two_titles(tmp_path):
    rss = (
        '<?xml version="1.0"?><rss><channel><title>Google News</title>'
        "<item><title>Alpha sobe</title></item>"
        "<item><title>Beta cai</title></item></channel></rss>"
    )

    def fetch(_url):
        return rss

    assert _reply("quais as noticias", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )


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


def test_network_failure_is_spoken(tmp_path):
    def fetch(_url):
        raise TimeoutError("off")

    assert _reply("noticias de hoje", fetch, tmp_path / "n.json") == (
        "Não alcancei isso agora, Senhor."
    )
