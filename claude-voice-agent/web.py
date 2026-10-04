"""Servidor local do painel de voz.

    uv run python -m claude_agent_voice.web

Abre em http://127.0.0.1:8765. A página pede só áudio.
"""

from __future__ import annotations

import base64
import io
import json
import logging
import os
import secrets
import threading
import time
import wave
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from zoneinfo import ZoneInfo

from .actions import DENY_SPOKEN, PERMIT_SPOKEN, extract_proposal, run_command, speak_result
from .agent import greeting, make_tts
from .hud import HudSession, make_reply_fn, take_turn
from .hud_page import render_page
from .personas import get_persona
from .llm_ollama import probe_ollama
from .settings import Settings
from .stt_whisper import WhisperSTT, to_mono16k
from .tts_kokoro import pcm16_bytes
from .wake import WakeGate

logger = logging.getLogger("claude_agent_voice.web")


def wav_bytes(pcm: bytes, sample_rate: int) -> bytes:
    """PCM16 mono -> WAV. Pura."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(pcm)
    return buf.getvalue()


class VoiceHud:
    """Um painel: sessão de wake, fala e (se houver) o cérebro."""

    def __init__(
        self,
        session: HudSession,
        reply_fn,
        synth_fn,
        transcribe_fn,
        clock,
        now=None,
        workdir: Path | None = None,
        probe_fn=None,
    ) -> None:
        self.session = session
        self.reply_fn = reply_fn
        self.synth_fn = synth_fn
        self.transcribe_fn = transcribe_fn
        self.clock = clock
        self.now = now or (lambda: datetime.now(ZoneInfo("America/Sao_Paulo")))
        self.workdir = workdir or Path.cwd()
        self.probe_fn = probe_fn or (lambda: {"up": False, "model": None, "models": []})
        self._lock = threading.Lock()
        self._greet_n = 0
        self._permits: dict[str, str] = {}
        self._status_at = 0.0
        self._status_cache: dict | None = None

    def handle(
        self,
        *,
        text: str | None = None,
        pcm: bytes | None = None,
        sample_rate: int = 16000,
        typed: bool = False,
    ) -> dict:
        with self._lock:
            if pcm:
                heard = self.transcribe_fn(pcm, sample_rate)
                enforce_wake = None
            else:
                heard = text or ""
                enforce_wake = False if typed else None
            result = take_turn(
                self.session,
                heard,
                self.clock(),
                self.reply_fn,
                enforce_wake=enforce_wake,
            )
            command = extract_proposal(result.reply) if result.status == "replied" else None
            if not command:
                return self._with_audio(result.status, result.heard, result.reply)
            if self.session.history and self.session.history[-1][0] == "assistant":
                self.session.history[-1] = ("assistant", PERMIT_SPOKEN)
            permit_id = secrets.token_hex(4)
            self._permits[permit_id] = command
            payload = self._with_audio("permit", result.heard, PERMIT_SPOKEN)
            payload["command"] = command
            payload["permit_id"] = permit_id
            return payload

    def resolve(self, permit_id: str, allow: bool) -> dict:
        """Executa ou recusa a ordem que o painel mostrou."""
        with self._lock:
            command = self._permits.pop(permit_id, None)
            if command is None:
                return self._with_audio("empty", "", "Não há ordem pendente, Senhor.")
            if not allow:
                self.session.history.append(("assistant", DENY_SPOKEN))
                payload = self._with_audio("replied", "", DENY_SPOKEN)
                payload["output"] = ""
                payload["code"] = None
                return payload
            code, output = run_command(command, self.workdir)
            reply = speak_result(code, output)
            self.session.history.append(("assistant", reply))
            payload = self._with_audio("replied", "", reply)
            payload["output"] = output
            payload["code"] = code
            return payload

    def status_payload(self) -> dict:
        now = time.monotonic()
        if self._status_cache is not None and now - self._status_at < 3:
            return self._status_cache
        info = self.probe_fn() or {}
        try:
            load = [round(n, 2) for n in os.getloadavg()]
        except OSError:
            load = []
        payload = {
            "up": bool(info.get("up")),
            "model": info.get("model"),
            "models": list(info.get("models") or []),
            "load": load,
        }
        self._status_cache = payload
        self._status_at = now
        return payload

    def warm(self) -> None:
        """Carrega o modelo de voz sem gastar a primeira saudação do dia."""
        self.synth_fn("Boa noite, Senhor.")

    def greeting_payload(self) -> dict:
        with self._lock:
            line = greeting(self.session.persona, when=self.now(), salt=self._greet_n)
            self._greet_n += 1
            pcm, rate = self.synth_fn(line)
            audio = wav_bytes(pcm, rate)
        return {
            "status": "replied",
            "heard": "",
            "reply": line,
            "audio_b64": base64.b64encode(audio).decode("ascii"),
            "sample_rate": rate,
        }

    def _with_audio(self, status: str, heard: str, reply: str) -> dict:
        payload = {
            "status": status,
            "heard": heard,
            "reply": reply,
            "audio_b64": None,
            "sample_rate": None,
        }
        if not reply:
            return payload
        pcm, rate = self.synth_fn(reply)
        payload["audio_b64"] = base64.b64encode(wav_bytes(pcm, rate)).decode("ascii")
        payload["sample_rate"] = rate
        return payload


def _default_synth(tts):
    def synth(text: str) -> tuple[bytes, int]:
        create_pcm = getattr(tts, "create_pcm", None)
        if create_pcm is not None:
            return create_pcm(text), tts.sample_rate
        samples, rate = tts.create(text)
        return pcm16_bytes(samples), rate

    return synth


def _default_transcribe(stt: WhisperSTT):
    def transcribe(pcm: bytes, sample_rate: int) -> str:
        audio = to_mono16k(pcm, sample_rate, 1)
        if audio.size == 0:
            return ""
        return stt.transcribe_array(audio)

    return transcribe


def create_hud(settings: Settings | None = None) -> VoiceHud:
    settings = settings or Settings.from_env()
    persona = get_persona(settings.persona)
    session = HudSession(
        persona=persona,
        require_wake=settings.require_wake,
        gate=WakeGate(wake_words=persona.wake_words, window_s=settings.wake_window_s),
    )
    tts = make_tts(settings, persona)
    host = settings.ollama_host
    preferred = settings.ollama_model

    def probe() -> dict:
        info = probe_ollama(host) if host else {"up": False, "model": None, "models": []}
        if info.get("up") and preferred:
            info["model"] = preferred
        return info

    stt = WhisperSTT(
        model=settings.whisper_model,
        device=settings.whisper_device,
        compute_type=settings.whisper_compute,
        language=settings.whisper_lang,
    )
    return VoiceHud(
        session=session,
        reply_fn=make_reply_fn(settings, persona),
        synth_fn=_default_synth(tts),
        transcribe_fn=_default_transcribe(stt),
        clock=time.monotonic,
        probe_fn=probe,
    )


def _handler(hud: VoiceHud, page: str):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args) -> None:
            logger.info("%s - %s", self.address_string(), fmt % args)

        def _send(self, code: int, body: bytes, content_type: str) -> None:
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _read_json(self) -> dict:
            length = int(self.headers.get("Content-Length", "0") or 0)
            if length > 8_000_000:
                raise ValueError("corpo grande demais")
            raw = self.rfile.read(length) if length else b"{}"
            data = json.loads(raw.decode("utf-8"))
            if not isinstance(data, dict):
                raise ValueError("json inválido")
            return data

        def do_GET(self) -> None:  # noqa: N802
            path = self.path.split("?", 1)[0]
            if path == "/api/status":
                body = json.dumps(hud.status_payload()).encode("utf-8")
                self._send(200, body, "application/json")
                return
            if path != "/":
                self._send(404, b"{}", "application/json")
                return
            self._send(200, page.encode("utf-8"), "text/html; charset=utf-8")

        def do_POST(self) -> None:  # noqa: N802
            path = self.path.split("?", 1)[0]
            try:
                data = self._read_json()
                if path == "/api/greeting":
                    payload = hud.greeting_payload()
                elif path == "/api/turn":
                    pcm = None
                    if data.get("pcm_b64"):
                        pcm = base64.b64decode(data["pcm_b64"])
                    payload = hud.handle(
                        text=data.get("text"),
                        pcm=pcm,
                        sample_rate=int(data.get("sample_rate") or 16000),
                        typed=pcm is None,
                    )
                elif path == "/api/permit":
                    payload = hud.resolve(str(data.get("id") or ""), bool(data.get("allow")))
                else:
                    self._send(404, b"{}", "application/json")
                    return
            except (ValueError, json.JSONDecodeError, base64.binascii.Error) as exc:
                body = json.dumps({"error": str(exc)}).encode("utf-8")
                self._send(400, body, "application/json")
                return
            except Exception:
                logger.exception("turno falhou")
                self._send(500, b'{"error":"falha"}', "application/json")
                return
            self._send(200, json.dumps(payload).encode("utf-8"), "application/json")

    return Handler


def serve(hud: VoiceHud, host: str = "127.0.0.1", port: int = 8765) -> ThreadingHTTPServer:
    persona = hud.session.persona
    page = render_page(persona.name, persona.name)
    httpd = ThreadingHTTPServer((host, port), _handler(hud, page))
    thread = threading.Thread(target=httpd.serve_forever, name="voice-hud", daemon=True)
    thread.start()
    httpd.hud_thread = thread  # type: ignore[attr-defined]
    return httpd


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    host = os.environ.get("CLAUDE_VOICE_HUD_HOST", "127.0.0.1")
    port = int(os.environ.get("CLAUDE_VOICE_HUD_PORT", "8765"))
    hud = create_hud()
    logger.info("aquecendo a voz %s...", hud.session.persona.voice)
    hud.warm()
    httpd = serve(hud, host, port)
    bound = httpd.server_address
    logger.info("Painel em http://%s:%s", bound[0], bound[1])
    try:
        httpd.hud_thread.join()  # type: ignore[attr-defined]
    except KeyboardInterrupt:
        httpd.shutdown()


if __name__ == "__main__":
    main()
