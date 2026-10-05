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

    path = tmp_path / "n.json"
    assert _reply("que tempo faz", fetch, path) == "De qual lugar, Senhor."
    assert _reply("qual o tempo", fetch, path) == "De qual lugar, Senhor."
    assert _reply("faz calor", fetch, path) == "De qual lugar, Senhor."
    assert _reply("faz sol", fetch, path) == "De qual lugar, Senhor."
    assert _reply("está nublado", fetch, path) == "De qual lugar, Senhor."
    assert _reply("vai esfriar", fetch, path) == "De qual lugar, Senhor."
    assert _reply("tempo para amanhã", fetch, path) == "De qual lugar, Senhor."
    assert _reply("está garoando", fetch, path) == "De qual lugar, Senhor."
    assert _reply("tem trovoada", fetch, path) == "De qual lugar, Senhor."
    assert _reply("está quente", fetch, path) == "De qual lugar, Senhor."
    assert _reply("chove", fetch, path) == "De qual lugar, Senhor."
    assert _reply("vai chover hoje", fetch, path) == "De qual lugar, Senhor."
    assert _reply("está chovendo agora", fetch, path) == "De qual lugar, Senhor."
    assert _reply("temperatura da cidade", fetch, path) == "De qual lugar, Senhor."
    assert _reply("qual a previsão para amanhã", fetch, path) == "De qual lugar, Senhor."
    assert _reply("previsão para amanhã", fetch, path) == "De qual lugar, Senhor."
    assert _reply("faz frio", fetch, path) == "De qual lugar, Senhor."
    assert _reply("quantos graus faz", fetch, path) == "De qual lugar, Senhor."
    assert _reply("como vai o tempo", fetch, path) == "De qual lugar, Senhor."
    assert _reply("como está o tempo", fetch, path) == "De qual lugar, Senhor."
    assert _reply("como está", fetch, path) is None
    assert _reply("como está você", fetch, path) is None
    assert _reply("me fala o tempo", fetch, path) == "De qual lugar, Senhor."
    assert _reply("me diz o clima", fetch, path) == "De qual lugar, Senhor."
    assert _reply("temperatura agora", fetch, path) == "De qual lugar, Senhor."
    assert _reply("qual a temperatura agora", fetch, path) == "De qual lugar, Senhor."
    assert _reply("tá quanto", fetch, path) == "De qual lugar, Senhor."
    assert _reply("tem sol", fetch, path) == "De qual lugar, Senhor."
    assert _reply("vai gear", fetch, path) == "De qual lugar, Senhor."
    assert _reply("clima para a semana", fetch, path) == "De qual lugar, Senhor."
    assert _reply("vai dar chuva", fetch, path) == "De qual lugar, Senhor."
    assert _reply("risco de chuva", fetch, path) == "De qual lugar, Senhor."
    assert _reply("pode chover", fetch, path) == "De qual lugar, Senhor."
    assert _reply("será que chove", fetch, path) == "De qual lugar, Senhor."
    assert _reply("me fala se vai chover", fetch, path) == "De qual lugar, Senhor."
    assert _reply("será que vai chover amanhã", fetch, path) == "De qual lugar, Senhor."
    assert _reply("vai chover à noite", fetch, path) == "De qual lugar, Senhor."


def test_day_after_tomorrow_is_not_tomorrow(tmp_path):
    seen = []

    def fetch(url):
        seen.append(url)
        if "geocoding" in url:
            assert "recife" in url.lower() or "curitiba" in url.lower()
            name = "Recife" if "recife" in url.lower() else "Curitiba"
            return '{"results":[{"latitude":-8.0,"longitude":-34.9,"name":"%s"}]}' % name
        if "forecast_days=3" in url:
            assert "temperature_2m_max" in url
            return '{"daily":{"temperature_2m_max":[28,27,31],"weather_code":[1,3,2]}}'
        if "forecast_days=2" in url:
            return '{"daily":{"temperature_2m_max":[28,27],"weather_code":[1,3]}}'
        return '{"current":{"temperature_2m":22,"weather_code":1}}'

    path = tmp_path / "n.json"
    assert _reply("tempo para depois de amanhã", fetch, path) == "De qual lugar, Senhor."
    assert _reply("qualidade do ar depois de amanhã em recife", fetch, path) is None
    assert seen == []
    assert _reply("tempo depois de amanhã em recife", fetch, path) == (
        "Depois de amanhã em Recife, máxima de 31 graus, parcialmente nublado, Senhor."
    )
    assert "name=recife" in seen[-2]
    assert "forecast_days=3" in seen[-1]
    assert _reply("vai chover depois de amanhã em curitiba", fetch, path) == (
        "Depois de amanhã em Curitiba, máxima de 31 graus, parcialmente nublado, Senhor."
    )
    assert "name=curitiba" in seen[-2]
    assert "forecast_days=3" in seen[-1]
    assert _reply("tempo amanhã em recife", fetch, path) == (
        "Amanhã em Recife, máxima de 27 graus, nublado, Senhor."
    )
    assert "forecast_days=2" in seen[-1]
    assert _reply("tempo para depois em recife", fetch, path) == (
        "Em Recife, 22 graus, quase limpo, Senhor."
    )
    assert "daily=" not in seen[-1]
    before = len(seen)
    assert _reply("tempo daqui a dois dias", fetch, path) == "De qual lugar, Senhor."
    assert len(seen) == before
    assert _reply("tempo daqui a dois dias em recife", fetch, path) == (
        "Depois de amanhã em Recife, máxima de 31 graus, parcialmente nublado, Senhor."
    )
    assert "forecast_days=3" in seen[-1]
    assert "name=recife" in seen[-2]


def test_weekend_names_saturday_and_sunday(tmp_path):
    seen = []

    def fetch(url):
        seen.append(url)
        if "geocoding" in url:
            assert "recife" in url.lower() or "curitiba" in url.lower()
            name = "Recife" if "recife" in url.lower() else "Curitiba"
            return '{"results":[{"latitude":-8.0,"longitude":-34.9,"name":"%s"}]}' % name
        if "news.google" in url:
            assert "q=fim" in url
            assert "forecast_days=8" not in url
            return "<rss><channel><item><title>Alpha sobe</title></item></channel></rss>"
        assert "forecast_days=8" in url
        assert "temperature_2m_min" in url
        return (
            '{"daily":{"time":["2026-10-05","2026-10-06","2026-10-07","2026-10-08",'
            '"2026-10-09","2026-10-10","2026-10-11","2026-10-12"],'
            '"temperature_2m_min":[18,18,18,18,18,12,14,18],'
            '"temperature_2m_max":[35,22,22,22,22,26,28,22]}}'
        )

    path = tmp_path / "n.json"
    assert _reply("clima para o fim de semana", fetch, path) == "De qual lugar, Senhor."
    assert _reply("tempo no fim de semana", fetch, path) == "De qual lugar, Senhor."
    assert _reply("notícias do fim de semana", fetch, path) == (
        "Nas notícias, Senhor. Alpha sobe."
    )
    assert "forecast_days=8" not in "".join(seen)
    assert _reply("clima para o fim de semana em recife", fetch, path) == (
        "Em Recife, no fim de semana, de 12 a 28 graus, Senhor."
    )
    assert "name=recife" in seen[-2]
    assert "fim" not in seen[-2]
    assert "forecast_days=8" in seen[-1]
    assert _reply("me fala o tempo no fim de semana em curitiba", fetch, path) == (
        "Em Curitiba, no fim de semana, de 12 a 28 graus, Senhor."
    )
    assert "name=curitiba" in seen[-2]


def test_week_names_the_span(tmp_path):
    seen = []

    def fetch(url):
        seen.append(url)
        if "geocoding" in url:
            assert "recife" in url.lower() or "curitiba" in url.lower()
            name = "Recife" if "recife" in url.lower() else "Curitiba"
            return '{"results":[{"latitude":-8.0,"longitude":-34.9,"name":"%s"}]}' % name
        assert "forecast_days=7" in url
        assert "temperature_2m_min" in url
        assert "weather_code" not in url
        return (
            '{"daily":{"temperature_2m_min":[18,16,-1.6,14],'
            '"temperature_2m_max":[29,27,24,22.2]}}'
        )

    path = tmp_path / "n.json"
    assert _reply("clima para a semana", fetch, path) == "De qual lugar, Senhor."
    assert _reply("tempo da semana", fetch, path) == "De qual lugar, Senhor."
    assert _reply("previsão para a semana que vem", fetch, path) == "De qual lugar, Senhor."
    assert _reply("tempo para pensar", fetch, path) is None
    assert _reply("tempo para amanhã", fetch, path) == "De qual lugar, Senhor."
    assert seen == []
    assert _reply("clima para a semana em recife", fetch, path) == (
        "Em Recife, na semana, de menos 2 a 29 graus, Senhor."
    )
    assert "name=recife" in seen[-2]
    assert "semana" not in seen[-2]
    assert "forecast_days=7" in seen[-1]
    assert _reply("me fala o tempo da semana em curitiba", fetch, path) == (
        "Em Curitiba, na semana, de menos 2 a 29 graus, Senhor."
    )
    assert "name=curitiba" in seen[-2]
    assert _reply("previsão do tempo para a semana em recife", fetch, path) == (
        "Em Recife, na semana, de menos 2 a 29 graus, Senhor."
    )


def test_weather_names_the_city(tmp_path):
    def fetch(url):
        if "geocoding" in url:
            return '{"results":[{"latitude":-22.9,"longitude":-43.2,"name":"Rio de Janeiro"}]}'
        return '{"current":{"temperature_2m":28.2,"weather_code":95}}'

    assert _reply("tempo em rio", fetch, tmp_path / "n.json") == (
        "Em Rio de Janeiro, 28 graus, trovoada, Senhor."
    )


