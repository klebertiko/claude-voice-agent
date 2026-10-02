"""Página do painel. Sem câmera: o centro é um anel, não um vídeo."""

from __future__ import annotations

_PAGE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>__NAME__</title>
<style>
  :root {
    --cyan: #8ee7ff;
    --gold: #e4c27a;
    --ink: #d7e8f2;
    --muted: #7f97a8;
    --bg: #05080d;
    --level: 0.15;
  }
  * { box-sizing: border-box; }
  html, body { margin: 0; height: 100%; }
  body {
    min-height: 100%;
    color: var(--ink);
    font-family: "Segoe UI", system-ui, sans-serif;
    background:
      radial-gradient(ellipse at 50% 42%, #123044 0%, transparent 46%),
      var(--bg);
    display: flex;
    flex-direction: column;
  }
  header {
    display: flex;
    justify-content: space-between;
    gap: 16px;
    padding: 18px 28px 0;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    font-size: 12px;
    color: var(--muted);
  }
  header strong { color: var(--cyan); font-weight: 600; }
  main {
    flex: 1;
    display: grid;
    place-items: center;
    padding: 12px;
  }
  .reactor {
    position: relative;
    width: min(420px, 78vw);
    aspect-ratio: 1;
    display: grid;
    place-items: center;
  }
  .ring {
    position: absolute;
    border-radius: 50%;
    border: 1px solid rgba(142, 231, 255, 0.45);
  }
  .r1 { inset: 4%; border-style: dashed; animation: spin 28s linear infinite; }
  .r2 {
    inset: 14%;
    border-width: 2px;
    border-color: transparent;
    border-top-color: var(--cyan);
    border-bottom-color: rgba(228, 194, 122, 0.8);
    animation: spin 12s linear infinite reverse;
  }
  .r3 {
    inset: 24%;
    background: repeating-conic-gradient(from 0deg, rgba(142,231,255,0.55) 0 2deg, transparent 2deg 12deg);
    -webkit-mask: radial-gradient(circle, transparent 62%, #000 64% 68%, transparent 70%);
    mask: radial-gradient(circle, transparent 62%, #000 64% 68%, transparent 70%);
    animation: spin 18s linear infinite;
  }
  .core {
    width: 38%;
    aspect-ratio: 1;
    border-radius: 50%;
    background:
      radial-gradient(circle at 50% 45%, #e9fbff 0%, var(--cyan) 28%, #0b3a52 70%, #061018 100%);
    box-shadow: 0 0 calc(24px + 70px * var(--level)) rgba(142, 231, 255, 0.55);
    transform: scale(calc(0.92 + var(--level) * 0.18));
    transition: transform 80ms linear;
  }
  .status {
    position: absolute;
    bottom: 6%;
    letter-spacing: 0.28em;
    font-size: 13px;
    color: var(--gold);
  }
  body[data-state="listening"] .r2 { animation-duration: 4s; }
  body[data-state="thinking"] .core { animation: pulse 1.1s ease-in-out infinite; }
  body[data-state="speaking"] { --level: 0.55; }
  body[data-state="ignored"] .status { color: var(--muted); }
  .log {
    min-height: 92px;
    max-height: 28vh;
    overflow: auto;
    margin: 0 28px;
    padding: 8px 4px 12px;
    font-size: 16px;
    line-height: 1.45;
  }
  .log p { margin: 0 0 8px; }
  .log .user { color: var(--gold); }
  .log .agent { color: var(--ink); }
  .log .meta { color: var(--muted); font-size: 14px; }
  form {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    padding: 0 28px 28px;
  }
  input {
    flex: 1 1 220px;
    background: rgba(8, 16, 24, 0.8);
    color: var(--ink);
    border: 1px solid rgba(142, 231, 255, 0.35);
    border-radius: 999px;
    padding: 12px 18px;
    font: inherit;
  }
  button {
    background: transparent;
    color: var(--cyan);
    border: 1px solid rgba(142, 231, 255, 0.55);
    border-radius: 999px;
    padding: 12px 18px;
    font: inherit;
    letter-spacing: 0.04em;
    cursor: pointer;
  }
  button:hover { background: rgba(142, 231, 255, 0.08); }
  button.hold { color: var(--gold); border-color: rgba(228, 194, 122, 0.7); }
  @keyframes spin { to { transform: rotate(360deg); } }
  @keyframes pulse { 50% { filter: brightness(1.35); } }
  @media (max-width: 640px) {
    header, .log, form { padding-left: 16px; padding-right: 16px; }
    header { letter-spacing: 0.12em; }
    form { padding-bottom: 16px; }
  }
</style>
</head>
<body data-state="idle">
<header>
  <span><strong>__NAME__</strong> · português do Brasil</span>
  <span>sem câmera</span>
</header>
<main>
  <div class="reactor" id="reactor">
    <div class="ring r1"></div>
    <div class="ring r2"></div>
    <div class="ring r3"></div>
    <div class="core"></div>
    <div class="status" id="status">PRONTO</div>
  </div>
</main>
<section class="log" id="log" aria-live="polite"></section>
<form id="form">
  <input id="text" autocomplete="off" placeholder="Diga ou escreva: __WAKE__, ..." />
  <button type="submit">Enviar</button>
  <button type="button" id="voice">Ouvir a voz</button>
  <button type="button" id="mic" class="hold">Segurar para falar</button>
</form>
<audio id="player"></audio>
<script>
const statusEl = document.getElementById("status");
const logEl = document.getElementById("log");
const form = document.getElementById("form");
const text = document.getElementById("text");
const player = document.getElementById("player");
const micBtn = document.getElementById("mic");
const reactor = document.getElementById("reactor");
const labels = { idle: "PRONTO", listening: "OUVINDO", thinking: "PENSANDO", speaking: "FALANDO" };

function setState(name) {
  document.body.dataset.state = name;
  statusEl.textContent = labels[name] || name;
}

function addLine(cls, message) {
  const p = document.createElement("p");
  p.className = cls;
  p.textContent = message;
  logEl.appendChild(p);
  logEl.scrollTop = logEl.scrollHeight;
}

let audioCtx;
let analyser;
function ensureAnalyser() {
  if (analyser) return;
  audioCtx = new AudioContext();
  const src = audioCtx.createMediaElementSource(player);
  analyser = audioCtx.createAnalyser();
  analyser.fftSize = 256;
  src.connect(analyser);
  analyser.connect(audioCtx.destination);
  const bins = new Uint8Array(analyser.frequencyBinCount);
  const tick = () => {
    if (document.body.dataset.state === "speaking") {
      analyser.getByteFrequencyData(bins);
      let sum = 0;
      for (const v of bins) sum += v;
      const level = Math.min(1, sum / bins.length / 140);
      reactor.style.setProperty("--level", String(0.2 + level));
    } else if (document.body.dataset.state !== "listening") {
      reactor.style.setProperty("--level", "0.15");
    }
    requestAnimationFrame(tick);
  };
  tick();
}

async function playWav(b64) {
  if (!b64) return;
  ensureAnalyser();
  if (audioCtx.state === "suspended") await audioCtx.resume();
  const bytes = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
  const url = URL.createObjectURL(new Blob([bytes], { type: "audio/wav" }));
  player.src = url;
  setState("speaking");
  await player.play();
  await new Promise(resolve => player.onended = resolve);
  URL.revokeObjectURL(url);
  setState("idle");
}

async function post(url, body) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body || {}),
  });
  if (!res.ok) throw new Error("falha " + res.status);
  return res.json();
}

