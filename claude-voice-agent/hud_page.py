"""Painel do Orion: conversa em casca escura, no registro de um painel de agente.

Sem vídeo. A placa e o grafo saíram; a tela é a conversa.
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
    --bg: #0e0e16;
    --bg2: #181822;
    --bg3: #22222e;
    --border: #36364c;
    --accent: #ff7a3c;
    --accent-solid: #ff7a3c;
    --accent-ink: #ffab81;
    --accent-wash-2: rgba(255, 105, 45, 0.12);
    --accent-line: rgba(255, 130, 67, 0.30);
    --text: #f3f3fb;
    --text2: #c0c0da;
    --text3: #9a9ab6;
    --green: #34d36b;
    --red: #f4565a;
    --hairline: rgba(255, 255, 255, 0.08);
    --surface-1: rgba(255, 255, 255, 0.025);
    --on-accent: #1a1400;
    --font: "Be Vietnam Pro", "Segoe UI", sans-serif;
  }
  * { box-sizing: border-box; }
  html, body { margin: 0; height: 100%; background: var(--bg); color: var(--text); }
  body { font-family: var(--font); font-size: 16px; line-height: 1.45; }
  .app { display: grid; grid-template-columns: 220px minmax(0, 1fr); height: 100%; }
  .side {
    background: var(--bg2);
    border-right: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    padding: 18px 14px;
    min-width: 0;
  }
  .brand { display: flex; align-items: center; gap: 10px; padding: 4px 6px 16px; }
  .mark {
    width: 28px; height: 28px; flex: none;
    background: var(--accent);
    color: var(--on-accent);
    font-weight: 700;
    display: flex; align-items: center; justify-content: center;
    border-radius: 8px;
  }
  .brand strong { font-size: 14px; letter-spacing: 0.18em; font-weight: 700; }
  .brand span { display: block; color: var(--text3); font-size: 12px; letter-spacing: 0; font-weight: 400; }
  .nav {
    display: flex; align-items: center; gap: 8px;
    padding: 10px 10px;
    border-radius: 8px;
    background: var(--accent-wash-2);
    color: var(--text);
    font-weight: 600;
    font-size: 14px;
  }
  .side .grow { flex: 1; }
  #status { color: var(--text3); font-size: 13px; padding: 8px 10px; }
  body[data-state="listening"] #status { color: var(--accent-ink); }
  body[data-state="speaking"] #status { color: var(--green); }
  body[data-state="ignored"] #status { color: var(--red); }
  .main { display: flex; flex-direction: column; min-width: 0; min-height: 0; }
  .top {
    height: 52px;
    display: flex; align-items: center; justify-content: space-between;
    padding: 0 20px;
    background: var(--bg2);
    border-bottom: 1px solid var(--border);
  }
  .top h1 { margin: 0; font-size: 16px; font-weight: 600; }
  #clock { color: var(--text2); font-size: 13px; font-variant-numeric: tabular-nums; }
  #log {
    flex: 1; min-height: 0; overflow: auto;
    display: flex; flex-direction: column; gap: 10px;
    padding: 18px 20px 8px;
  }
  #log .empty { margin: auto; color: var(--text3); font-size: 15px; }
  #log .user, #log .agent, #log .meta { margin: 0; max-width: min(72ch, 100%); }
  #log .user {
    align-self: flex-end;
    background: var(--accent-wash-2);
    border: 1px solid var(--accent-line);
    border-radius: 12px 12px 3px 12px;
    padding: 8px 12px;
  }
  #log .agent {
    align-self: flex-start;
    background: var(--surface-1);
    border: 1px solid var(--hairline);
    border-radius: 3px 12px 12px 12px;
    padding: 14px 16px;
    line-height: 1.65;
  }
  #log .meta { align-self: center; color: var(--text3); font-size: 13px; background: none; border: 0; padding: 2px 8px; }
  .bar {
    display: flex; align-items: flex-end; gap: 8px;
    margin: 8px 16px 16px;
    padding: 8px;
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 18px;
  }
  #text {
    flex: 1; min-width: 0;
    background: var(--bg3);
    border: 1px solid var(--border);
    border-radius: 12px;
    color: var(--text);
    font: inherit;
    font-size: 16px;
    padding: 11px 14px;
    outline: none;
  }
  #text:focus { border-color: var(--accent-line); }
  #text::placeholder { color: var(--text3); }
  button {
    font: inherit; font-weight: 600; font-size: 13px;
    cursor: pointer;
    border: 1px solid var(--border);
    background: var(--bg3);
    color: var(--text2);
    height: 44px;
    padding: 0 12px;
    border-radius: 12px;
    flex: none;
  }
  button:hover { border-color: var(--accent); color: var(--accent); }
  button:disabled { opacity: 0.4; cursor: not-allowed; }
  button.primary {
    background: var(--accent-solid);
    border-color: var(--accent-solid);
    color: var(--on-accent);
    width: 44px; padding: 0;
  }
  button.primary:hover { opacity: 0.88; color: var(--on-accent); }
  button[data-state="error"] { border-color: var(--red); color: var(--red); }
  button[data-state="success"] { border-color: var(--green); color: var(--green); }
  #mic[data-hot="1"] { border-color: var(--red); color: var(--red); }
  button:focus-visible, #text:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
  @media (max-width: 800px) {
    .app { grid-template-columns: 1fr; grid-template-rows: auto 1fr; }
    .side { flex-direction: row; align-items: center; gap: 12px; border-right: 0; border-bottom: 1px solid var(--border); padding: 10px 12px; }
    .brand { padding: 0; }
    .nav, .side .grow { display: none; }
    #status { margin-left: auto; }
    .bar { margin: 8px 10px 10px; border-radius: 24px; }
    #text { border: 0; background: transparent; }
  }
  @media (prefers-reduced-motion: reduce) {
    * { scroll-behavior: auto; }
  }
</style>
</head>
<body data-state="idle" data-name="__NAME__">
<canvas id="field" hidden></canvas>
<div class="app">
  <aside class="side">
    <div class="brand">
      <div class="mark" aria-hidden="true">O</div>
      <div>
        <strong>__NAME__</strong>
        <span id="status">pronto</span>
      </div>
    </div>
    <div class="nav">Conversa</div>
    <div class="grow"></div>
  </aside>
  <section class="main">
    <header class="top">
      <h1>Conversa</h1>
      <div id="clock">00:00:00</div>
    </header>
    <div id="log" aria-live="polite"><p class="empty" id="empty">Diga, Senhor.</p></div>
    <form class="bar" id="form">
      <input id="text" autocomplete="off" placeholder="Diga, Senhor" aria-label="frase" />
      <button type="button" id="voice">ouvir</button>
      <button type="button" id="mic" aria-label="segurar para falar">falar</button>
      <button class="primary" type="submit" aria-label="enviar">↑</button>
    </form>
  </section>
</div>
<audio id="player"></audio>
<script>
const statusEl = document.getElementById("status");
const clockEl = document.getElementById("clock");
const logEl = document.getElementById("log");
const emptyEl = document.getElementById("empty");
const form = document.getElementById("form");
const text = document.getElementById("text");
const player = document.getElementById("player");
const micBtn = document.getElementById("mic");
const voiceBtn = document.getElementById("voice");
const submitBtn = form.querySelector("[type=submit]");
const labels = {
  idle: "pronto",
  listening: "ouvindo",
  thinking: "pensando",
  speaking: "falando",
  ignored: "sem o nome"
};
function tickClock() {
  clockEl.textContent = new Intl.DateTimeFormat("pt-BR", {
    timeZone: "America/Sao_Paulo",
    hour: "2-digit", minute: "2-digit", second: "2-digit", hourCycle: "h23"
  }).format(new Date());
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
    addLine("meta", "Não ouvi o nome. Diga __WAKE__.");
    if (sourceBtn) mark(sourceBtn, "error");
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
tickClock();
setInterval(tickClock, 1000);
</script>
</body>
</html>
"""


def render_page(name: str, wake: str) -> str:
    """Injeta o nome da persona. O microfone pede só áudio."""
    safe_name = name.replace("<", "").replace(">", "").replace('"', "").replace("&", "")
    safe_wake = wake.replace("<", "").replace(">", "").replace('"', "").replace("&", "")
    return _PAGE.replace("__NAME__", safe_name).replace("__WAKE__", safe_wake)