def test_weather_hears_the_city_inside_the_question(tmp_path):
    seen = []

    def fetch(url):
        seen.append(url)
        if "geocoding" in url:
            assert any(city in url.lower() for city in ("paulo", "curitiba", "rio", "recife"))
            return '{"results":[{"latitude":-23.5,"longitude":-46.6,"name":"São Paulo"}]}'
        if "temperature_2m_min" in url:
            assert "forecast_days=7" in url
            return (
                '{"daily":{"temperature_2m_min":[18,16,15,14,17,18,19],'
                '"temperature_2m_max":[27,26,24,22,25,28,29]}}'
            )
        if "daily=" in url:
            return '{"daily":{"temperature_2m_max":[20,27],"weather_code":[1,3]}}'
        return '{"current":{"temperature_2m":22,"weather_code":1}}'

    path = tmp_path / "n.json"
    assert _reply("qual o clima em São Paulo", fetch, path) == (
        "Em São Paulo, 22 graus, quase limpo, Senhor."
    )
    assert _reply("clima São Paulo", fetch, path) == (
        "Em São Paulo, 22 graus, quase limpo, Senhor."
    )
    assert _reply("qual é o clima", fetch, path) == "De qual lugar, Senhor."
    assert _reply("clima agora", fetch, path) == "De qual lugar, Senhor."
    assert _reply("tempo são paulo", fetch, path) == (
        "Em São Paulo, 22 graus, quase limpo, Senhor."
    )
    assert _reply("previsão curitiba", fetch, path) == (
        "Em São Paulo, 22 graus, quase limpo, Senhor."
    )
    assert any("curitiba" in url for url in seen)
    assert _reply("qual a previsão para curitiba", fetch, path) == (
        "Em São Paulo, 22 graus, quase limpo, Senhor."
    )
    assert _reply("tempo para pensar", fetch, path) is None
    assert _reply("tempo no rio", fetch, path) == (
        "Em São Paulo, 22 graus, quase limpo, Senhor."
    )
    assert any("rio" in url for url in seen)
    assert _reply("clima do rio", fetch, path) == (
        "Em São Paulo, 22 graus, quase limpo, Senhor."
    )
    assert _reply("qual a temperatura em recife", fetch, path) == (
        "Em São Paulo, 22 graus, quase limpo, Senhor."
    )
    assert any("recife" in url for url in seen)
    assert _reply("qual a temperatura", fetch, path) == "De qual lugar, Senhor."
    assert _reply("vai chover", fetch, path) == "De qual lugar, Senhor."
    assert _reply("vai chover em curitiba", fetch, path) == (
        "Em São Paulo, 22 graus, quase limpo, Senhor."
    )
    assert "curitiba" in seen[-2]
    assert _reply("qual o clima de recife", fetch, path) == (
        "Em São Paulo, 22 graus, quase limpo, Senhor."
    )
    assert "recife" in seen[-2]
    assert _reply("como está o tempo no rio", fetch, path) == (
        "Em São Paulo, 22 graus, quase limpo, Senhor."
    )
    assert "rio" in seen[-2]
    assert _reply("como está recife", fetch, path) == (
        "Em São Paulo, 22 graus, quase limpo, Senhor."
    )
    assert "name=recife" in seen[-2]
    assert "daily=" not in seen[-1]
    assert _reply("como tá curitiba", fetch, path) == (
        "Em São Paulo, 22 graus, quase limpo, Senhor."
    )
    assert "name=curitiba" in seen[-2]
    assert _reply("como vai recife", fetch, path) == (
        "Em São Paulo, 22 graus, quase limpo, Senhor."
    )
    assert "name=recife" in seen[-2]
    assert _reply("me fala como está recife", fetch, path) == (
        "Em São Paulo, 22 graus, quase limpo, Senhor."
    )
    assert "name=recife" in seen[-2]
    assert _reply("como está recife amanhã", fetch, path) == (
        "Amanhã em São Paulo, máxima de 27 graus, nublado, Senhor."
    )
    assert "name=recife" in seen[-2]
    assert "amanha" not in seen[-2]
    assert "daily=" in seen[-1]
    assert _reply("previsão do tempo para curitiba", fetch, path) == (
        "Em São Paulo, 22 graus, quase limpo, Senhor."
    )
    assert "curitiba" in seen[-2]
    assert _reply("previsão do tempo", fetch, path) == "De qual lugar, Senhor."
    assert _reply("está chovendo", fetch, path) == "De qual lugar, Senhor."
    assert _reply("está chovendo em curitiba", fetch, path) == (
        "Em São Paulo, 22 graus, quase limpo, Senhor."
    )
    assert "curitiba" in seen[-2]
    assert _reply("faz calor em recife", fetch, path) == (
        "Em São Paulo, 22 graus, quase limpo, Senhor."
    )
    assert "recife" in seen[-2]
    assert _reply("está quente no rio", fetch, path) == (
        "Em São Paulo, 22 graus, quase limpo, Senhor."
    )
    assert "rio" in seen[-2]
    assert _reply("chove em curitiba", fetch, path) == (
        "Em São Paulo, 22 graus, quase limpo, Senhor."
    )
    assert "curitiba" in seen[-2]
    assert _reply("vai chover hoje em curitiba", fetch, path) == (
        "Em São Paulo, 22 graus, quase limpo, Senhor."
    )
    assert "curitiba" in seen[-2]
    assert "hoje" not in seen[-2]
    assert _reply("está chovendo agora em curitiba", fetch, path) == (
        "Em São Paulo, 22 graus, quase limpo, Senhor."
    )
    assert "curitiba" in seen[-2]
    assert "agora" not in seen[-2]
    assert _reply("chove em curitiba hoje", fetch, path) == (
        "Em São Paulo, 22 graus, quase limpo, Senhor."
    )
    assert "name=curitiba" in seen[-2]
    assert _reply("temperatura de são paulo", fetch, path) == (
        "Em São Paulo, 22 graus, quase limpo, Senhor."
    )
    assert "paulo" in seen[-2]
    assert _reply("qual a temperatura de recife", fetch, path) == (
        "Em São Paulo, 22 graus, quase limpo, Senhor."
    )
    assert "recife" in seen[-2]
    assert _reply("temperatura no rio", fetch, path) == (
        "Em São Paulo, 22 graus, quase limpo, Senhor."
    )
    assert "rio" in seen[-2]
    assert _reply("qual o tempo lá em recife", fetch, path) == (
        "Em São Paulo, 22 graus, quase limpo, Senhor."
    )
    assert "name=recife" in seen[-2]
    assert _reply("faz sol em recife", fetch, path) == (
        "Em São Paulo, 22 graus, quase limpo, Senhor."
    )
    assert "name=recife" in seen[-2]
    assert _reply("está nublado em curitiba", fetch, path) == (
        "Em São Paulo, 22 graus, quase limpo, Senhor."
    )
    assert "name=curitiba" in seen[-2]
    assert _reply("vai esfriar em curitiba", fetch, path) == (
        "Em São Paulo, 22 graus, quase limpo, Senhor."
    )
    assert "name=curitiba" in seen[-2]
    assert _reply("vai esfriar hoje em curitiba", fetch, path) == (
        "Em São Paulo, 22 graus, quase limpo, Senhor."
    )
    assert "name=curitiba" in seen[-2]
    assert "hoje" not in seen[-2]
    assert _reply("tempo para amanhã em curitiba", fetch, path) == (
        "Amanhã em São Paulo, máxima de 27 graus, nublado, Senhor."
    )
    assert "name=curitiba" in seen[-2]
    assert "amanha" not in seen[-2]
    assert "daily=" in seen[-1]
    assert _reply("vai chover amanhã em curitiba", fetch, path) == (
        "Amanhã em São Paulo, máxima de 27 graus, nublado, Senhor."
    )
    assert "name=curitiba" in seen[-2]
    assert _reply("clima amanhã no rio", fetch, path) == (
        "Amanhã em São Paulo, máxima de 27 graus, nublado, Senhor."
    )
    assert "name=rio" in seen[-2]
    assert "amanha" not in seen[-2]
    assert _reply("tempo para hoje em curitiba", fetch, path) == (
        "Em São Paulo, 22 graus, quase limpo, Senhor."
    )
    assert "daily=" not in seen[-1]
    assert _reply("está garoando em curitiba", fetch, path) == (
        "Em São Paulo, 22 graus, quase limpo, Senhor."
    )
    assert "name=curitiba" in seen[-2]
    assert _reply("tem trovoada no rio", fetch, path) == (
        "Em São Paulo, 22 graus, quase limpo, Senhor."
    )
    assert "name=rio" in seen[-2]
    assert _reply("qual a temperatura agora em recife", fetch, path) == (
        "Em São Paulo, 22 graus, quase limpo, Senhor."
    )
    assert "name=recife" in seen[-2]
    assert "agora" not in seen[-2]
    assert "daily=" not in seen[-1]
    assert _reply("faz frio em curitiba", fetch, path) == (
        "Em São Paulo, 22 graus, quase limpo, Senhor."
    )
    assert "name=curitiba" in seen[-2]
    assert _reply("quantos graus faz em recife", fetch, path) == (
        "Em São Paulo, 22 graus, quase limpo, Senhor."
    )
    assert "name=recife" in seen[-2]
    assert "daily=" not in seen[-1]
    assert _reply("amanhã vai chover em recife", fetch, path) == (
        "Amanhã em São Paulo, máxima de 27 graus, nublado, Senhor."
    )
    assert "name=recife" in seen[-2]
    assert "amanha" not in seen[-2]
    assert "daily=" in seen[-1]
    assert _reply("vai fazer frio amanhã em curitiba", fetch, path) == (
        "Amanhã em São Paulo, máxima de 27 graus, nublado, Senhor."
    )
    assert "name=curitiba" in seen[-2]
    assert "amanha" not in seen[-2]
    assert _reply("como vai o tempo em recife", fetch, path) == (
        "Em São Paulo, 22 graus, quase limpo, Senhor."
    )
    assert "name=recife" in seen[-2]
    assert "daily=" not in seen[-1]
    assert _reply("tá quanto em recife", fetch, path) == (
        "Em São Paulo, 22 graus, quase limpo, Senhor."
    )
    assert "name=recife" in seen[-2]
    assert _reply("quanto tá em curitiba", fetch, path) == (
        "Em São Paulo, 22 graus, quase limpo, Senhor."
    )
    assert "name=curitiba" in seen[-2]
    assert _reply("quantos graus está fazendo em recife", fetch, path) == (
        "Em São Paulo, 22 graus, quase limpo, Senhor."
    )
    assert "name=recife" in seen[-2]
    assert "fazendo" not in seen[-2]
    assert _reply("tem sol em recife", fetch, path) == (
        "Em São Paulo, 22 graus, quase limpo, Senhor."
    )
    assert "name=recife" in seen[-2]
    assert _reply("vai gear em curitiba", fetch, path) == (
        "Em São Paulo, 22 graus, quase limpo, Senhor."
    )
    assert "name=curitiba" in seen[-2]
    assert _reply("clima para a semana em curitiba", fetch, path) == (
        "Em São Paulo, na semana, de 14 a 29 graus, Senhor."
    )
    assert "name=curitiba" in seen[-2]
    assert "semana" not in seen[-2]
    assert "forecast_days=7" in seen[-1]
    assert _reply("vai dar chuva em curitiba", fetch, path) == (
        "Em São Paulo, 22 graus, quase limpo, Senhor."
    )
    assert "name=curitiba" in seen[-2]
    assert _reply("vai dar chuva amanhã em recife", fetch, path) == (
        "Amanhã em São Paulo, máxima de 27 graus, nublado, Senhor."
    )
    assert "name=recife" in seen[-2]
    assert "amanha" not in seen[-2]
    assert "daily=" in seen[-1]
    assert _reply("risco de chuva em curitiba", fetch, path) == (
        "Em São Paulo, 22 graus, quase limpo, Senhor."
    )
    assert "name=curitiba" in seen[-2]
    assert "daily=" not in seen[-1]
    assert _reply("pode chover em recife", fetch, path) == (
        "Em São Paulo, 22 graus, quase limpo, Senhor."
    )
    assert "name=recife" in seen[-2]
    assert _reply("será que chove em recife", fetch, path) == (
        "Em São Paulo, 22 graus, quase limpo, Senhor."
    )
    assert "name=recife" in seen[-2]
    assert "daily=" not in seen[-1]
    assert _reply("me fala se vai chover em curitiba", fetch, path) == (
        "Em São Paulo, 22 graus, quase limpo, Senhor."
    )
    assert "name=curitiba" in seen[-2]
    assert _reply("se vai chover em recife", fetch, path) == (
        "Em São Paulo, 22 graus, quase limpo, Senhor."
    )
    assert "name=recife" in seen[-2]
    assert _reply("será que vai chover amanhã em recife", fetch, path) == (
        "Amanhã em São Paulo, máxima de 27 graus, nublado, Senhor."
    )
    assert "name=recife" in seen[-2]
    assert "amanha" not in seen[-2]
    assert "daily=" in seen[-1]
    assert _reply("vai chover à noite em recife", fetch, path) == (
        "Em São Paulo, 22 graus, quase limpo, Senhor."
    )
    assert "name=recife" in seen[-2]
    assert "noite" not in seen[-2]
    assert "daily=" not in seen[-1]
    assert _reply("vai chover amanhã à noite em recife", fetch, path) == (
        "Amanhã em São Paulo, máxima de 27 graus, nublado, Senhor."
    )
    assert "name=recife" in seen[-2]
    assert "daily=" in seen[-1]
    assert _reply("faz frio à noite em curitiba", fetch, path) == (
        "Em São Paulo, 22 graus, quase limpo, Senhor."
    )
    assert "name=curitiba" in seen[-2]
    assert "daily=" not in seen[-1]


