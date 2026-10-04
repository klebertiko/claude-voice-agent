"""Painel do Orion: reator ao centro, sistemas e a conversa.

Sem vídeo. O reator é o núcleo; a conversa e os sistemas ficam em volta.
"""

from __future__ import annotations

_PAGE = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>__NAME__</title>
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;600;700&display=swap" rel="stylesheet" />
<style>
  :root {
    color-scheme: dark;
    --bg: #07090d;
    --bg2: #10131a;
    --bg3: #181c26;
    --border: #2a3142;
    --text: #e7edf5;
    --text2: #b7c0d0;
    --text3: #7e8aa0;
    --accent: #ff7a3c;
    --core: #d7f4ff;
    --ring: #7ec8ff;
    --green: #3ddc84;
    --red: #f4565a;
    --font: "Be Vietnam Pro", "Segoe UI", sans-serif;
  }
  * { box-sizing: border-box; }
  html, body { margin: 0; height: 100%; background: var(--bg); color: var(--text); }
  body { font-family: var(--font); font-size: 15px; }
  .app {
    height: 100%;
    display: grid;
    grid-template-columns: 232px minmax(0, 1fr) 340px;
    grid-template-rows: 52px minmax(0, 1fr) auto;
  }
  .side {
    grid-row: 1 / -1;
    background: var(--bg2);
    border-right: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    padding: 16px 14px;
    gap: 14px;
    min-width: 0;
  }
  .brand { display: flex; align-items: center; gap: 10px; }
  .mark {
    width: 28px; height: 28px; flex: none; border-radius: 8px;
    background: var(--accent); color: #1a1400; font-weight: 700;
    display: flex; align-items: center; justify-content: center;
  }
  .brand strong { letter-spacing: 0.16em; font-size: 14px; }
  #status { color: var(--text3); font-size: 12px; font-weight: 400; letter-spacing: 0; display: block; }
  body[data-state="listening"] #status { color: var(--accent); }
  body[data-state="speaking"] #status { color: var(--green); }
  body[data-state="thinking"] #status { color: var(--ring); }
  body[data-state="ignored"] #status { color: var(--red); }
  .side h2 {
    margin: 8px 0 6px; font-size: 11px; letter-spacing: 0.16em;
    text-transform: uppercase; color: var(--text3); font-weight: 600;
  }
  .row {
    display: flex; justify-content: space-between; gap: 8px;
    padding: 7px 0; border-bottom: 1px solid var(--border);
    font-size: 13px;
  }
  .row span { color: var(--text3); }
  .row b { font-weight: 600; text-align: right; }
  .top {
    grid-column: 2 / -1;
    display: flex; align-items: center; justify-content: space-between;
    padding: 0 16px; background: var(--bg2); border-bottom: 1px solid var(--border);
  }
  .top h1 { margin: 0; font-size: 15px; font-weight: 600; }
  #clock { color: var(--ring); font-variant-numeric: tabular-nums; letter-spacing: 0.04em; }
  .stage { position: relative; min-width: 0; min-height: 0; }
  #field { display: block; width: 100%; height: 100%; }
  .dock {
    background: var(--bg2);
    border-left: 1px solid var(--border);
    display: flex; flex-direction: column; min-width: 0; min-height: 0;
  }
  .dock h2 {
    margin: 0; padding: 12px 14px 0; font-size: 11px; letter-spacing: 0.16em;
    text-transform: uppercase; color: var(--text3); font-weight: 600;
  }
  #log {
    flex: 1; min-height: 0; overflow: auto;
    display: flex; flex-direction: column; gap: 8px;
    padding: 12px 14px;
  }
  #log .empty { margin: auto; color: var(--text3); }
  #log .user, #log .agent { margin: 0; max-width: 100%; padding: 8px 12px; line-height: 1.5; }
  #log .user {
    align-self: flex-end;
    background: rgba(255, 122, 60, 0.12);
    border: 1px solid rgba(255, 130, 67, 0.35);
    border-radius: 12px 12px 3px 12px;
  }
  #log .agent {
    align-self: flex-start;
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 3px 12px 12px 12px;
  }
  #log .meta { align-self: center; color: var(--text3); font-size: 13px; margin: 0; }
  .bar {
    grid-column: 2 / -1;
    display: flex; align-items: center; gap: 8px;
    margin: 10px 12px 12px; padding: 8px;
    background: var(--bg2); border: 1px solid var(--border); border-radius: 16px;
  }
  #text {
    flex: 1; min-width: 0; background: var(--bg3); color: var(--text);
    border: 1px solid var(--border); border-radius: 12px;
    font: inherit; font-size: 16px; padding: 11px 14px; outline: none;
  }
  #text:focus { border-color: var(--ring); }
  #text::placeholder { color: var(--text3); }
  button {
    font: inherit; font-weight: 600; font-size: 13px; cursor: pointer;
    height: 44px; padding: 0 12px; border-radius: 12px; flex: none;
    background: var(--bg3); color: var(--text2); border: 1px solid var(--border);
  }
  button:hover { border-color: var(--accent); color: var(--accent); }
  button:disabled { opacity: 0.4; cursor: not-allowed; }
  button.primary { background: var(--accent); border-color: var(--accent); color: #1a1400; width: 44px; padding: 0; }
  button.primary:hover { color: #1a1400; opacity: 0.9; }
  button[data-state="error"] { border-color: var(--red); color: var(--red); }
  #mic[data-hot="1"] { border-color: var(--red); color: var(--red); }
  button:focus-visible, #text:focus-visible { outline: 2px solid var(--ring); outline-offset: 2px; }
  @media (max-width: 900px) {
    .app { grid-template-columns: 1fr; grid-template-rows: auto 38vh minmax(180px, 1fr) auto; }
    .side { grid-row: auto; flex-direction: row; flex-wrap: wrap; border-right: 0; border-bottom: 1px solid var(--border); padding: 10px 12px; gap: 8px 16px; }
    .side h2 { display: none; }
    .systems { display: flex; gap: 12px; flex: 1; }
    .row { border: 0; padding: 0; }
    .top { grid-column: 1; }
    .dock { border-left: 0; border-top: 1px solid var(--border); }
    .bar { grid-column: 1; margin: 8px; }
  }
  @media (prefers-reduced-motion: reduce) { * { scroll-behavior: auto; } }
</style>
</head>
<body data-state="idle" data-name="__NAME__">
<div class="app">
  <aside class="side">
    <div class="brand">
      <div class="mark" aria-hidden="true">O</div>
      <div>
        <strong>__NAME__</strong>
        <span id="status">pronto</span>
      </div>
    </div>
    <div>
      <h2>Sistemas</h2>
      <div class="systems">
        <div class="row"><span>voz</span><b>george</b></div>
        <div class="row"><span>ritmo</span><b>1.08</b></div>
        <div class="row"><span>fuso</span><b>Brasília</b></div>
        <div class="row"><span>sessão</span><b id="sess">à espera do nome</b></div>
        <div class="row"><span>data</span><b id="date">—</b></div>
      </div>
    </div>
  </aside>
  <header class="top">
    <h1>Reator</h1>
    <div id="clock">00:00:00</div>
  </header>
  <div class="stage">
    <canvas id="field" aria-label="reator"></canvas>
  </div>
  <section class="dock">
    <h2>Conversa</h2>
    <div id="log" aria-live="polite"><p class="empty" id="empty">Diga, Senhor.</p></div>
  </section>
  <form class="bar" id="form">
    <input id="text" autocomplete="off" placeholder="Diga, Senhor" aria-label="frase" />
    <button type="button" id="voice">ouvir</button>
    <button type="button" id="mic" aria-label="segurar para falar">falar</button>
    <button class="primary" type="submit" aria-label="enviar">↑</button>
  </form>
</div>
<audio id="player"></audio>
<script>
const canvas = document.getElementById("field");
const ctx = canvas.getContext("2d");
const statusEl = document.getElementById("status");
const clockEl = document.getElementById("clock");
const dateEl = document.getElementById("date");
const sessEl = document.getElementById("sess");
const logEl = document.getElementById("log");
const emptyEl = document.getElementById("empty");
const form = document.getElementById("form");
const text = document.getElementById("text");
const player = document.getElementById("player");
const micBtn = document.getElementById("mic");
const voiceBtn = document.getElementById("voice");
const submitBtn = form.querySelector("[type=submit]");
const DPR = Math.min(devicePixelRatio || 1, 2);
const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
const labels = { idle: "pronto", listening: "ouvindo", thinking: "pensando", speaking: "falando", ignored: "sem o nome" };

function resize() {
  const stage = canvas.parentElement;
  const w = stage.clientWidth, h = stage.clientHeight;
  canvas.width = Math.max(1, Math.floor(w * DPR));
  canvas.height = Math.max(1, Math.floor(h * DPR));
  canvas.style.width = w + "px";
  canvas.style.height = h + "px";
  ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
}

function ring(cx, cy, r, start, span, width, color) {
  ctx.beginPath();
  ctx.strokeStyle = color;
  ctx.lineWidth = width;
  ctx.arc(cx, cy, r, start, start + span);
  ctx.stroke();
}

function drawReactor(now) {
  const w = canvas.width / DPR, h = canvas.height / DPR;
  const cx = w / 2, cy = h / 2;
  const R = Math.min(w, h) * 0.36;
  const state = document.body.dataset.state;
  const spin = reduce ? 0.4 : now / 1000;
  const dir = state === "listening" ? -1 : 1;
  const pace = state === "thinking" ? 1.6 : state === "speaking" ? 0.8 : 0.35;
  const grd = ctx.createRadialGradient(cx, cy, R * 0.2, cx, cy, Math.max(w, h) * 0.7);
  grd.addColorStop(0, "#121820");
  grd.addColorStop(1, "#07090d");
  ctx.fillStyle = grd;
  ctx.fillRect(0, 0, w, h);

  ctx.save();
  ctx.translate(cx, cy);
  ctx.strokeStyle = "rgba(126,200,255,0.18)";
  ctx.lineWidth = 1;
  for (let i = 0; i < 72; i++) {
    const a = (i / 72) * Math.PI * 2;
    const inner = R * 1.18, outer = i % 6 === 0 ? R * 1.32 : R * 1.26;
    ctx.beginPath();
    ctx.moveTo(Math.cos(a) * inner, Math.sin(a) * inner);
    ctx.lineTo(Math.cos(a) * outer, Math.sin(a) * outer);
    ctx.stroke();
  }
  ctx.restore();

  const base = spin * pace * dir;
  for (let s = 0; s < 8; s++) {
    ring(cx, cy, R, base + s * (Math.PI / 4), Math.PI / 6, 7, "rgba(126,200,255,0.85)");
  }
  for (let s = 0; s < 6; s++) {
    ring(cx, cy, R * 0.78, -base * 1.4 + s * (Math.PI / 3), Math.PI / 5, 4, "rgba(180,220,255,0.55)");
  }
  ring(cx, cy, R * 0.58, base * 0.6, Math.PI * 1.55, 2, "rgba(126,200,255,0.45)");

  const load = state === "thinking" ? 0.82 : state === "listening" ? 0.6 : state === "speaking" ? 0.45 + level * 0.5 : 0.28;
  ring(cx, cy, R * 0.48, -Math.PI / 2, Math.PI * 2 * load, 6, "#ff7a3c");

  ctx.save();
  ctx.translate(cx, cy);
  ctx.rotate(base * 0.5);
  ctx.beginPath();
  for (let i = 0; i < 3; i++) {
    const a = -Math.PI / 2 + i * (Math.PI * 2 / 3);
    const x = Math.cos(a) * R * 0.28, y = Math.sin(a) * R * 0.28;
    if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
  }
  ctx.closePath();
  ctx.strokeStyle = "rgba(215,244,255,0.9)";
  ctx.lineWidth = 2;
  ctx.stroke();
  ctx.restore();

  const coreR = R * (0.12 + (state === "speaking" ? level * 0.05 : 0));
  const core = ctx.createRadialGradient(cx, cy, 0, cx, cy, coreR * 3);
  core.addColorStop(0, "#ffffff");
  core.addColorStop(0.35, "#d7f4ff");
  core.addColorStop(1, "rgba(126,200,255,0)");
  ctx.fillStyle = core;
  ctx.beginPath();
  ctx.arc(cx, cy, coreR * 3, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillStyle = "#f4fbff";
  ctx.beginPath();
  ctx.arc(cx, cy, coreR, 0, Math.PI * 2);
  ctx.fill();

  ctx.fillStyle = "rgba(183,192,208,0.8)";
  ctx.font = "13px Be Vietnam Pro, sans-serif";
  ctx.textAlign = "center";
  ctx.fillText((labels[state] || state).toUpperCase(), cx, cy + R * 1.48);
}

let level = 0;
const timeBuf = new Uint8Array(256);
function sampleLevel() {
  if (!analyser || document.body.dataset.state !== "speaking") { level *= 0.9; return; }
  analyser.getByteTimeDomainData(timeBuf);
  let s = 0;
  for (let i = 0; i < timeBuf.length; i++) {
    const v = (timeBuf[i] - 128) / 128;
    s += v * v;
  }
  level = Math.min(1, Math.sqrt(s / timeBuf.length) * 5);
}
function frame(now) {
  sampleLevel();
  drawReactor(now || 0);
  if (!reduce) requestAnimationFrame(frame);
}
function tickClock() {
  const now = new Date();
  clockEl.textContent = new Intl.DateTimeFormat("pt-BR", {
    timeZone: "America/Sao_Paulo", hour: "2-digit", minute: "2-digit", second: "2-digit", hourCycle: "h23"
  }).format(now);
  dateEl.textContent = new Intl.DateTimeFormat("pt-BR", {
    timeZone: "America/Sao_Paulo", day: "2-digit", month: "short"
  }).format(now);
}
function setState(name) {
  document.body.dataset.state = name;
  statusEl.textContent = labels[name] || name;
  const busy = name === "thinking";
  for (const btn of [submitBtn, voiceBtn, micBtn]) {
    btn.disabled = busy;
    if (busy) btn.dataset.state = "loading";
    else if (btn.dataset.state === "loading") delete btn.dataset.state;
  }
  text.disabled = busy;
}
function mark(btn, state) {
  btn.dataset.state = state;
  setTimeout(() => { if (btn.dataset.state === state) delete btn.dataset.state; }, 900);
}
function addLine(cls, message) {
  if (emptyEl) emptyEl.remove();
  const p = document.createElement("p");
  p.className = cls;
  p.textContent = message;
  logEl.appendChild(p);
  logEl.scrollTop = logEl.scrollHeight;
}
let audioCtx, analyser;
function ensureAnalyser() {
  if (analyser) return;
  audioCtx = new AudioContext();
  const src = audioCtx.createMediaElementSource(player);
  analyser = audioCtx.createAnalyser();
  analyser.fftSize = 256;
  src.connect(analyser);
  analyser.connect(audioCtx.destination);
}
async function playWav(b64) {
  if (!b64) return;
  ensureAnalyser();
  if (audioCtx.state === "suspended") await audioCtx.resume();
  const bytes = Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
  const url = URL.createObjectURL(new Blob([bytes], { type: "audio/wav" }));
  player.src = url;
  setState("speaking");
  await player.play();
  await new Promise((resolve) => { player.onended = resolve; });
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
async function showTurn(data, sourceBtn) {
  if (data.heard) addLine("user", data.heard);
  if (data.status === "ignored") {
    setState("ignored");
    sessEl.textContent = "à espera do nome";
    addLine("meta", "Não ouvi o nome. Diga __WAKE__.");
    if (sourceBtn) mark(sourceBtn, "error");
    return;
  }
  if (data.status === "noise") {
    setState("idle");
    addLine("meta", "Ignorei um ruído.");
    return;
  }
  if (data.status === "replied") sessEl.textContent = "acordado";
  if (data.reply) addLine("agent", data.reply);
  if (data.audio_b64) await playWav(data.audio_b64);
  else setState("idle");
  if (sourceBtn && data.reply) mark(sourceBtn, "success");
}
form.addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const value = text.value.trim();
  if (!value) return;
  text.value = "";
  setState("thinking");
  try { await showTurn(await post("/api/turn", { text: value }), submitBtn); }
  catch (err) { setState("idle"); addLine("meta", "Não consegui falar agora."); mark(submitBtn, "error"); }
});
voiceBtn.addEventListener("click", async () => {
  setState("thinking");
  try {
    const data = await post("/api/greeting", {});
    if (data.reply) addLine("agent", data.reply);
    if (data.status === "replied") sessEl.textContent = "acordado";
    if (data.audio_b64) await playWav(data.audio_b64);
    else setState("idle");
    mark(voiceBtn, "success");
  } catch (err) {
    setState("idle");
    addLine("meta", "Não consegui falar agora.");
    mark(voiceBtn, "error");
  }
});
let micStream, captureCtx, processor, chunks = [], capturing = false;
async function startMic(ev) {
  ev.preventDefault();
  if (capturing || micBtn.disabled) return;
  try {
    micStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
  } catch (err) {
    addLine("meta", "Microfone indisponível. Escreva a frase.");
    mark(micBtn, "error");
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
    chunks.push(new Float32Array(event.inputBuffer.getChannelData(0)));
  };
  source.connect(processor);
  processor.connect(sink);
  sink.connect(captureCtx.destination);
  micBtn.dataset.hot = "1";
  setState("listening");
}
async function stopMic(ev) {
  if (!capturing) return;
  ev.preventDefault();
  capturing = false;
  delete micBtn.dataset.hot;
  const rate = captureCtx.sampleRate;
  processor.disconnect();
  micStream.getTracks().forEach((track) => track.stop());
  await captureCtx.close();
  const total = chunks.reduce((n, c) => n + c.length, 0);
  const merged = new Float32Array(total);
  let offset = 0;
  for (const chunk of chunks) { merged.set(chunk, offset); offset += chunk.length; }
  const pcm = new Int16Array(merged.length);
  for (let i = 0; i < merged.length; i++) {
    const s = Math.max(-1, Math.min(1, merged[i]));
    pcm[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
  }
  const bytes = new Uint8Array(pcm.buffer);
  let binary = "";
  const stepSize = 0x8000;
  for (let i = 0; i < bytes.length; i += stepSize) {
    binary += String.fromCharCode(...bytes.subarray(i, i + stepSize));
  }
  setState("thinking");
  try {
    await showTurn(await post("/api/turn", { pcm_b64: btoa(binary), sample_rate: rate }), micBtn);
  } catch (err) {
    setState("idle");
    addLine("meta", "Não consegui ouvir agora.");
    mark(micBtn, "error");
  }
}
micBtn.addEventListener("pointerdown", startMic);
micBtn.addEventListener("pointerup", stopMic);
micBtn.addEventListener("pointerleave", stopMic);
addEventListener("resize", resize);
resize();
tickClock();
setInterval(tickClock, 1000);
requestAnimationFrame(frame);
</script>
</body>
</html>
"""


def render_page(name: str, wake: str) -> str:
    """Injeta o nome da persona. O microfone pede só áudio."""
    safe_name = name.replace("<", "").replace(">", "").replace('"', "").replace("&", "")
    safe_wake = wake.replace("<", "").replace(">", "").replace('"', "").replace("&", "")
    return _PAGE.replace("__NAME__", safe_name).replace("__WAKE__", safe_wake)
