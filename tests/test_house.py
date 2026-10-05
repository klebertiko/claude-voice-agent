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
    assert _reply("me fala o tempo", fetch, path) == "De qual lugar, Senhor."
    assert _reply("me diz o clima", fetch, path) == "De qual lugar, Senhor."
    assert _reply("temperatura agora", fetch, path) == "De qual lugar, Senhor."
    assert _reply("qual a temperatura agora", fetch, path) == "De qual lugar, Senhor."
    assert _reply("tá quanto", fetch, path) == "De qual lugar, Senhor."
    assert _reply("tem sol", fetch, path) == "De qual lugar, Senhor."
    assert _reply("vai gear", fetch, path) == "De qual lugar, Senhor."
    assert _reply("clima para a semana", fetch, path) == "De qual lugar, Senhor."


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
        "Em São Paulo, 22 graus, quase limpo, Senhor."
    )
    assert "name=curitiba" in seen[-2]
    assert "semana" not in seen[-2]
    assert "daily=" not in seen[-1]


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
    before = len(seen)
    assert _reply("o que aconteceu", fetch, tmp_path / "n.json") == "Sobre o que, Senhor."
    assert len(seen) == before
    assert _reply("o que aconteceu no brasil", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert "brasil" in seen[-1].lower()
    assert _reply("novidades sobre tecnologia", fetch, tmp_path / "n.json") == (
        "Nas notícias, Senhor. Alpha sobe. Beta cai."
    )
    assert "tecnologia" in seen[-1]


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
    ):
        assert _reply(said, fetch, path) == "O café é uma bebida, Senhor."
    assert all(url.endswith("q=cafe") for url in seen)
    assert _reply("pode pesquisar", fetch, path) == "O que devo procurar, Senhor?"
    assert _reply("google", fetch, path) == "O que devo procurar, Senhor?"
    assert _reply("o que é", fetch, path) == "O que devo procurar, Senhor?"
    assert _reply("me fala sobre", fetch, path) == "O que devo procurar, Senhor?"
    assert _reply("quero saber", fetch, path) == "O que devo procurar, Senhor?"
    assert _reply("quem é", fetch, path) == "O que devo procurar, Senhor?"
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
    assert _reply("quero anotar ligar amanhã", fetch, path) == "Anotado, Senhor."
    saved = path.read_text(encoding="utf-8")
    assert '"text": "ligar amanhã"' in saved
    assert "quero anotar" not in saved
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
    assert _reply("procura lembrete", fetch, path) == "O que devo buscar nas notas, Senhor?"
    assert _reply("tem recado sobre projeto", fetch, path) == (
        "Nas notas, Senhor. entregar o projeto na sexta."
    )
    assert _reply("cadê a nota", fetch, path) == "O que devo buscar nas notas, Senhor?"
    voice_hit = _reply("onde eu anotei a voz", fetch, voice)
    assert voice_hit == "Nas notas, Senhor. revisar o projeto de voz."


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

    def fake_weather(place, _fetch, day=""):
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
    assert reply("buscar nota", []) == "O que devo buscar nas notas, Senhor?"
    assert "comprar café" in reply("café", [])


def test_network_failure_is_spoken(tmp_path):
    def fetch(_url):
        raise TimeoutError("off")

    assert _reply("noticias de hoje", fetch, tmp_path / "n.json") == (
        "Não alcancei isso agora, Senhor."
    )