def test_humidity_names_the_city(tmp_path):
    seen = []

    def fetch(url):
        seen.append(url)
        if "geocoding" in url:
            assert "recife" in url.lower() or "curitiba" in url.lower()
            name = "Recife" if "recife" in url.lower() else "Curitiba"
            return (
                '{"results":[{"latitude":-8.0,"longitude":-34.9,"name":"%s"}]}' % name
            )
        if "relative_humidity_2m_mean" in url:
            assert "forecast_days=2" in url
            assert "temperature_2m" not in url
            return '{"daily":{"relative_humidity_2m_mean":[80,64]}}'
        assert "relative_humidity_2m" in url
        assert "current=" in url
        assert "temperature_2m" not in url
        return '{"current":{"relative_humidity_2m":80}}'

    path = tmp_path / "n.json"
    assert _reply("umidade", fetch, path) == "De qual lugar, Senhor."
    assert _reply("tá úmido", fetch, path) == "De qual lugar, Senhor."
    assert _reply("me fala a umidade", fetch, path) == "De qual lugar, Senhor."
    assert _reply("umidade amanhã", fetch, path) == "De qual lugar, Senhor."
    assert _reply("tá úmido amanhã", fetch, path) == "De qual lugar, Senhor."
    assert _reply("me fala tá úmido", fetch, path) == "De qual lugar, Senhor."
    assert seen == []
    assert _reply("umidade em recife", fetch, path) == (
        "Em Recife, umidade de 80 por cento, Senhor."
    )
    assert _reply("qual a umidade do ar em curitiba", fetch, path) == (
        "Em Curitiba, umidade de 80 por cento, Senhor."
    )
    assert _reply("tá úmido em recife", fetch, path) == (
        "Em Recife, umidade de 80 por cento, Senhor."
    )
    assert _reply("me fala a umidade em recife", fetch, path) == (
        "Em Recife, umidade de 80 por cento, Senhor."
    )
    assert _reply("me fala tá úmido em recife", fetch, path) == (
        "Em Recife, umidade de 80 por cento, Senhor."
    )
    assert "daily=" not in seen[-1]
    assert _reply("umidade amanhã em recife", fetch, path) == (
        "Amanhã em Recife, umidade de 64 por cento, Senhor."
    )
    assert "name=recife" in seen[-2]
    assert "relative_humidity_2m_mean" in seen[-1]
    assert "forecast_days=2" in seen[-1]
    assert _reply("umidade para amanhã em recife", fetch, path) == (
        "Amanhã em Recife, umidade de 64 por cento, Senhor."
    )
    assert _reply("tá úmido amanhã em recife", fetch, path) == (
        "Amanhã em Recife, umidade de 64 por cento, Senhor."
    )
    assert "name=recife" in seen[-2]
    assert "amanha" not in seen[-2]
    assert "relative_humidity_2m_mean" in seen[-1]
    assert "graus" not in _reply("umidade em recife", fetch, path)


def test_feels_like_names_the_city(tmp_path):
    seen = []

    def fetch(url):
        seen.append(url)
        if "geocoding" in url:
            assert "curitiba" in url.lower() or "recife" in url.lower()
            name = "Curitiba" if "curitiba" in url.lower() else "Recife"
            return (
                '{"results":[{"latitude":-25.4,"longitude":-49.2,"name":"%s"}]}' % name
            )
        if "apparent_temperature_mean" in url:
            assert "forecast_days=2" in url
            assert "temperature_2m" not in url
            assert "relative_humidity" not in url
            return '{"daily":{"apparent_temperature_mean":[14.2,21.4]}}'
        assert "apparent_temperature" in url
        assert "current=" in url
        assert "temperature_2m" not in url
        assert "relative_humidity" not in url
        return '{"current":{"apparent_temperature":14.2}}'

    path = tmp_path / "n.json"
    assert _reply("sensação térmica", fetch, path) == "De qual lugar, Senhor."
    assert _reply("me fala a sensação térmica", fetch, path) == "De qual lugar, Senhor."
    assert _reply("sensação térmica amanhã", fetch, path) == "De qual lugar, Senhor."
    assert _reply("sensação", fetch, path) == "De qual lugar, Senhor."
    assert _reply("qual a sensação", fetch, path) == "De qual lugar, Senhor."
    assert _reply("sensação do projeto", fetch, path) is None
    assert seen == []
    assert _reply("sensação térmica em curitiba", fetch, path) == (
        "Em Curitiba, sensação de 14 graus, Senhor."
    )
    assert _reply("qual a sensação térmica em recife", fetch, path) == (
        "Em Recife, sensação de 14 graus, Senhor."
    )
    assert _reply("me fala a sensação térmica em recife", fetch, path) == (
        "Em Recife, sensação de 14 graus, Senhor."
    )
    assert _reply("qual a sensação em recife", fetch, path) == (
        "Em Recife, sensação de 14 graus, Senhor."
    )
    assert _reply("me fala a sensação em curitiba", fetch, path) == (
        "Em Curitiba, sensação de 14 graus, Senhor."
    )
    assert "daily=" not in seen[-1]
    assert _reply("sensação térmica amanhã em recife", fetch, path) == (
        "Amanhã em Recife, sensação de 21 graus, Senhor."
    )
    assert _reply("sensação amanhã em recife", fetch, path) == (
        "Amanhã em Recife, sensação de 21 graus, Senhor."
    )
    assert "apparent_temperature_mean" in seen[-1]
    assert "forecast_days=2" in seen[-1]


def test_wind_names_the_city(tmp_path):
    seen = []

    def fetch(url):
        seen.append(url)
        if "geocoding" in url:
            assert "recife" in url.lower() or "curitiba" in url.lower()
            name = "Recife" if "recife" in url.lower() else "Curitiba"
            return (
                '{"results":[{"latitude":-8.0,"longitude":-34.9,"name":"%s"}]}' % name
            )
        if "wind_speed_10m_mean" in url:
            assert "forecast_days=2" in url
            assert "temperature_2m" not in url
            assert "apparent_temperature" not in url
            assert "relative_humidity" not in url
            return '{"daily":{"wind_speed_10m_mean":[18.4,12.2]}}'
        assert "wind_speed_10m" in url
        assert "current=" in url
        assert "temperature_2m" not in url
        assert "apparent_temperature" not in url
        assert "relative_humidity" not in url
        return '{"current":{"wind_speed_10m":18.4}}'

    path = tmp_path / "n.json"
    assert _reply("vento", fetch, path) == "De qual lugar, Senhor."
    assert _reply("tá ventando", fetch, path) == "De qual lugar, Senhor."
    assert _reply("me diz o vento", fetch, path) == "De qual lugar, Senhor."
    assert _reply("vento para amanhã", fetch, path) == "De qual lugar, Senhor."
    assert _reply("tá ventando amanhã", fetch, path) == "De qual lugar, Senhor."
    assert _reply("me fala tá ventando", fetch, path) == "De qual lugar, Senhor."
    assert seen == []
    assert _reply("vento em recife", fetch, path) == (
        "Em Recife, vento de 18 quilômetros por hora, Senhor."
    )
    assert _reply("qual a velocidade do vento em curitiba", fetch, path) == (
        "Em Curitiba, vento de 18 quilômetros por hora, Senhor."
    )
    assert _reply("tá ventando em recife", fetch, path) == (
        "Em Recife, vento de 18 quilômetros por hora, Senhor."
    )
    assert _reply("me diz o vento em curitiba", fetch, path) == (
        "Em Curitiba, vento de 18 quilômetros por hora, Senhor."
    )
    assert _reply("me fala tá ventando em recife", fetch, path) == (
        "Em Recife, vento de 18 quilômetros por hora, Senhor."
    )
    assert "daily=" not in seen[-1]
    assert _reply("vento amanhã em curitiba", fetch, path) == (
        "Amanhã em Curitiba, vento de 12 quilômetros por hora, Senhor."
    )
    assert "name=curitiba" in seen[-2]
    assert "wind_speed_10m_mean" in seen[-1]
    assert "forecast_days=2" in seen[-1]
    assert _reply("tá ventando amanhã em curitiba", fetch, path) == (
        "Amanhã em Curitiba, vento de 12 quilômetros por hora, Senhor."
    )
    assert "name=curitiba" in seen[-2]
    assert "amanha" not in seen[-2]
    assert "wind_speed_10m_mean" in seen[-1]


def test_sun_names_the_city(tmp_path):
    seen = []

    def fetch(url):
        seen.append(url)
        if "geocoding" in url:
            assert "recife" in url.lower() or "curitiba" in url.lower()
            name = "Recife" if "recife" in url.lower() else "Curitiba"
            return (
                '{"results":[{"latitude":-8.0,"longitude":-34.9,"name":"%s"}]}' % name
            )
        if "daily=sunrise" in url:
            return '{"daily":{"sunrise":["2026-10-05T05:12","2026-10-06T05:13"]}}'
        if "daily=sunset" in url:
            return '{"daily":{"sunset":["2026-10-05T17:40","2026-10-06T17:41"]}}'
        raise AssertionError(url)

    path = tmp_path / "n.json"
    assert _reply("nascer do sol", fetch, path) == "De qual lugar, Senhor."
    assert _reply("pôr do sol", fetch, path) == "De qual lugar, Senhor."
    assert _reply("me fala o nascer do sol", fetch, path) == "De qual lugar, Senhor."
    assert seen == []
    assert _reply("nascer do sol em recife", fetch, path) == (
        "Em Recife, o sol nasce às 5 horas e 12 minutos, Senhor."
    )
    assert "daily=sunrise" in seen[-1]
    assert "temperature_2m" not in seen[-1]
    assert _reply("que horas o sol nasce em recife", fetch, path) == (
        "Em Recife, o sol nasce às 5 horas e 12 minutos, Senhor."
    )
    assert _reply("nascer do sol amanhã em recife", fetch, path) == (
        "Amanhã em Recife, o sol nasce às 5 horas e 13 minutos, Senhor."
    )
    assert "forecast_days=2" in seen[-1]
    assert _reply("pôr do sol em curitiba", fetch, path) == (
        "Em Curitiba, o sol se põe às 17 horas e 40 minutos, Senhor."
    )
    assert "daily=sunset" in seen[-1]
    assert _reply("que horas o sol se põe em curitiba", fetch, path) == (
        "Em Curitiba, o sol se põe às 17 horas e 40 minutos, Senhor."
    )
    assert _reply("me fala o nascer do sol em recife", fetch, path) == (
        "Em Recife, o sol nasce às 5 horas e 12 minutos, Senhor."
    )
    assert "daily=sunrise" in seen[-1]


def test_uv_names_the_city(tmp_path):
    seen = []

    def fetch(url):
        seen.append(url)
        if "geocoding" in url:
            assert "recife" in url.lower() or "curitiba" in url.lower()
            name = "Recife" if "recife" in url.lower() else "Curitiba"
            return (
                '{"results":[{"latitude":-8.0,"longitude":-34.9,"name":"%s"}]}' % name
            )
        assert "uv_index_max" in url
        assert "temperature_2m" not in url
        return '{"daily":{"uv_index_max":[11.2,9.4]}}'

    path = tmp_path / "n.json"
    assert _reply("índice uv", fetch, path) == "De qual lugar, Senhor."
    assert _reply("uv", fetch, path) == "De qual lugar, Senhor."
    assert _reply("me diz o uv", fetch, path) == "De qual lugar, Senhor."
    assert seen == []
    assert _reply("índice uv em recife", fetch, path) == (
        "Em Recife, índice UV de 11, Senhor."
    )
    assert "forecast_days=1" in seen[-1]
    assert _reply("qual o uv em curitiba", fetch, path) == (
        "Em Curitiba, índice UV de 11, Senhor."
    )
    assert _reply("uv amanhã em recife", fetch, path) == (
        "Amanhã em Recife, índice UV de 9, Senhor."
    )
    assert "forecast_days=2" in seen[-1]
    assert _reply("me diz o uv em recife", fetch, path) == (
        "Em Recife, índice UV de 11, Senhor."
    )
    assert "forecast_days=1" in seen[-1]


def test_pressure_names_the_city(tmp_path):
    seen = []

    def fetch(url):
        seen.append(url)
        if "geocoding" in url:
            assert "recife" in url.lower() or "curitiba" in url.lower()
            name = "Recife" if "recife" in url.lower() else "Curitiba"
            return (
                '{"results":[{"latitude":-8.0,"longitude":-34.9,"name":"%s"}]}' % name
            )
        if "surface_pressure_mean" in url:
            assert "forecast_days=2" in url
            assert "temperature_2m" not in url
            return '{"daily":{"surface_pressure_mean":[1013.4,1008.2]}}'
        assert "surface_pressure" in url
        assert "current=" in url
        assert "temperature_2m" not in url
        return '{"current":{"surface_pressure":1013.4}}'

    path = tmp_path / "n.json"
    assert _reply("pressão", fetch, path) == "De qual lugar, Senhor."
    assert _reply("pressão atmosférica", fetch, path) == "De qual lugar, Senhor."
    assert _reply("me conta a pressão", fetch, path) == "De qual lugar, Senhor."
    assert _reply("pressão amanhã", fetch, path) == "De qual lugar, Senhor."
    assert seen == []
    assert _reply("pressão em recife", fetch, path) == (
        "Em Recife, pressão de 1013 milibares, Senhor."
    )
    assert _reply("qual a pressão atmosférica em curitiba", fetch, path) == (
        "Em Curitiba, pressão de 1013 milibares, Senhor."
    )
    assert _reply("me conta a pressão em recife", fetch, path) == (
        "Em Recife, pressão de 1013 milibares, Senhor."
    )
    assert "daily=" not in seen[-1]
    assert _reply("pressão amanhã em recife", fetch, path) == (
        "Amanhã em Recife, pressão de 1008 milibares, Senhor."
    )
    assert "name=recife" in seen[-2]
    assert "surface_pressure_mean" in seen[-1]
    assert "forecast_days=2" in seen[-1]


