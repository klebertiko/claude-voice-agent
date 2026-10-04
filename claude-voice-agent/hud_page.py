"""Painel do Orion: o reator é a sala, a conversa é anotação.

Sem vídeo. A faixa de cima guarda os sistemas; a margem de baixo, a fala.
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
<link href="https://fonts.googleapis.com/css2?family=Familjen+Grotesk:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet" />
<style>
  /* Hallmark · pre-emit critique: P5 H4 E4 S5 R4 V5 */
  /* Hallmark · macrostructure: Photographic · genre: atmospheric · theme: custom-reactor
   * heading: bottom-aligned · body: full-bleed marginalia · divider: hairline
   * button: typographic-only · image: full-bleed · reveal: none */
  :root {
    color-scheme: dark;
    --color-paper: oklch(0.16 0.018 250);
    --color-paper-2: oklch(0.21 0.02 250);
    --color-ink: oklch(0.93 0.012 250);
    --color-ink-2: oklch(0.74 0.02 250);
    --color-rule: oklch(0.4 0.02 250);
    --color-accent: oklch(0.8 0.11 78);
    --color-accent-ink: oklch(0.22 0.03 78);
    --color-ring: oklch(0.78 0.05 230);
    --color-core: oklch(0.95 0.02 220);
    --color-focus: oklch(0.82 0.07 230);
    --color-ok: oklch(0.78 0.08 165);
    --color-bad: oklch(0.7 0.13 25);
    --font-display: "IBM Plex Mono", ui-monospace, monospace;
    --font-body: "Familjen Grotesk", "Segoe UI", sans-serif;
    --font-mono: "IBM Plex Mono", ui-monospace, monospace;
    --space-3xs: 0.25rem;
    --space-2xs: 0.5rem;
    --space-xs: 0.75rem;
    --space-sm: 1rem;
    --space-md: 1.5rem;
    --space-lg: 2rem;
    --space-xl: 3rem;
    --text-xs: 0.75rem;
    --text-sm: 0.875rem;
    --text-md: 1rem;
    --text-lg: 1.25rem;
    --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
    --dur-short: 220ms;
    --radius-card: 0;
  }
  * { box-sizing: border-box; }
  html, body {
    margin: 0;
    min-height: 100%;
    overflow-x: clip;
    background: var(--color-paper);
    color: var(--color-ink);
  }
  body {
    font-family: var(--font-body);
    font-size: var(--text-md);
    font-style: normal;
  }
  #field {
    position: fixed;
    inset: 0;
    width: 100%;
    height: 100%;
    z-index: 0;
    display: block;
  }
  .room {
    position: relative;
    z-index: 1;
    min-height: 100vh;
    min-width: 0;
    display: grid;
    grid-template-rows: auto minmax(16rem, 1fr) auto auto;
  }
  .strip, .floor { background: var(--color-paper); }
  .strip {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: var(--space-sm);
    padding: var(--space-sm) var(--space-md);
    border-bottom: 1px solid var(--color-rule);
  }
  .brand { display: flex; align-items: baseline; gap: var(--space-xs); min-width: 0; }
  .brand strong {
    font-family: var(--font-display);
    font-weight: 500;
    font-style: normal;
    font-size: var(--text-sm);
    letter-spacing: 0.18em;
  }
  #status {
    font-family: var(--font-mono);
    font-size: var(--text-xs);
    color: var(--color-ink-2);
    letter-spacing: 0.06em;
  }
  body[data-state="listening"] #status,
  body[data-state="speaking"] #status { color: var(--color-accent); }
  body[data-state="thinking"] #status { color: var(--color-ring); }
  body[data-state="ignored"] #status { color: var(--color-bad); }
  .systems {
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-2xs) var(--space-md);
    margin: 0;
    min-width: 0;
  }
  .systems div { display: flex; gap: var(--space-2xs); align-items: baseline; }
  .systems dt {
    font-family: var(--font-mono);
    font-size: var(--text-xs);
    color: var(--color-ink-2);
    font-weight: 400;
  }
  .systems dd {
    margin: 0;
    font-family: var(--font-mono);
    font-size: var(--text-xs);
    color: var(--color-ink);
  }
  #clock {
    font-family: var(--font-mono);
    font-size: var(--text-sm);
    font-variant-numeric: tabular-nums;
    color: var(--color-ring);
    margin: 0;
  }
  .well { min-width: 0; min-height: 0; }
  .talk {
    max-width: 62ch;
    padding: 0 var(--space-md) var(--space-sm);
    background: linear-gradient(to top, var(--color-paper) 70%, transparent);
  }
  .talk h2 {
    margin: 0 0 var(--space-2xs);
    font-family: var(--font-mono);
    font-size: var(--text-xs);
    font-weight: 500;
    font-style: normal;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--color-ink-2);
  }
  #log {
    min-height: 0;
    max-height: 28vh;
    overflow: auto;
    display: flex;
    flex-direction: column;
    gap: var(--space-2xs);
  }
  #log .empty { margin: 0; color: var(--color-ink-2); }
  #log p { margin: 0; line-height: 1.45; overflow-wrap: anywhere; min-width: 0; }
  #log .user, #log .agent { color: var(--color-ink); }
  #log .meta { color: var(--color-ink-2); font-size: var(--text-sm); }
  #log p[data-speaker]::before {
    content: attr(data-speaker);
    display: inline-block;
    min-width: 4.5rem;
    margin-right: var(--space-xs);
    font-family: var(--font-mono);
    font-size: var(--text-xs);
    letter-spacing: 0.08em;
    color: var(--color-ink-2);
  }
  .floor {
    display: flex;
    align-items: center;
    gap: var(--space-sm);
    padding: var(--space-sm) var(--space-md);
    border-top: 1px solid var(--color-rule);
  }
  #text {
    flex: 1;
    min-width: 0;
    background: transparent;
    color: var(--color-ink);
    border: 0;
    border-bottom: 1px solid var(--color-rule);
    border-radius: var(--radius-card);
    font: inherit;
    font-size: var(--text-md);
    padding: var(--space-2xs) 0;
    outline: none;
  }
  #text::placeholder { color: var(--color-ink-2); }
  #text:hover { border-bottom-color: var(--color-ink-2); }
  #text:focus-visible { outline: 2px solid var(--color-focus); outline-offset: 2px; }
  #text:active { color: var(--color-ink); }
  #text:disabled { color: var(--color-ink-2); }
  #text[data-state="loading"] { border-bottom-color: var(--color-ring); }
  #text[data-state="error"] { border-bottom-color: var(--color-bad); }
  #text[data-state="success"] { border-bottom-color: var(--color-ok); }
  .act {
    font-family: var(--font-mono);
    font-size: var(--text-xs);
    font-weight: 500;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    white-space: nowrap;
    cursor: pointer;
    height: auto;
    padding: var(--space-2xs) 0;
    border: 0;
    border-radius: var(--radius-card);
    background: transparent;
    color: var(--color-ink-2);
    transition: color var(--dur-short) var(--ease-out);
  }
  .act:hover { color: var(--color-accent); }
  .act:focus-visible { outline: 2px solid var(--color-focus); outline-offset: 2px; }
  .act:active { color: var(--color-ink); }
  .act:disabled { color: var(--color-rule); cursor: not-allowed; }
  .act[data-state="loading"] { color: var(--color-ring); }
  .act[data-state="error"] { color: var(--color-bad); }
  .act[data-state="success"] { color: var(--color-ok); }
  #mic[data-hot="1"] { color: var(--color-bad); }
  @media (max-width: 900px) {
    .strip { flex-wrap: wrap; padding: var(--space-xs) var(--space-sm); }
    .room { grid-template-rows: auto minmax(14rem, 42vh) auto auto; }
    .talk { max-width: none; padding: 0 var(--space-sm) var(--space-xs); }
    #log { max-height: 24vh; }
    .floor { flex-wrap: wrap; padding: var(--space-xs) var(--space-sm); gap: var(--space-xs); }
    #text { flex: 1 1 100%; }
  }
  @media (prefers-reduced-motion: reduce) {
    .act { transition: none; }
  }
</style>
</head>
<body data-state="idle" data-name="__NAME__">
<canvas id="field" aria-label="reator"></canvas>
<div class="room">
  <header class="strip">
    <div class="brand">
      <strong>__NAME__</strong>
      <span id="status">pronto</span>
    </div>
    <dl class="systems">
      <div><dt>voz</dt><dd>george</dd></div>
      <div><dt>ritmo</dt><dd>1.08</dd></div>
      <div><dt>fuso</dt><dd>Brasília</dd></div>
      <div><dt>sessão</dt><dd id="sess">à espera do nome</dd></div>
      <div><dt>data</dt><dd id="date">—</dd></div>
    </dl>
    <p id="clock">00:00:00</p>
  </header>
  <div class="well"></div>
  <section class="talk">
    <h2>Conversa</h2>
    <div id="log" aria-live="polite"><p class="empty" id="empty">Diga, Senhor.</p></div>
  </section>
  <form class="floor" id="form">
    <input id="text" autocomplete="off" placeholder="Diga, Senhor" aria-label="frase" />
    <button class="act" type="button" id="voice">ouvir</button>
    <button class="act" type="button" id="mic" aria-label="segurar para falar">falar</button>
    <button class="act" type="submit" id="send">enviar</button>
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
const submitBtn = document.getElementById("send");
const DPR = Math.min(devicePixelRatio || 1, 2);
const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
const labels = { idle: "pronto", listening: "ouvindo", thinking: "pensando", speaking: "falando", ignored: "sem o nome" };
const css = getComputedStyle(document.documentElement);
const tok = (name) => css.getPropertyValue(name).trim();
const ink = {
  paper: tok("--color-paper"),
  paper2: tok("--color-paper-2"),
  ink2: tok("--color-ink-2"),
  ring: tok("--color-ring"),
  accent: tok("--color-accent"),
  core: tok("--color-core"),
  mono: tok("--font-mono"),
};

function resize() {
  const w = window.innerWidth, h = window.innerHeight;
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
  const cx = w / 2, cy = h * 0.46;
  const R = Math.min(w, h) * 0.28;
  const state = document.body.dataset.state;
  const spin = reduce ? 0.6 : now / 1000;
  const dir = state === "listening" ? -1 : 1;
  const pace = state === "thinking" ? 0.9 : state === "speaking" ? 0.45 : 0.16;
  ctx.fillStyle = ink.paper;
  ctx.fillRect(0, 0, w, h);
  const bloom = ctx.createRadialGradient(cx, cy, R * 0.1, cx, cy, R * 2.4);
  bloom.addColorStop(0, ink.paper2);
  bloom.addColorStop(1, ink.paper);
  ctx.fillStyle = bloom;
  ctx.fillRect(0, 0, w, h);

  ctx.save();
  ctx.translate(cx, cy);
  ctx.globalAlpha = 0.45;
  ctx.strokeStyle = ink.ring;
  ctx.lineWidth = 1;
  for (let i = 0; i < 96; i++) {
    const a = (i / 96) * Math.PI * 2;
    const inner = R * 1.22;
    const outer = i % 8 === 0 ? R * 1.36 : R * 1.28;
    ctx.beginPath();
    ctx.moveTo(Math.cos(a) * inner, Math.sin(a) * inner);
    ctx.lineTo(Math.cos(a) * outer, Math.sin(a) * outer);
    ctx.stroke();
  }
  ctx.restore();

  const base = spin * pace * dir;
  ctx.globalAlpha = 0.9;
  for (let s = 0; s < 3; s++) {
    ring(cx, cy, R, base + s * (Math.PI * 2 / 3), Math.PI / 2.4, 1.5, ink.ring);
  }
  ctx.globalAlpha = 0.55;
  for (let s = 0; s < 3; s++) {
    ring(cx, cy, R * 0.72, -base * 1.3 + s * (Math.PI * 2 / 3), Math.PI / 3, 1, ink.ring);
  }
  const load = state === "thinking" ? 0.72 : state === "listening" ? 0.5 : state === "speaking" ? 0.4 + level * 0.55 : 0.22;
  ctx.globalAlpha = 1;
  ring(cx, cy, R * 0.46, -Math.PI / 2, Math.PI * 2 * load, 2, ink.accent);

  ctx.save();
  ctx.translate(cx, cy);
  ctx.rotate(base * 0.35);
  ctx.beginPath();
  for (let i = 0; i < 3; i++) {
    const a = -Math.PI / 2 + i * (Math.PI * 2 / 3);
    const x = Math.cos(a) * R * 0.26, y = Math.sin(a) * R * 0.26;
    if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
  }
  ctx.closePath();
  ctx.strokeStyle = ink.core;
  ctx.lineWidth = 1.25;
  ctx.stroke();
  ctx.restore();

  const coreR = R * (0.07 + (state === "speaking" ? level * 0.04 : 0));
  const core = ctx.createRadialGradient(cx, cy, 0, cx, cy, coreR * 4);
  core.addColorStop(0, ink.core);
  core.addColorStop(0.4, ink.ring);
  core.addColorStop(1, ink.paper);
  ctx.globalAlpha = 0.85;
  ctx.fillStyle = core;
  ctx.beginPath();
  ctx.arc(cx, cy, coreR * 4, 0, Math.PI * 2);
  ctx.fill();
  ctx.globalAlpha = 1;
  ctx.fillStyle = ink.core;
  ctx.beginPath();
  ctx.arc(cx, cy, coreR, 0, Math.PI * 2);
  ctx.fill();

  ctx.fillStyle = ink.ink2;
  ctx.font = "500 12px " + ink.mono;
  ctx.textAlign = "center";
  ctx.fillText((labels[state] || state).toUpperCase(), cx, cy + R * 1.55);
  ctx.globalAlpha = 1;
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
  if (busy) text.dataset.state = "loading";
  else if (text.dataset.state === "loading") delete text.dataset.state;
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
  if (cls === "user") p.dataset.speaker = "senhor";
  if (cls === "agent") p.dataset.speaker = "orion";
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