async function showTurn(data) {
  if (data.heard) addLine("user", data.heard);
  if (data.status === "ignored") {
    setState("ignored");
    addLine("meta", "Não ouvi o nome. Diga __WAKE__.");
    return;
  }
  if (data.status === "noise") {
    setState("idle");
    addLine("meta", "Ignorei um ruído.");
    return;
  }
  if (data.reply) addLine("agent", data.reply);
  if (data.audio_b64) await playWav(data.audio_b64);
  else setState("idle");
}

form.addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const value = text.value.trim();
  if (!value) return;
  text.value = "";
  setState("thinking");
  try {
    await showTurn(await post("/api/turn", { text: value }));
  } catch (err) {
    setState("idle");
    addLine("meta", "Não consegui falar agora.");
  }
});

document.getElementById("voice").addEventListener("click", async () => {
  setState("thinking");
  try {
    const data = await post("/api/greeting", {});
    if (data.reply) addLine("agent", data.reply);
    await playWav(data.audio_b64);
  } catch (err) {
    setState("idle");
    addLine("meta", "Não consegui falar agora.");
  }
});

let micStream;
let captureCtx;
let processor;
let chunks = [];
let capturing = false;

async function startMic(ev) {
  ev.preventDefault();
  if (capturing) return;
  try {
    micStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
  } catch (err) {
    addLine("meta", "Microfone indisponível. Escreva a frase.");
    return;
  }
  captureCtx = new AudioContext();
  const source = captureCtx.createMediaStreamSource(micStream);
  processor = captureCtx.createScriptProcessor(4096, 1, 1);
  const sink = captureCtx.createGain();
  sink.gain.value = 0;
  chunks = [];
  capturing = true;
  processor.onaudioprocess = (event) => {
    if (!capturing) return;
    const data = event.inputBuffer.getChannelData(0);
    chunks.push(new Float32Array(data));
    let sum = 0;
    for (let i = 0; i < data.length; i++) sum += Math.abs(data[i]);
    reactor.style.setProperty("--level", String(Math.min(1, sum / data.length * 8)));
  };
  source.connect(processor);
  processor.connect(sink);
  sink.connect(captureCtx.destination);
  setState("listening");
}

async function stopMic(ev) {
  if (!capturing) return;
  ev.preventDefault();
  capturing = false;
  const rate = captureCtx.sampleRate;
  processor.disconnect();
  micStream.getTracks().forEach(track => track.stop());
  await captureCtx.close();
  const total = chunks.reduce((n, c) => n + c.length, 0);
  const merged = new Float32Array(total);
  let offset = 0;
  for (const chunk of chunks) {
    merged.set(chunk, offset);
    offset += chunk.length;
  }
  const pcm = new Int16Array(merged.length);
  for (let i = 0; i < merged.length; i++) {
    const s = Math.max(-1, Math.min(1, merged[i]));
    pcm[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
  }
  const bytes = new Uint8Array(pcm.buffer);
  let binary = "";
  const step = 0x8000;
  for (let i = 0; i < bytes.length; i += step) {
    binary += String.fromCharCode(...bytes.subarray(i, i + step));
  }
  setState("thinking");
  try {
    await showTurn(await post("/api/turn", {
      pcm_b64: btoa(binary),
      sample_rate: rate,
    }));
  } catch (err) {
    setState("idle");
    addLine("meta", "Não consegui ouvir agora.");
  }
}

micBtn.addEventListener("pointerdown", startMic);
micBtn.addEventListener("pointerup", stopMic);
micBtn.addEventListener("pointerleave", stopMic);
</script>
</body>
</html>
"""


def render_page(name: str, wake: str) -> str:
    """Injeta o nome da persona. O microfone pede só áudio."""
    safe_name = name.replace("<", "").replace(">", "")
    safe_wake = wake.replace("<", "").replace(">", "")
    return (
        _PAGE.replace("__NAME__", safe_name).replace("__WAKE__", safe_wake)
    )