def test_rain_chance_names_the_city(tmp_path):
    seen = []

    def fetch(url):
        seen.append(url)
        if "geocoding" in url:
            assert "recife" in url.lower() or "curitiba" in url.lower()
            name = "Recife" if "recife" in url.lower() else "Curitiba"
            return (
                '{"results":[{"latitude":-8.0,"longitude":-34.9,"name":"%s"}]}' % name
            )
        assert "precipitation_probability_max" in url
        assert "temperature_2m" not in url
        assert "weather_code" not in url
        return '{"daily":{"precipitation_probability_max":[40,81]}}'

    path = tmp_path / "n.json"
    assert _reply("chance de chuva", fetch, path) == "De qual lugar, Senhor."
    assert _reply("probabilidade de chuva", fetch, path) == "De qual lugar, Senhor."
    assert _reply("me fala a chance de chuva", fetch, path) == "De qual lugar, Senhor."
    assert _reply("risco de chuva", fetch, path) == "De qual lugar, Senhor."
    assert seen == []
    assert _reply("chance de chuva em recife", fetch, path) == (
        "Em Recife, chance de chuva de 40 por cento, Senhor."
    )
    assert "name=recife" in seen[-2]
    assert "forecast_days=1" in seen[-1]
    assert _reply("me fala a probabilidade de chuva em curitiba", fetch, path) == (
        "Em Curitiba, chance de chuva de 40 por cento, Senhor."
    )
    assert _reply("chance de chuva amanhã em recife", fetch, path) == (
        "Amanhã em Recife, chance de chuva de 81 por cento, Senhor."
    )
    assert "forecast_days=2" in seen[-1]
    assert "amanha" not in seen[-2]
    assert _reply("probabilidade de chuva para amanhã em curitiba", fetch, path) == (
        "Amanhã em Curitiba, chance de chuva de 81 por cento, Senhor."
    )
    assert "name=curitiba" in seen[-2]


