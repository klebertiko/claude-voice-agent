"""Ordens no computador: propõe, espera, e só então corre."""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from claude_agent_voice.actions import (
    clean_command,
    extract_proposal,
    local_command,
    speak_result,
)
from claude_agent_voice.hud import make_reply_fn
from claude_agent_voice.llm_ollama import ask_ollama, probe_ollama
from claude_agent_voice.personas import get_persona
from claude_agent_voice.settings import Settings
from claude_agent_voice.wake import WakeGate
from claude_agent_voice.hud import HudSession
from claude_agent_voice.web import VoiceHud


def test_local_command_and_refusal():
    assert local_command("execute ls -la") == "ls -la"
    assert local_command("liste os arquivos") == "ls"
    assert local_command("que horas são") is None
    assert clean_command("rm\n-rf /") is None
    assert extract_proposal("Posso.\nACAO: pwd") == "pwd"
    assert speak_result(0, "oi") == "Feito, Senhor. oi"
    assert speak_result(1, "x") == "Falhou, Senhor."


def test_permit_does_not_run_until_allowed(tmp_path):
    marker = tmp_path / "marcador"

    def reply(_cleaned, _history):
        return "ACAO: touch marcador"

    hud = VoiceHud(
        session=HudSession(
            persona=get_persona("orion"),
            gate=WakeGate(wake_words=("orion",), window_s=30),
        ),
        reply_fn=reply,
        synth_fn=lambda text: (b"\x00\x00" * 4, 24000),
        transcribe_fn=lambda pcm, rate: "",
        clock=lambda: 1.0,
        workdir=tmp_path,
    )
    pending = hud.handle(text="execute touch marcador", typed=True)
    assert pending["status"] == "permit"
    assert pending["command"] == "touch marcador"
    assert pending["reply"] == "Posso executar isto, Senhor?"
    assert not marker.exists()

    denied = hud.resolve(pending["permit_id"], False)
    assert denied["reply"] == "Não fiz, Senhor."
    assert denied["heard"] == ""
    assert not marker.exists()

    again = hud.handle(text="execute touch marcador", typed=True)
    allowed = hud.resolve(again["permit_id"], True)
    assert marker.exists()
    assert allowed["code"] == 0
    assert allowed["reply"] == "Feito, Senhor."


def test_ollama_host_from_env():
    settings = Settings.from_env(env={"OLLAMA_HOST": "http://10.0.0.8:11434", "OLLAMA_MODEL": "qwen2.5"})
    assert settings.ollama_host == "http://10.0.0.8:11434"
    assert settings.ollama_model == "qwen2.5"


def test_probe_down_is_honest():
    assert probe_ollama("http://127.0.0.1:9", timeout=0.2)["up"] is False


def test_ask_ollama_reads_chat(tmp_path):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            return

        def do_POST(self):
            length = int(self.headers.get("Content-Length", "0"))
            raw = json.loads(self.rfile.read(length).decode())
            assert raw["model"] == "qwen"
            assert raw["messages"][-1]["content"] == "liste a mesa"
            body = json.dumps({"message": {"content": "ACAO: ls"}}).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    port = httpd.server_address[1]
    try:
        text = ask_ollama(f"http://127.0.0.1:{port}", "qwen", "seja breve", [], "liste a mesa", timeout=3)
        assert text == "ACAO: ls"
    finally:
        httpd.shutdown()


def test_clock_does_not_need_ollama():
    settings = Settings.from_env(env={"OLLAMA_HOST": "http://127.0.0.1:9", "CLAUDE_VOICE_CLAUDE_CLI": "no-such-claude"})
    reply = make_reply_fn(settings, get_persona("orion"), lambda: __import__("datetime").datetime(2026, 10, 2, 15, 5))
    assert "15 horas" in reply("que horas são", [])
    assert reply("execute pwd", []).startswith("ACAO:")