def test_extreme_names_the_city(tmp_path):
    seen = []

    def fetch(url):
        seen.append(url)
        if "geocoding" in url:
            assert "recife" in url.lower() or "curitiba" in url.lower()
            name = "Recife" if "recife" in url.lower() else "Curitiba"
            return (
                '{"results":[{"latitude":-8.0,"longitude":-34.9,"name":"%s"}]}' % name
            )
        if "temperature_2m_min" in url:
            assert "temperature_2m_max" not in url
            assert "weather_code" not in url
            return '{"daily":{"temperature_2m_min":[21.2,16.4]}}'
        assert "temperature_2m_max" in url
        assert "weather_code" not in url
        return '{"daily":{"temperature_2m_max":[31.6,29.2]}}'

    path = tmp_path / "n.json"
    assert _reply("qual a máxima", fetch, path) == "De qual lugar, Senhor."
    assert _reply("qual a mínima", fetch, path) == "De qual lugar, Senhor."
    assert seen == []
    assert _reply("qual a máxima em recife", fetch, path) == (
        "Em Recife, máxima de 32 graus, Senhor."
    )
    assert "name=recife" in seen[-2]
    assert "forecast_days=1" in seen[-1]
    assert _reply("qual a mínima em curitiba", fetch, path) == (
        "Em Curitiba, mínima de 21 graus, Senhor."
    )
    assert "name=curitiba" in seen[-2]
    assert _reply("máxima de amanhã em recife", fetch, path) == (
        "Amanhã em Recife, máxima de 29 graus, Senhor."
    )
    assert "forecast_days=2" in seen[-1]
    assert "amanha" not in seen[-2]
    assert _reply("mínima amanhã em curitiba", fetch, path) == (
        "Amanhã em Curitiba, mínima de 16 graus, Senhor."
    )
    assert _reply("me fala a máxima em recife", fetch, path) == (
        "Em Recife, máxima de 32 graus, Senhor."
    )
    assert "name=recife" in seen[-2]
    assert "forecast_days=1" in seen[-1]
    assert _reply("máxima para amanhã em recife", fetch, path) == (
        "Amanhã em Recife, máxima de 29 graus, Senhor."
    )
    assert "forecast_days=2" in seen[-1]
    assert "amanha" not in seen[-2]
    before = len(seen)
    assert _reply("me fala a máxima", fetch, path) == "De qual lugar, Senhor."
    assert len(seen) == before


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
    assert _reply("notícias economia", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert "economia" in seen[-1]
    assert _reply("o que está acontecendo no Brasil", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert "brasil" in seen[-1].lower()
    before = len(seen)
    assert _reply("notícias sobre", fetch, tmp_path / "n.json") == "Sobre o que, Senhor."
    assert _reply("quais as novidades", fetch, tmp_path / "n.json") == "Sobre o que, Senhor."
    assert _reply("notícias", fetch, tmp_path / "n.json") == "Sobre o que, Senhor."
    assert len(seen) == before
    assert _reply("notícia nova", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert "brasil" in seen[-1].lower()
    assert "nova" not in seen[-1].lower()
    assert _reply("tem notícia nova", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert "brasil" in seen[-1].lower()
    assert _reply("alguma novidade", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert "brasil" in seen[-1].lower()
    assert _reply("notícia nova de economia", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert "economia" in seen[-1]
    assert _reply("últimas notícias", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert "brasil" in seen[-1].lower()
    assert _reply("quais as últimas notícias", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert _reply("o que há de novo", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert "brasil" in seen[-1].lower()
    assert _reply("o que há de novo sobre tecnologia", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert "tecnologia" in seen[-1]
    assert _reply("o que há de novo na geladeira", fetch, tmp_path / "n.json") is None
    assert _reply("o que houve de novo", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert "brasil" in seen[-1].lower()
    assert _reply("o que houve de novo sobre tecnologia", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert "tecnologia" in seen[-1]
    assert _reply("o que houve de novo na geladeira", fetch, tmp_path / "n.json") is None
    assert _reply("me conta o que há de novo", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert "brasil" in seen[-1].lower()
    assert _reply("o que há de novo hoje", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert "brasil" in seen[-1].lower()
    assert "hoje" not in seen[-1].lower()
    assert _reply("notícias de agora", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=brasil")
    assert "agora" not in seen[-1].lower()
    assert _reply("notícia de agora", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=brasil")
    assert _reply("notícias de hoje", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=hoje")
    assert _reply("notícias de última hora", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=brasil")
    assert "hora" not in seen[-1].lower()
    assert _reply("manchetes de última hora", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=brasil")
    assert _reply("notícias urgentes", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=brasil")
    assert "urgente" not in seen[-1].lower()
    assert _reply("notícias de última hora sobre economia", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=economia")
    assert "hora" not in seen[-1].lower()
    assert "ultima" not in seen[-1].lower()
    assert _reply("notícias urgentes sobre tecnologia", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=tecnologia")
    assert "urgente" not in seen[-1].lower()
    assert _reply("manchetes de última hora sobre esporte", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=esporte")
    assert "hora" not in seen[-1].lower()
    assert _reply("plantão", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=brasil")
    assert _reply("plantão de notícias", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=brasil")
    assert "noticia" not in seen[-1].lower()
    assert _reply("me dá o plantão", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=brasil")
    assert _reply("plantão de economia", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=economia")
    assert _reply("plantão da economia", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=economia")
    assert _reply("o plantão da economia", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=economia")
    assert _reply("plantão do esporte", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=esporte")
    assert _reply("plantão a respeito de tecnologia", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=tecnologia")
    assert "respeito" not in seen[-1].lower()
    assert _reply("plantão sobre tecnologia", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=tecnologia")
    assert _reply("o que houve hoje", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=brasil")
    assert "hoje" not in seen[-1].lower()
    assert _reply("o que houve agora", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=brasil")
    assert "agora" not in seen[-1].lower()
    assert _reply("me conta o que houve hoje", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert "hoje" not in seen[-1].lower()
    before = len(seen)
    assert _reply("o que aconteceu", fetch, tmp_path / "n.json") == "Sobre o que, Senhor."
    assert _reply("o que houve", fetch, tmp_path / "n.json") is None
    assert _reply("o que houve na geladeira", fetch, tmp_path / "n.json") is None
    assert len(seen) == before
    assert _reply("o que aconteceu no brasil", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert "brasil" in seen[-1].lower()
    assert _reply("novidades sobre tecnologia", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert "tecnologia" in seen[-1]
    assert _reply("manchetes", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=brasil")
    assert _reply("quais as manchetes", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=brasil")
    assert _reply("manchetes de economia", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=economia")
    assert _reply("me dá as notícias", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=brasil")
    assert _reply("me conta as notícias", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=brasil")
    assert _reply("me diz as últimas notícias", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=brasil")
    assert _reply("me dá as notícias de economia", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=economia")
    assert _reply("me atualiza das notícias", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=brasil")
    assert _reply("atualiza as notícias", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=brasil")
    assert _reply("me atualiza das notícias de economia", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=economia")
    assert _reply("me atualiza sobre economia", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=economia")
    assert "atualiza" not in seen[-1].lower()
    assert _reply("atualiza sobre tecnologia", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=tecnologia")
    assert _reply("me atualiza a respeito de economia", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=economia")
    assert "respeito" not in seen[-1].lower()
    assert _reply("atualiza a respeito da tecnologia", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=tecnologia")
    assert _reply("me atualiza sobre as notícias", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=brasil")
    assert "noticia" not in seen[-1].lower()
    assert _reply("me atualiza sobre o brasil", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=brasil")
    assert "o%20brasil" not in seen[-1].lower()
    assert _reply("me atualiza quanto à economia", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=economia")
    assert "quanto" not in seen[-1].lower()
    assert _reply("atualiza quanto ao esporte", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=esporte")
    assert _reply("me atualiza quanto às notícias", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=brasil")
    assert "noticia" not in seen[-1].lower()
    assert _reply("notícias quanto à economia", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=economia")
    assert "quanto" not in seen[-1].lower()
    assert _reply("manchetes quanto à tecnologia", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=tecnologia")
    assert "quanto" not in seen[-1].lower()
    assert _reply("plantão quanto à economia", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=economia")
    assert "quanto" not in seen[-1].lower()
    assert _reply("me dá as notícias quanto ao esporte", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=esporte")
    assert "quanto" not in seen[-1].lower()
    assert _reply("resumo das notícias", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=brasil")
    assert _reply("me dá um resumo das notícias", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=brasil")
    assert _reply("resumo das notícias de economia", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=economia")
    assert _reply("o que está rolando", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=brasil")
    assert _reply("o que tá rolando", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=brasil")
    assert _reply("o que está rolando sobre tecnologia", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=tecnologia")
    assert _reply("me conta o que está rolando", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=brasil")
    assert _reply("o que está rolando hoje", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=brasil")
    assert "hoje" not in seen[-1].lower()
    assert _reply("o que está rolando quanto à economia", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=economia")
    assert "quanto" not in seen[-1].lower()
    assert _reply("me conta o que tá rolando quanto ao esporte", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=esporte")
    assert _reply("o que há de novo quanto à tecnologia", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=tecnologia")
    assert "quanto" not in seen[-1].lower()
    assert _reply("o que houve de novo quanto à economia", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=economia")
    assert _reply("notícias brasileiras", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=brasil")
    assert "brasileira" not in seen[-1].lower()
    assert _reply("notícia brasileira", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=brasil")
    assert _reply("as notícias brasileiras", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=brasil")
    assert "brasileira" not in seen[-1].lower()
    assert _reply("me dá as notícias brasileiras", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=brasil")
    assert _reply("quais as notícias brasileiras", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=brasil")
    assert _reply("notícias nacionais", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=brasil")
    assert "nacional" not in seen[-1].lower()
    assert _reply("notícias em recife", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=recife")
    assert "em%20recife" not in seen[-1].lower()
    assert _reply("notícias no rio", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=rio")
    assert "no%20rio" not in seen[-1].lower()
    assert _reply("me dá as notícias na bahia", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=bahia")
    assert "na%20bahia" not in seen[-1].lower()
    assert _reply("manchetes em recife", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=recife")
    assert "em%20recife" not in seen[-1].lower()
    assert _reply("manchetes no rio", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=rio")
    assert _reply("quais as manchetes em recife", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=recife")
    assert _reply("manchetes na geladeira", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert seen[-1].endswith("q=geladeira")
    before = len(seen)
    assert _reply("quais as notícias", fetch, tmp_path / "n.json") == "Sobre o que, Senhor."
    assert _reply("me atualiza", fetch, tmp_path / "n.json") is None
    assert _reply("me atualiza quanto à", fetch, tmp_path / "n.json") is None
    assert _reply("notícias quanto à", fetch, tmp_path / "n.json") == "Sobre o que, Senhor."
    assert _reply("manchetes quanto à", fetch, tmp_path / "n.json") == "Sobre o que, Senhor."
    assert _reply("plantão quanto à", fetch, tmp_path / "n.json") is None
    assert _reply("o que está rolando quanto à", fetch, tmp_path / "n.json") is None
    assert _reply("o que há de novo quanto à", fetch, tmp_path / "n.json") is None
    assert _reply("plantão médico", fetch, tmp_path / "n.json") is None
    assert _reply("as notícias", fetch, tmp_path / "n.json") == "Sobre o que, Senhor."
    assert _reply("o que está acontecendo", fetch, tmp_path / "n.json") == "Sobre o que, Senhor."
    assert _reply("o que há de novo na geladeira", fetch, tmp_path / "n.json") is None
    assert _reply("notícias", fetch, tmp_path / "n.json") == "Sobre o que, Senhor."
    assert len(seen) == before


def test_dollar_names_the_quote(tmp_path):
    quote = {"bid": "5.42"}
    seen = []

    def fetch(url):
        seen.append(url)
        if "CotacaoDolarDia" in url:
            assert "10-05-2026" in url
            return '{"value":[{"cotacaoVenda":%s}]}' % quote["bid"]
        if "news.google" in url:
            return (
                '<?xml version="1.0"?><rss><channel>'
                "<item><title>Dólar recua</title></item></channel></rss>"
            )
        return '{"AbstractText":"O dólar é a moeda dos Estados Unidos."}'

    path = tmp_path / "n.json"
    said = "O dólar está em 5 reais e 42 centavos, Senhor."
    assert _reply("qual a cotação do dólar", fetch, path) == said
    assert _reply("quanto está o dólar", fetch, path) == said
    assert _reply("dólar hoje", fetch, path) == said
    assert _reply("me fala a cotação do dólar", fetch, path) == said
    assert _reply("quanto tá o dólar agora", fetch, path) == said
    assert all("CotacaoDolarDia" in url for url in seen)
    quote["bid"] = "5.00"
    assert _reply("o dólar", fetch, path) == "O dólar está em 5 reais, Senhor."
    quote["bid"] = "5.01"
    assert _reply("qual o dólar", fetch, path) == (
        "O dólar está em 5 reais e 1 centavo, Senhor."
    )
    before = len(seen)
    assert _reply("cotação do euro", fetch, path) is None
    assert _reply("qual a cotação", fetch, path) is None
    assert len(seen) == before
    assert _reply("me explica o dólar", fetch, path) == (
        "O dólar é a moeda dos Estados Unidos, Senhor."
    )
    assert seen[-1].endswith("q=dolar")
    assert "USD-BRL" not in seen[-1]
    assert _reply("notícias sobre o dólar", fetch, path) == (
        "Nas notícias, Senhor. Dólar recua."
    )
    assert "news.google" in seen[-1]
    assert seen[-1].endswith("q=o%20dolar")

    def earlier(url):
        if "10-05-2026" in url:
            return '{"value":[]}'
        if "10-04-2026" in url:
            return '{"value":[{"cotacaoVenda":5.10}]}'
        raise AssertionError(url)

    assert _reply("dólar hoje", earlier, path) == (
        "O dólar está em 5 reais e 10 centavos, Senhor."
    )


def test_search_speaks_the_abstract(tmp_path):
    seen = []

    def fetch(url):
        seen.append(url)
        return '{"AbstractText":"O café é uma bebida. O resto fica de fora."}'

    path = tmp_path / "n.json"
    assert _reply("pesquise café", fetch, path) == (
        "O café é uma bebida, Senhor."
    )
    for said in (
        "pode pesquisar café",
        "pesquisa café",
        "me pesquisa o café",
        "quero pesquisar café",
        "pesquise sobre café",
        "busque sobre o café",
        "busca aí café",
        "pesquisa pra mim o café",
        "quero que pesquise café",
        "dá uma pesquisada no café",
        "pesquisa no google café",
        "google café",
        "pesquisa café no google",
        "me fala sobre o café",
        "o que é café",
        "explica sobre café",
        "me explica o café",
        "me fala do café",
        "quero saber sobre o café",
        "pesquisa no youtube café",
        "pesquisa café no youtube",
        "define café",
        "definição de café",
    ):
        assert _reply(said, fetch, path) == "O café é uma bebida, Senhor."
    assert all(url.endswith("q=cafe") for url in seen)
    assert _reply("pode pesquisar", fetch, path) == "O que devo procurar, Senhor?"
    assert _reply("google", fetch, path) == "O que devo procurar, Senhor?"
    assert _reply("o que é", fetch, path) == "O que devo procurar, Senhor?"
    assert _reply("me fala sobre", fetch, path) == "O que devo procurar, Senhor?"
    assert _reply("quero saber", fetch, path) == "O que devo procurar, Senhor?"
    assert _reply("quem é", fetch, path) == "O que devo procurar, Senhor?"
    assert _reply("define", fetch, path) == "O que devo procurar, Senhor?"
    assert _reply("pesquisa youtube", fetch, path) == "O que devo procurar, Senhor?"
    assert _reply("o que é você", fetch, path) is None
    assert _reply("quem é você", fetch, path) is None
    assert _reply("quem é santos dumont", fetch, path) == "O café é uma bebida, Senhor."
    assert seen[-1].endswith("q=santos%20dumont")


def test_search_without_abstract_asks_permission(tmp_path):
    def fetch(_url):
        return '{"AbstractText":""}'

    reply = _reply("busque reator arc", fetch, tmp_path / "n.json")
    assert reply.startswith("ACAO: xdg-open 'https://duckduckgo.com/?q=")


def test_reminder_roundtrip(tmp_path):
    path = tmp_path / "notes.json"

    def fetch(_url):
        raise AssertionError("lembrete não usa rede")

    assert _reply("anote entregar o projeto na sexta", fetch, path) == "Anotado, Senhor."
    assert _reply("anote comprar café", fetch, path) == "Anotado, Senhor."
    assert _reply("me lembre de voz do orion", fetch, path) == "Anotado, Senhor."
    assert _reply("me lembre comprar pão", fetch, path) == "Anotado, Senhor."
    saved = path.read_text(encoding="utf-8")
    assert '"text": "comprar pão"' in saved
    assert "de comprar" not in saved
    listed = _reply("meus lembretes", fetch, path)
    assert "comprar pão" in listed
    assert listed.index("entregar o projeto na sexta") < listed.index("comprar café")
    assert "comprar café" in listed
    assert "voz do orion" in listed
    assert _reply("anota aí comprar leite", fetch, path) == "Anotado, Senhor."
    assert '"text": "comprar leite"' in path.read_text(encoding="utf-8")
    assert "aí" not in path.read_text(encoding="utf-8")
    assert _reply("lembra de pagar a luz", fetch, path) == "Anotado, Senhor."
    assert '"text": "pagar a luz"' in path.read_text(encoding="utf-8")
    assert _reply("anota pra mim comprar pão", fetch, path) == "Anotado, Senhor."
    saved = path.read_text(encoding="utf-8")
    assert '"text": "comprar pão"' in saved
    assert "pra mim" not in saved
    assert _reply("anota isso comprar pão", fetch, path) == "Anotado, Senhor."
    assert _reply("não me deixa esquecer de ligar amanhã", fetch, path) == "Anotado, Senhor."
    saved = path.read_text(encoding="utf-8")
    assert '"text": "ligar amanhã"' in saved
    assert "esquecer" not in saved
    assert _reply("guarda nas notas comprar pão", fetch, path) == "Anotado, Senhor."
    assert '"text": "comprar pão"' in path.read_text(encoding="utf-8")
    assert _reply("guarda isso comprar pão", fetch, path) == "Anotado, Senhor."
    saved = path.read_text(encoding="utf-8")
    assert '"text": "comprar pão"' in saved
    assert "guarda isso" not in saved
    assert _reply("guarda isso nas notas ligar amanhã", fetch, path) == "Anotado, Senhor."
    saved = path.read_text(encoding="utf-8")
    assert '"text": "ligar amanhã"' in saved
    assert "nas notas" not in saved
    assert _reply("guarda isso", fetch, path) == "O que devo anotar, Senhor?"
    assert _reply("salva uma nota ligar amanhã", fetch, path) == "Anotado, Senhor."
    saved = path.read_text(encoding="utf-8")
    assert '"text": "ligar amanhã"' in saved
    assert "uma nota" not in saved
    assert _reply("coloca na nota pagar a luz", fetch, path) == "Anotado, Senhor."
    assert '"text": "pagar a luz"' in path.read_text(encoding="utf-8")
    assert _reply("anota na nota comprar pão", fetch, path) == "Anotado, Senhor."
    saved = path.read_text(encoding="utf-8")
    assert '"text": "comprar pão"' in saved
    assert "na nota" not in saved
    assert _reply("guarda nas notas", fetch, path) == "O que devo anotar, Senhor?"
    assert _reply("guarda o arquivo", fetch, path) is None
    assert _reply("anota que preciso comprar pão", fetch, path) == "Anotado, Senhor."
    saved = path.read_text(encoding="utf-8")
    assert '"text": "preciso comprar pão"' in saved
    assert "que preciso" not in saved
    assert _reply("anota que", fetch, path) == "O que devo anotar, Senhor?"
    assert _reply("anota isso", fetch, path) == "O que devo anotar, Senhor?"
    assert _reply("adiciona nas notas comprar pão", fetch, path) == "Anotado, Senhor."
    saved = path.read_text(encoding="utf-8")
    assert '"text": "comprar pão"' in saved
    assert "nas notas comprar" not in saved
    assert _reply("cria uma nota ligar amanhã", fetch, path) == "Anotado, Senhor."
    saved = path.read_text(encoding="utf-8")
    assert '"text": "ligar amanhã"' in saved
    assert "uma nota" not in saved
    assert _reply("não me deixa esquecer comprar pão", fetch, path) == "Anotado, Senhor."
    saved = path.read_text(encoding="utf-8")
    assert '"text": "comprar pão"' in saved
    assert "esquecer" not in saved
    assert _reply("cria uma nota", fetch, path) == "O que devo anotar, Senhor?"
    assert _reply("adiciona nas notas", fetch, path) == "O que devo anotar, Senhor?"
    assert _reply("novo lembrete", fetch, path) == "O que devo anotar, Senhor?"
    assert _reply("adiciona sal", fetch, path) is None
    assert _reply("cria uma imagem", fetch, path) is None
    assert _reply("bota o livro na mesa", fetch, path) is None
    assert _reply("lembrete comprar pão", fetch, path) == "Anotado, Senhor."
    saved = path.read_text(encoding="utf-8")
    assert '"text": "comprar pão"' in saved
    assert _reply("lembrete de comprar pão", fetch, path) == "Anotado, Senhor."
    saved = path.read_text(encoding="utf-8")
    assert '"text": "comprar pão"' in saved
    assert "de comprar" not in saved
    assert _reply("lembrete de", fetch, path) == "O que devo anotar, Senhor?"
    assert _reply("quero anotar ligar amanhã", fetch, path) == "Anotado, Senhor."
    saved = path.read_text(encoding="utf-8")
    assert '"text": "ligar amanhã"' in saved
    assert "quero anotar" not in saved
    assert _reply("não esquece comprar pão", fetch, path) == "Anotado, Senhor."
    saved = path.read_text(encoding="utf-8")
    assert '"text": "comprar pão"' in saved
    assert "esquece" not in saved
    assert _reply("anota amanhã comprar pão", fetch, path) == "Anotado, Senhor."
    saved = path.read_text(encoding="utf-8")
    assert '"text": "comprar pão"' in saved
    assert "amanhã comprar" not in saved
    assert _reply("anota para amanhã comprar pão", fetch, path) == "Anotado, Senhor."
    saved = path.read_text(encoding="utf-8")
    assert '"text": "comprar pão"' in saved
    assert "para amanhã" not in saved
    assert _reply("não me deixa esquecer de ligar amanhã", fetch, path) == "Anotado, Senhor."
    assert '"text": "ligar amanhã"' in path.read_text(encoding="utf-8")
    assert _reply("anota amanhã", fetch, path) == "O que devo anotar, Senhor?"
    assert _reply("não esquece", fetch, path) == "O que devo anotar, Senhor?"
    assert _reply("preciso anotar", fetch, path) == "O que devo anotar, Senhor?"
    assert _reply("pode anotar", fetch, path) == "O que devo anotar, Senhor?"
    assert _reply("quais são minhas notas", fetch, path).startswith("Lembretes, Senhor.")
    assert _reply("lista as notas", fetch, path).startswith("Lembretes, Senhor.")
    assert "pagar a luz" in _reply("quais são os lembretes", fetch, path)
    assert _reply("o que eu tenho anotado", fetch, path).startswith("Lembretes, Senhor.")
    assert _reply("mostra minhas notas", fetch, path).startswith("Lembretes, Senhor.")
    assert _reply("leia os lembretes", fetch, path).startswith("Lembretes, Senhor.")
    assert _reply("meus recados", fetch, path).startswith("Lembretes, Senhor.")
    assert _reply("liste os arquivos", fetch, path) is None


def test_note_query_is_only_the_search():
    from claude_agent_voice.house import note_query_of

    assert note_query_of("buscar nota projeto", "Nas notas, Senhor. entregar.") == "projeto"
    assert note_query_of("buscar nas notas projeto", "Nas notas, Senhor. entregar.") == "projeto"
    assert note_query_of("procure nas minhas notas projeto", "Nas notas, Senhor. entregar.") == "projeto"
    assert note_query_of("notas do projeto", "Nas notas, Senhor. entregar.") == "projeto"
    assert note_query_of("tem nota sobre voz", "Nas notas, Senhor. revisar.") == "voz"
    assert note_query_of("pesquise nas notas o projeto", "Nas notas, Senhor. entregar.") == "projeto"
    assert note_query_of("buscar o projeto nas notas", "Nas notas, Senhor. entregar.") == "projeto"
    assert note_query_of("o que eu anotei sobre projeto", "Nas notas, Senhor. entregar.") == "projeto"
    assert note_query_of("onde está a nota do projeto", "Nas notas, Senhor. entregar.") == "projeto"
    assert note_query_of(
        "tem alguma coisa sobre projeto nas notas", "Nas notas, Senhor. entregar."
    ) == "projeto"
    assert note_query_of(
        "procure alguma coisa sobre voz nas notas", "Nas notas, Senhor. revisar."
    ) == "voz"
    assert note_query_of("o que eu anotei", "Lembretes, Senhor. entregar.") == ""
    assert note_query_of("mostra a última nota", "A última nota, Senhor. revisar.") == ""
    assert note_query_of("mostra a primeira nota", "A primeira nota, Senhor. entregar.") == ""
    assert note_query_of("mostra a nota do projeto", "Nas notas, Senhor. entregar.") == "projeto"
    assert note_query_of("voz", "Nas notas, Senhor. revisar o projeto de voz.") == "voz"
    assert note_query_of("buscar nota marte", "Não há nota com isso, Senhor.") == "marte"
    assert note_query_of("buscar nota", "O que devo buscar nas notas, Senhor?") == ""
    assert note_query_of("que horas são", "São 15 horas, Senhor.") == ""


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
    assert _reply("buscar nas notas projeto", fetch, path) == (
        "Nas notas, Senhor. entregar o projeto na sexta."
    )
    assert _reply("procura nas notas projeto", fetch, path) == (
        "Nas notas, Senhor. entregar o projeto na sexta."
    )
    assert _reply("procure nas minhas notas projeto", fetch, path) == (
        "Nas notas, Senhor. entregar o projeto na sexta."
    )
    assert _reply("notas do projeto", fetch, path) == (
        "Nas notas, Senhor. entregar o projeto na sexta."
    )
    voice = tmp_path / "voice.json"
    voice.write_text(
        '[{"text": "revisar o projeto de voz", "at": "a"}]',
        encoding="utf-8",
    )
    assert _reply("tem nota sobre voz", fetch, voice) == (
        "Nas notas, Senhor. revisar o projeto de voz."
    )
    assert _reply("nas notas projeto", fetch, path) == (
        "Nas notas, Senhor. entregar o projeto na sexta."
    )
    assert _reply("pesquise nas notas o projeto", fetch, path) == (
        "Nas notas, Senhor. entregar o projeto na sexta."
    )
    assert _reply("buscar o projeto nas notas", fetch, path) == (
        "Nas notas, Senhor. entregar o projeto na sexta."
    )
    assert _reply("procura projeto nas notas", fetch, path) == (
        "Nas notas, Senhor. entregar o projeto na sexta."
    )
    assert _reply("busca nas minhas notas a voz", fetch, voice) == (
        "Nas notas, Senhor. revisar o projeto de voz."
    )
    assert _reply("o que eu anotei", fetch, path).startswith("Lembretes, Senhor.")
    assert _reply("o que eu anotei sobre projeto", fetch, path) == (
        "Nas notas, Senhor. entregar o projeto na sexta."
    )
    assert _reply("nas minhas notas tem projeto", fetch, path) == (
        "Nas notas, Senhor. entregar o projeto na sexta."
    )
    assert _reply("tem alguma coisa sobre projeto nas notas", fetch, path) == (
        "Nas notas, Senhor. entregar o projeto na sexta."
    )
    assert _reply("procure alguma coisa sobre voz nas notas", fetch, voice) == (
        "Nas notas, Senhor. revisar o projeto de voz."
    )
    assert _reply("alguma nota sobre projeto", fetch, path) == (
        "Nas notas, Senhor. entregar o projeto na sexta."
    )
    assert _reply("tem alguma coisa nas notas", fetch, path) == (
        "O que devo buscar nas notas, Senhor?"
    )
    assert _reply("buscar nota marte", fetch, path) == "Não há nota com isso, Senhor."
    assert _reply("cadê a nota do projeto", fetch, path) == (
        "Nas notas, Senhor. entregar o projeto na sexta."
    )
    assert _reply("onde anotei o projeto", fetch, path) == (
        "Nas notas, Senhor. entregar o projeto na sexta."
    )
    assert _reply("onde está a nota do projeto", fetch, path) == (
        "Nas notas, Senhor. entregar o projeto na sexta."
    )
    assert _reply("onde ficou a nota da voz", fetch, voice) == (
        "Nas notas, Senhor. revisar o projeto de voz."
    )
    assert _reply("onde está a nota", fetch, path) == "O que devo buscar nas notas, Senhor?"
    assert _reply("lembrete do projeto", fetch, path) == (
        "Nas notas, Senhor. entregar o projeto na sexta."
    )
    assert "do projeto" not in path.read_text(encoding="utf-8")
    assert _reply("procura lembrete do projeto", fetch, path) == (
        "Nas notas, Senhor. entregar o projeto na sexta."
    )
    assert _reply("onde eu deixei a nota do projeto", fetch, path) == (
        "Nas notas, Senhor. entregar o projeto na sexta."
    )
    assert _reply("procura o recado da voz", fetch, voice) == (
        "Nas notas, Senhor. revisar o projeto de voz."
    )
    latest = tmp_path / "latest.json"
    latest.write_text(
        '[{"text": "entregar o projeto na sexta"}, {"text": "revisar o projeto de voz"}]',
        encoding="utf-8",
    )
    heard = "A última nota, Senhor. revisar o projeto de voz."
    for phrase in (
        "mostra a última nota",
        "última nota",
        "qual foi a última nota",
        "lê a última nota",
        "lembrete mais recente",
        "o último recado",
        "me mostra a nota mais recente",
        "me conta a última nota",
        "me diz a última nota",
        "me fala o último lembrete",
    ):
        assert _reply(phrase, fetch, latest) == heard
    assert "mais recente" not in latest.read_text(encoding="utf-8")
    empty = tmp_path / "empty.json"
    empty.write_text("[]", encoding="utf-8")
    assert _reply("mostra a última nota", fetch, empty) == "Nada anotado, Senhor."
    assert _reply("mostra as notas", fetch, latest).startswith("Lembretes, Senhor.")
    assert "entregar o projeto na sexta" in _reply("mostra as notas", fetch, latest)
    listed_late = _reply("as últimas notas", fetch, latest)
    assert listed_late.startswith("Lembretes, Senhor.")
    assert "entregar o projeto na sexta" in listed_late
    assert "revisar o projeto de voz" in listed_late
    assert _reply("os últimos lembretes", fetch, latest) == listed_late
    assert _reply("me mostra as últimas notas", fetch, latest) == listed_late
    assert _reply("quais são as últimas notas", fetch, latest) == listed_late
    assert _reply("as últimas notas", fetch, empty) == "Nada anotado, Senhor."
    assert _reply("mostra a nota do projeto", fetch, path) == (
        "Nas notas, Senhor. entregar o projeto na sexta."
    )
    assert _reply("me mostra a nota do projeto", fetch, path) == (
        "Nas notas, Senhor. entregar o projeto na sexta."
    )
    assert _reply("lê a nota do projeto", fetch, path) == (
        "Nas notas, Senhor. entregar o projeto na sexta."
    )
    assert _reply("o lembrete do projeto", fetch, path) == (
        "Nas notas, Senhor. entregar o projeto na sexta."
    )
    assert _reply("nota do projeto", fetch, path) == (
        "Nas notas, Senhor. entregar o projeto na sexta."
    )
    assert _reply("mostra o recado da voz", fetch, voice) == (
        "Nas notas, Senhor. revisar o projeto de voz."
    )
    assert _reply("recado da voz", fetch, voice) == (
        "Nas notas, Senhor. revisar o projeto de voz."
    )
    assert _reply("mostra a nota", fetch, path) == "O que devo buscar nas notas, Senhor?"
    assert _reply("me mostra as notas", fetch, latest).startswith("Lembretes, Senhor.")
    assert "revisar o projeto de voz" in _reply("me mostra as notas", fetch, latest)
    assert _reply("mostra a primeira nota", fetch, latest) == (
        "A primeira nota, Senhor. entregar o projeto na sexta."
    )
    assert _reply("nota mais antiga", fetch, latest) == (
        "A primeira nota, Senhor. entregar o projeto na sexta."
    )
    assert _reply("o lembrete mais antigo", fetch, latest) == (
        "A primeira nota, Senhor. entregar o projeto na sexta."
    )
    assert _reply("lembrete mais antigo", fetch, latest) == (
        "A primeira nota, Senhor. entregar o projeto na sexta."
    )
    assert _reply("me diz a primeira nota", fetch, latest) == (
        "A primeira nota, Senhor. entregar o projeto na sexta."
    )
    assert _reply("me conta o primeiro lembrete", fetch, latest) == (
        "A primeira nota, Senhor. entregar o projeto na sexta."
    )
    assert _reply("me fala a nota mais antiga", fetch, latest) == (
        "A primeira nota, Senhor. entregar o projeto na sexta."
    )
    assert "primeira" not in latest.read_text(encoding="utf-8")
    assert "mais antigo" not in latest.read_text(encoding="utf-8")
    assert _reply("as primeiras notas", fetch, latest) == listed_late
    assert _reply("os primeiros recados", fetch, latest) == listed_late
    assert _reply("quantas notas eu tenho", fetch, latest) == "São 2 notas, Senhor."
    assert _reply("tem quantas notas", fetch, latest) == "São 2 notas, Senhor."
    assert _reply("tem quantos lembretes", fetch, latest) == "São 2 notas, Senhor."
    assert _reply("tem quantos recados", fetch, empty) == "Nada anotado, Senhor."
    assert _reply("me diz quantas notas", fetch, latest) == "São 2 notas, Senhor."
    assert _reply("me fala quantas notas eu tenho", fetch, latest) == "São 2 notas, Senhor."
    assert _reply("tem quantos lembretes eu tenho", fetch, latest) == "São 2 notas, Senhor."
    assert _reply("me conta quantos recados", fetch, empty) == "Nada anotado, Senhor."
    assert _reply("eu tenho quantas notas", fetch, latest) == "São 2 notas, Senhor."
    assert _reply("eu tenho quantos lembretes", fetch, latest) == "São 2 notas, Senhor."
    assert _reply("quantas notas tenho eu", fetch, latest) == "São 2 notas, Senhor."
    assert _reply("eu tenho quantas notas", fetch, empty) == "Nada anotado, Senhor."
    assert "quantas" not in latest.read_text(encoding="utf-8")
    assert _reply("quantas notas", fetch, empty) == "Nada anotado, Senhor."
    assert _reply("mostra a primeira nota", fetch, empty) == "Nada anotado, Senhor."
    one = tmp_path / "one.json"
    one.write_text('[{"text": "entregar o projeto na sexta"}]', encoding="utf-8")
    assert _reply("quantas notas", fetch, one) == "Uma nota, Senhor."
    assert "do projeto" not in path.read_text(encoding="utf-8")
    assert _reply("lembrete do projeto", fetch, path) == (
        "Nas notas, Senhor. entregar o projeto na sexta."
    )
    assert _reply("procura lembrete", fetch, path) == "O que devo buscar nas notas, Senhor?"
    assert _reply("tem recado sobre projeto", fetch, path) == (
        "Nas notas, Senhor. entregar o projeto na sexta."
    )
    assert _reply("cadê a nota", fetch, path) == "O que devo buscar nas notas, Senhor?"
    voice_hit = _reply("onde eu anotei a voz", fetch, voice)
    assert voice_hit == "Nas notas, Senhor. revisar o projeto de voz."


def test_air_names_the_city(tmp_path):
    quote = {"index": 34}
    seen = []

    def fetch(url):
        seen.append(url)
        if "geocoding" in url:
            assert "recife" in url.lower() or "curitiba" in url.lower()
            name = "Recife" if "recife" in url.lower() else "Curitiba"
            return '{"results":[{"latitude":-8.0,"longitude":-34.9,"name":"%s"}]}' % name
        assert "air-quality" in url
        assert "european_aqi" in url
        assert "temperature_2m" not in url
        return '{"current":{"european_aqi":%s}}' % quote["index"]

    path = tmp_path / "n.json"
    assert _reply("qualidade do ar", fetch, path) == "De qual lugar, Senhor."
    assert _reply("me fala a qualidade do ar", fetch, path) == "De qual lugar, Senhor."
    assert seen == []
    assert _reply("qualidade do ar em recife", fetch, path) == (
        "Em Recife, qualidade do ar razoável, índice 34, Senhor."
    )
    assert "name=recife" in seen[-2]
    assert "air-quality" in seen[-1]
    assert _reply("me fala a qualidade do ar em curitiba", fetch, path) == (
        "Em Curitiba, qualidade do ar razoável, índice 34, Senhor."
    )
    assert "name=curitiba" in seen[-2]
    quote["index"] = 0
    assert _reply("qualidade do ar agora em recife", fetch, path) == (
        "Em Recife, qualidade do ar boa, índice 0, Senhor."
    )
    quote["index"] = 101
    assert _reply("qual a qualidade do ar em recife", fetch, path) == (
        "Em Recife, qualidade do ar péssima, índice 101, Senhor."
    )
    before = len(seen)
    assert _reply("qualidade do ar amanhã em recife", fetch, path) is None
    assert len(seen) == before


def test_visibility_names_the_city(tmp_path):
    quote = {"meters": 18040, "tomorrow": 11361.67}
    seen = []

    def fetch(url):
        seen.append(url)
        if "geocoding" in url:
            assert "recife" in url.lower() or "curitiba" in url.lower()
            name = "Recife" if "recife" in url.lower() else "Curitiba"
            return '{"results":[{"latitude":-8.0,"longitude":-34.9,"name":"%s"}]}' % name
        if "visibility_mean" in url:
            assert "forecast_days=2" in url
            assert "temperature_2m" not in url
            tomorrow = "null" if quote["tomorrow"] is None else quote["tomorrow"]
            return '{"daily":{"visibility_mean":[18326.67,%s]}}' % tomorrow
        assert "current=visibility" in url
        assert "temperature_2m" not in url
        return '{"current":{"visibility":%s}}' % quote["meters"]

    path = tmp_path / "n.json"
    assert _reply("visibilidade", fetch, path) == "De qual lugar, Senhor."
    assert _reply("me fala a visibilidade", fetch, path) == "De qual lugar, Senhor."
    assert _reply("visibilidade amanhã", fetch, path) == "De qual lugar, Senhor."
    assert _reply("visibilidade do projeto", fetch, path) is None
    assert seen == []
    assert _reply("visibilidade em recife", fetch, path) == (
        "Em Recife, visibilidade de 18 quilômetros, Senhor."
    )
    assert "name=recife" in seen[-2]
    assert "current=visibility" in seen[-1]
    quote["meters"] = 9440
    assert _reply("me fala a visibilidade em curitiba", fetch, path) == (
        "Em Curitiba, visibilidade de 9 quilômetros, Senhor."
    )
    assert "name=curitiba" in seen[-2]
    quote["meters"] = 0
    assert _reply("qual a visibilidade agora em recife", fetch, path) == (
        "Em Recife, visibilidade de 0 metros, Senhor."
    )
    quote["meters"] = 1
    assert _reply("visibilidade hoje em recife", fetch, path) == (
        "Em Recife, visibilidade de 1 metro, Senhor."
    )
    quote["meters"] = 1000
    assert _reply("me diz a visibilidade em recife", fetch, path) == (
        "Em Recife, visibilidade de 1 quilômetro, Senhor."
    )
    quote["meters"] = 1500
    assert _reply("visibilidade de recife", fetch, path) == (
        "Em Recife, visibilidade de 2 quilômetros, Senhor."
    )
    assert _reply("visibilidade amanhã em recife", fetch, path) == (
        "Amanhã em Recife, visibilidade de 11 quilômetros, Senhor."
    )
    assert "visibility_mean" in seen[-1]
    assert "forecast_days=2" in seen[-1]
    quote["tomorrow"] = None
    assert _reply("visibilidade para amanhã em curitiba", fetch, path) == (
        "Não alcancei o clima, Senhor."
    )


def test_dew_names_the_city(tmp_path):
    quote = {"graus": 20.9, "tomorrow": 21.8}
    seen = []

    def fetch(url):
        seen.append(url)
        if "geocoding" in url:
            assert "recife" in url.lower() or "curitiba" in url.lower()
            name = "Recife" if "recife" in url.lower() else "Curitiba"
            return '{"results":[{"latitude":-8.0,"longitude":-34.9,"name":"%s"}]}' % name
        if "dew_point_2m_mean" in url:
            assert "forecast_days=2" in url
            assert "temperature_2m" not in url
            tomorrow = "null" if quote["tomorrow"] is None else quote["tomorrow"]
            return '{"daily":{"dew_point_2m_mean":[20.4,%s]}}' % tomorrow
        assert "current=dew_point_2m" in url
        assert "temperature_2m" not in url
        return '{"current":{"dew_point_2m":%s}}' % quote["graus"]

    path = tmp_path / "n.json"
    assert _reply("ponto de orvalho", fetch, path) == "De qual lugar, Senhor."
    assert _reply("me fala o ponto de orvalho", fetch, path) == "De qual lugar, Senhor."
    assert _reply("ponto de orvalho amanhã", fetch, path) == "De qual lugar, Senhor."
    assert _reply("orvalho", fetch, path) is None
    assert _reply("ponto de orvalho do projeto", fetch, path) is None
    assert seen == []
    assert _reply("ponto de orvalho em recife", fetch, path) == (
        "Em Recife, ponto de orvalho de 21 graus, Senhor."
    )
    assert "name=recife" in seen[-2]
    assert "current=dew_point_2m" in seen[-1]
    quote["graus"] = 12.9
    assert _reply("me fala o ponto de orvalho em curitiba", fetch, path) == (
        "Em Curitiba, ponto de orvalho de 13 graus, Senhor."
    )
    assert "name=curitiba" in seen[-2]
    quote["graus"] = 0
    assert _reply("qual o ponto de orvalho agora em recife", fetch, path) == (
        "Em Recife, ponto de orvalho de 0 graus, Senhor."
    )
    quote["graus"] = -3.2
    assert _reply("ponto de orvalho hoje em recife", fetch, path) == (
        "Em Recife, ponto de orvalho de menos 3 graus, Senhor."
    )
    assert _reply("ponto de orvalho amanhã em recife", fetch, path) == (
        "Amanhã em Recife, ponto de orvalho de 22 graus, Senhor."
    )
    assert "dew_point_2m_mean" in seen[-1]
    assert "forecast_days=2" in seen[-1]
    quote["tomorrow"] = None
    assert _reply("ponto de orvalho para amanhã em curitiba", fetch, path) == (
        "Não alcancei o clima, Senhor."
    )


def test_dew_follow_up_keeps_the_field(tmp_path, monkeypatch):
    from claude_agent_voice.hud import make_reply_fn
    from claude_agent_voice.personas import get_persona
    from claude_agent_voice.settings import Settings

    seen = []

    def fake_weather(place, _fetch, day="", field=""):
        seen.append((place, field, day))
        when = "Amanhã em" if day == "amanha" else "Em"
        return f"{when} {place}, ponto de orvalho de 21 graus, Senhor."

    monkeypatch.setattr("claude_agent_voice.house._weather", fake_weather)
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
    assert reply("ponto de orvalho", []) == "De qual lugar, Senhor."
    assert reply("recife", []) == "Em recife, ponto de orvalho de 21 graus, Senhor."
    assert seen == [("recife", "orvalho", "")]
    assert reply("ponto de orvalho amanhã", []) == "De qual lugar, Senhor."
    assert reply("curitiba", []) == (
        "Amanhã em curitiba, ponto de orvalho de 21 graus, Senhor."
    )
    assert seen[-1] == ("curitiba", "orvalho", "amanha")


def test_visibility_follow_up_keeps_the_field(tmp_path, monkeypatch):
    from claude_agent_voice.hud import make_reply_fn
    from claude_agent_voice.personas import get_persona
    from claude_agent_voice.settings import Settings

    seen = []

    def fake_weather(place, _fetch, day="", field=""):
        seen.append((place, field, day))
        when = "Amanhã em" if day == "amanha" else "Em"
        return f"{when} {place}, visibilidade de 18 quilômetros, Senhor."

    monkeypatch.setattr("claude_agent_voice.house._weather", fake_weather)
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
    assert reply("visibilidade", []) == "De qual lugar, Senhor."
    assert reply("recife", []) == "Em recife, visibilidade de 18 quilômetros, Senhor."
    assert seen == [("recife", "visibilidade", "")]
    assert reply("visibilidade amanhã", []) == "De qual lugar, Senhor."
    assert reply("curitiba", []) == (
        "Amanhã em curitiba, visibilidade de 18 quilômetros, Senhor."
    )
    assert seen[-1] == ("curitiba", "visibilidade", "amanha")


def test_air_follow_up_keeps_the_field(tmp_path, monkeypatch):
    from claude_agent_voice.hud import make_reply_fn
    from claude_agent_voice.personas import get_persona
    from claude_agent_voice.settings import Settings

    seen = []

    def fake_weather(place, _fetch, day="", field=""):
        seen.append((place, field, day))
        return f"Em {place}, qualidade do ar boa, índice 12, Senhor."

    monkeypatch.setattr("claude_agent_voice.house._weather", fake_weather)
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
    assert reply("qualidade do ar", []) == "De qual lugar, Senhor."
    assert reply("recife", []) == "Em recife, qualidade do ar boa, índice 12, Senhor."
    assert seen == [("recife", "ar", "")]


def test_forget_removes_only_the_newest(tmp_path):
    def fetch(_url):
        raise AssertionError("desfazer não usa rede")

    path = tmp_path / "n.json"
    path.write_text(
        '[{"text": "entregar o projeto"}, {"text": "revisar a voz"}]',
        encoding="utf-8",
    )
    assert _reply("apaga a última nota", fetch, path) == "Desfeito, Senhor. revisar a voz."
    left = path.read_text(encoding="utf-8")
    assert "revisar a voz" not in left
    assert "entregar o projeto" in left
    assert _reply("a última nota", fetch, path) == (
        "A última nota, Senhor. entregar o projeto."
    )
    assert _reply("desfaz a última nota", fetch, path) == (
        "Desfeito, Senhor. entregar o projeto."
    )
    assert _reply("apaga o último lembrete", fetch, path) == "Nada para desfazer, Senhor."
    assert _reply("esquece", fetch, path) == "O que devo anotar, Senhor?"


def test_camera_and_image_are_refused(tmp_path):
    def fetch(_url):
        raise AssertionError("recusa não usa rede")

    path = tmp_path / "n.json"
    assert _reply("ligue a câmera", fetch, path) == "Não uso câmera, Senhor."
    assert _reply("gere uma imagem do reator", fetch, path) == (
        "Ainda não gero imagem aqui, Senhor."
    )


def test_whatsapp_number_keeps_spaces_and_dashes():
    from claude_agent_voice.house import whatsapp_number

    assert whatsapp_number("11 99999-8888") == "11999998888"
    assert whatsapp_number("(11) 99999-8888") == "11999998888"
    assert whatsapp_number("+55 11 99999-8888") == "5511999998888"
    assert whatsapp_number("5511999998888") == "5511999998888"
    assert whatsapp_number("cheguei") == ""


def test_whatsapp_is_a_link_with_permission(tmp_path):
    def fetch(_url):
        raise AssertionError("whatsapp não usa rede")

    path = tmp_path / "n.json"
    reply = _reply("mande whatsapp para 5511999998888 dizendo cheguei", fetch, path)
    assert reply.startswith("ACAO: xdg-open 'https://wa.me/5511999998888?text=cheguei'")
    spaced = _reply("mande whatsapp para (11) 99999-8888 dizendo cheguei", fetch, path)
    assert spaced.startswith("ACAO: xdg-open 'https://wa.me/11999998888?text=cheguei'")
    assert _reply("mande um whatsapp", fetch, path) == "Diga o número, Senhor."
    assert _reply("manda um zap", fetch, path) == "Diga o número, Senhor."
    assert _reply("mande whatsapp para 5511999998888", fetch, path) == (
        "O que devo escrever, Senhor?"
    )
    oi = _reply("manda um oi no zap para 11988887777", fetch, path)
    assert oi.startswith("ACAO: xdg-open 'https://wa.me/11988887777?text=oi'")
    casa = _reply("manda vou para casa no zap para 11988887777", fetch, path)
    assert "text=vou%20para%20casa" in casa
    assert "11988887777" in casa
    depois = _reply("manda zap para 11988887777 oi", fetch, path)
    assert depois.startswith("ACAO: xdg-open 'https://wa.me/11988887777?text=oi'")
    dito = _reply("manda mensagem para 11988887777 oi", fetch, path)
    assert dito.startswith("ACAO: xdg-open 'https://wa.me/11988887777?text=oi'")
    envia = _reply("envia uma mensagem para 11988887777 dizendo cheguei", fetch, path)
    assert envia.startswith("ACAO: xdg-open 'https://wa.me/11988887777?text=cheguei'")
    assert _reply("manda mensagem", fetch, path) == "Diga o número, Senhor."
    assert _reply("tenho uma mensagem", fetch, path) is None


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
    assert reply("11 99999-8888", []) == "O que devo escrever, Senhor?"
    assert "11999998888" in reply("na porta", [])
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

    def fake_weather(place, _fetch, day="", field=""):
        if field == "umidade":
            when = "Amanhã em" if day == "amanha" else "Em"
            return f"{when} {place}, umidade de 80 por cento, Senhor."
        if field == "sensacao":
            when = "Amanhã em" if day == "amanha" else "Em"
            return f"{when} {place}, sensação de 14 graus, Senhor."
        if field == "vento":
            when = "Amanhã em" if day == "amanha" else "Em"
            return f"{when} {place}, vento de 18 quilômetros por hora, Senhor."
        if field == "nascer":
            when = "Amanhã em" if day == "amanha" else "Em"
            return f"{when} {place}, o sol nasce às 5 horas e 12 minutos, Senhor."
        if field == "por":
            when = "Amanhã em" if day == "amanha" else "Em"
            return f"{when} {place}, o sol se põe às 17 horas e 40 minutos, Senhor."
        if field == "uv":
            when = "Amanhã em" if day == "amanha" else "Em"
            return f"{when} {place}, índice UV de 11, Senhor."
        if field == "pressao":
            when = "Amanhã em" if day == "amanha" else "Em"
            return f"{when} {place}, pressão de 1013 milibares, Senhor."
        if field == "chance":
            when = "Amanhã em" if day == "amanha" else "Em"
            return f"{when} {place}, chance de chuva de 40 por cento, Senhor."
        if field == "semana":
            return f"Em {place}, na semana, de 14 a 29 graus, Senhor."
        if field == "fim":
            return f"Em {place}, no fim de semana, de 12 a 28 graus, Senhor."
        if field == "maxima":
            when = "Amanhã em" if day == "amanha" else "Em"
            return f"{when} {place}, máxima de 31 graus, Senhor."
        if field == "minima":
            when = "Amanhã em" if day == "amanha" else "Em"
            return f"{when} {place}, mínima de 18 graus, Senhor."
        if day == "depois":
            return f"Depois de amanhã em {place}, máxima de 31 graus, nublado, Senhor."
        if day == "amanha":
            return f"Amanhã em {place}, máxima de 27 graus, nublado, Senhor."
        return f"Em {place}, 19 graus, nublado, Senhor."

    monkeypatch.setattr("claude_agent_voice.house._weather", fake_weather)
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
    assert reply("tempo para amanhã", []) == "De qual lugar, Senhor."
    assert reply("aí", []) == "De qual lugar, Senhor."
    assert reply("Curitiba", []) == "Amanhã em Curitiba, máxima de 27 graus, nublado, Senhor."
    assert reply("vai chover amanhã", []) == "De qual lugar, Senhor."
    assert "15 horas" in reply("que horas são", [])
    assert reply("qual o tempo", []) == "De qual lugar, Senhor."
    assert reply("Recife", []) == "Em Recife, 19 graus, nublado, Senhor."
    assert reply("tempo para amanhã", []) == "De qual lugar, Senhor."
    assert reply("Curitiba hoje", []) == "Em Curitiba, 19 graus, nublado, Senhor."
    assert reply("qual o tempo", []) == "De qual lugar, Senhor."
    assert reply("amanhã em Curitiba", []) == (
        "Amanhã em Curitiba, máxima de 27 graus, nublado, Senhor."
    )
    assert reply("qual a previsão para amanhã", []) == "De qual lugar, Senhor."
    assert reply("Curitiba", []) == "Amanhã em Curitiba, máxima de 27 graus, nublado, Senhor."
    assert reply("umidade", []) == "De qual lugar, Senhor."
    assert reply("Recife", []) == "Em Recife, umidade de 80 por cento, Senhor."
    assert reply("qual o tempo", []) == "De qual lugar, Senhor."
    assert reply("Recife", []) == "Em Recife, 19 graus, nublado, Senhor."
    assert reply("sensação térmica", []) == "De qual lugar, Senhor."
    assert reply("Curitiba", []) == "Em Curitiba, sensação de 14 graus, Senhor."
    assert reply("qual a sensação", []) == "De qual lugar, Senhor."
    assert reply("Recife", []) == "Em Recife, sensação de 14 graus, Senhor."
    assert reply("vento", []) == "De qual lugar, Senhor."
    assert reply("Recife", []) == "Em Recife, vento de 18 quilômetros por hora, Senhor."
    assert reply("nascer do sol", []) == "De qual lugar, Senhor."
    assert reply("Recife", []) == "Em Recife, o sol nasce às 5 horas e 12 minutos, Senhor."
    assert reply("pôr do sol amanhã", []) == "De qual lugar, Senhor."
    assert reply("Curitiba", []) == (
        "Amanhã em Curitiba, o sol se põe às 17 horas e 40 minutos, Senhor."
    )
    assert reply("índice uv", []) == "De qual lugar, Senhor."
    assert reply("Recife", []) == "Em Recife, índice UV de 11, Senhor."
    assert reply("pressão atmosférica", []) == "De qual lugar, Senhor."
    assert reply("Curitiba", []) == "Em Curitiba, pressão de 1013 milibares, Senhor."
    assert reply("qual a máxima", []) == "De qual lugar, Senhor."
    assert reply("Recife", []) == "Em Recife, máxima de 31 graus, Senhor."
    assert reply("qual o tempo", []) == "De qual lugar, Senhor."
    assert reply("Recife", []) == "Em Recife, 19 graus, nublado, Senhor."
    assert reply("mínima amanhã", []) == "De qual lugar, Senhor."
    assert reply("Curitiba", []) == "Amanhã em Curitiba, mínima de 18 graus, Senhor."
    assert reply("me fala a máxima", []) == "De qual lugar, Senhor."
    assert reply("Recife", []) == "Em Recife, máxima de 31 graus, Senhor."
    assert reply("máxima para amanhã", []) == "De qual lugar, Senhor."
    assert reply("Recife", []) == "Amanhã em Recife, máxima de 31 graus, Senhor."
    assert reply("umidade amanhã", []) == "De qual lugar, Senhor."
    assert reply("Recife", []) == "Amanhã em Recife, umidade de 80 por cento, Senhor."
    assert reply("vento para amanhã", []) == "De qual lugar, Senhor."
    assert reply("Curitiba", []) == (
        "Amanhã em Curitiba, vento de 18 quilômetros por hora, Senhor."
    )
    assert reply("sensação térmica amanhã", []) == "De qual lugar, Senhor."
    assert reply("Recife", []) == "Amanhã em Recife, sensação de 14 graus, Senhor."
    assert reply("pressão amanhã", []) == "De qual lugar, Senhor."
    assert reply("Curitiba", []) == "Amanhã em Curitiba, pressão de 1013 milibares, Senhor."
    assert reply("chance de chuva", []) == "De qual lugar, Senhor."
    assert reply("Recife", []) == "Em Recife, chance de chuva de 40 por cento, Senhor."
    assert reply("chance de chuva amanhã", []) == "De qual lugar, Senhor."
    assert reply("Curitiba", []) == (
        "Amanhã em Curitiba, chance de chuva de 40 por cento, Senhor."
    )
    assert reply("clima para a semana", []) == "De qual lugar, Senhor."
    assert reply("Curitiba", []) == "Em Curitiba, na semana, de 14 a 29 graus, Senhor."
    assert reply("clima para o fim de semana", []) == "De qual lugar, Senhor."
    assert reply("Recife", []) == "Em Recife, no fim de semana, de 12 a 28 graus, Senhor."
    assert reply("tempo para depois de amanhã", []) == "De qual lugar, Senhor."
    assert reply("Recife", []) == (
        "Depois de amanhã em Recife, máxima de 31 graus, nublado, Senhor."
    )


def test_typed_search_keeps_orion_as_the_subject(monkeypatch):
    from claude_agent_voice.hud import HudSession, make_reply_fn, take_turn
    from claude_agent_voice.personas import get_persona
    from claude_agent_voice.settings import Settings
    from claude_agent_voice.wake import WakeGate

    seen = []

    def fake_search(query, _fetch):
        seen.append(query)
        return f"Achei {query}, Senhor."

    monkeypatch.setattr("claude_agent_voice.house._search", fake_search)
    persona = get_persona("orion")
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
        persona,
        lambda: WHEN,
    )
    session = HudSession(
        persona=persona,
        gate=WakeGate(wake_words=persona.wake_words, window_s=30),
    )
    result = take_turn(session, "busque Orion", 10.0, reply, enforce_wake=False)
    assert result.reply == "Achei orion, Senhor."
    assert seen == ["orion"]


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
    assert reply("guarda isso", []) == "O que devo anotar, Senhor?"
    assert reply("ligar amanhã", []) == "Anotado, Senhor."
    assert "ligar amanhã" in notes.read_text(encoding="utf-8")
    assert reply("lembrete de", []) == "O que devo anotar, Senhor?"
    assert reply("pagar a luz", []) == "Anotado, Senhor."
    assert '"text": "pagar a luz"' in notes.read_text(encoding="utf-8")
    assert reply("buscar nota", []) == "O que devo buscar nas notas, Senhor?"
    assert "comprar café" in reply("café", [])


def test_network_failure_is_spoken(tmp_path):
    def fetch(_url):
        raise TimeoutError("off")

    assert _reply("noticias de hoje", fetch, tmp_path / "n.json") == (
        "Não alcancei isso agora, Senhor."
    )
