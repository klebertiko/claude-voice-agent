"""Painel do Orion: grafo em tela cheia e a conversa na lateral. Sem vídeo."""

from __future__ import annotations

_PAGE = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>__NAME__</title>
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600&display=swap" rel="stylesheet" />
<style>
  :root {
    --paper: #07090d;
    --ink: #e7e9ee;
    --muted: #9aa3b2;
    --line: #1f2937;
    --chip: #0d1320;
    --accent: #34d399;
    --accent-ink: #04281a;
    --dock: 300px;
    --font: "Geist", ui-sans-serif, sans-serif;
  }
  * { box-sizing: border-box; }
  html, body { margin: 0; height: 100%; overflow: hidden; background: var(--paper); }
  body {
    color: var(--ink);
    font-family: var(--font);
    font-size: 15px;
    line-height: 1.45;
  }
  #field { display: block; width: 100%; height: 100%; cursor: grab; touch-action: none; }
  #field.drag { cursor: grabbing; }
  .vignette {
    position: fixed; inset: 0; z-index: 1; pointer-events: none;
    background: radial-gradient(ellipse at 42% 48%, transparent 42%, rgba(0,0,0,.55) 100%);
  }
  .brand, .dock { position: fixed; z-index: 4; }
  .brand { top: 18px; left: 20px; }
  .brand a {
    color: var(--ink); text-decoration: none;
    font-weight: 600; font-size: 20px; letter-spacing: -0.03em;
  }
  .brand p {
    margin: 2px 0 0; color: var(--muted); font-size: 12px; letter-spacing: 0.08em;
    text-transform: uppercase;
  }
  body[data-state="listening"] .brand p,
  body[data-state="speaking"] .brand p { color: var(--accent); }
  .legend {
    display: flex; flex-wrap: wrap; gap: 4px 12px;
    padding: 0 0 4px;
  }
  .legend .row { display: flex; align-items: center; gap: 6px; color: #cbd5e1; font-size: 12px; }
  .legend .dot { width: 9px; height: 9px; border-radius: 50%; }
  .dock {
    top: 12px; right: 12px; bottom: 12px; width: var(--dock);
    display: flex; flex-direction: column; gap: 10px;
    background: rgba(10,13,18,.94);
    border: 1px solid var(--line);
    border-radius: 16px;
    padding: 14px;
    min-width: 0;
  }
  .dock h2 {
    margin: 0; font-size: 13px; font-weight: 500; letter-spacing: 0.12em;
    text-transform: uppercase; color: var(--muted);
  }
  #log {
    flex: 1; min-height: 0; overflow: auto; padding-right: 4px;
  }
  #log p { margin: 0 0 10px; }
  #log .empty {
    margin: auto; text-align: center; max-width: 18ch;
    color: #d5dbe6; font-size: 18px; letter-spacing: -0.02em;
  }
  #log .meta { color: var(--muted); font-size: 14px; }
  #log .user { color: #d7deea; }
  #log .agent { color: var(--ink); }
  .find, .composer { display: flex; gap: 8px; }
  .composer { flex-wrap: wrap; }
  input, button {
    font: inherit; color: var(--ink);
  }
  input {
    min-width: 0; min-height: 40px; flex: 1;
    background: var(--chip); border: 1px solid #283548; border-radius: 999px;
    padding: 0 14px;
  }
  input:focus-visible, button:focus-visible, .brand a:focus-visible {
    outline: 2px solid var(--accent); outline-offset: 2px;
  }
  button {
    min-height: 40px; padding: 0 14px; white-space: nowrap; cursor: pointer;
    background: #111827; color: #d1d5db; border: 1px solid #283548; border-radius: 999px;
  }
  button:hover { background: #1c2a3f; }
  button:active { transform: translateY(1px); }
  button:disabled { opacity: 0.4; cursor: not-allowed; }
  button.primary { background: var(--accent); color: var(--accent-ink); border-color: var(--accent); font-weight: 600; }
  button.primary:hover { background: #5ee0b0; }
  button[data-state="error"] { border-color: #f0a0a8; color: #f0a0a8; }
  button[data-state="success"] { border-color: var(--accent); }
  .composer .primary { flex: 1 1 100%; }
  @media (max-width: 800px) {
    .dock {
      top: auto; left: 8px; right: 8px; bottom: 8px; width: auto; height: 46vh;
    }
    .brand { top: 12px; left: 12px; }
  }
  @media (max-width: 414px) {
    .composer { display: grid; grid-template-columns: 1fr 1fr; }
    .composer input, .composer .primary { grid-column: 1 / -1; }
  }
  @media (prefers-reduced-motion: reduce) {
    button:active { transform: none; }
  }
</style>
</head>
<body data-state="idle" data-name="__NAME__">
<canvas id="field" aria-label="mapa da sessão"></canvas>
<div class="vignette" aria-hidden="true"></div>
<header class="brand">
  <a href="#log">__NAME__</a>
  <p id="status">pronto</p>
</header>
<aside class="dock">
  <div class="legend" id="legend" aria-label="grupos"></div>
  <h2>conversa</h2>
  <div id="log" aria-live="polite"><p class="empty" id="empty">chame pelo nome.</p></div>
  <form class="find" id="find-form">
    <input id="find" type="search" autocomplete="off" placeholder="achar na sessão" aria-label="achar na sessão" />
  </form>
  <form class="composer" id="form">
    <input id="text" autocomplete="off" placeholder="diga __WAKE__, e depois a frase" aria-label="frase" />
    <button class="primary" type="submit">enviar</button>
    <button type="button" id="voice">ouvir</button>
    <button type="button" id="mic" aria-label="segurar para falar">falar</button>
  </form>
</aside>
<audio id="player"></audio>
<script>
const NAME = document.body.dataset.name || "Orion";
const canvas = document.getElementById("field");
const ctx = canvas.getContext("2d");
const statusEl = document.getElementById("status");
const logEl = document.getElementById("log");
const emptyEl = document.getElementById("empty");
const form = document.getElementById("form");
const text = document.getElementById("text");
const player = document.getElementById("player");
const micBtn = document.getElementById("mic");
const voiceBtn = document.getElementById("voice");
const submitBtn = form.querySelector("[type=submit]");
const legendEl = document.getElementById("legend");
const DPR = Math.min(devicePixelRatio || 1, 2);
const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
const labels = { idle: "pronto", listening: "ouvindo", thinking: "pensando", speaking: "falando", ignored: "sem o nome" };
const GROUPS = [
  { id: "orion", name: "orion", color: "#f4efe4" },
  { id: "escuta", name: "escuta", color: "#8eb6ff" },
  { id: "voz", name: "voz", color: "#f0c36a" },
  { id: "tempo", name: "tempo", color: "#f0a0c0" },
  { id: "sessao", name: "sessão", color: "#5ee0b5" },
];
const HOMES = {
  orion: [0, 0],
  escuta: [-70, -48],
  voz: [74, -36],
  tempo: [-64, 58],
  sessao: [68, 52],
};
let seed = 11;
function rnd() { seed = (seed * 16807) % 2147483647; return (seed - 1) / 2147483646; }
const nodes = [];
const links = [];
let selected = null;
let hover = null;
let view = { x: 0, y: 0, k: 1 };
let userCam = false;
let W = 1, H = 1;

function addNode(group, label, r, home) {
  const h = home || HOMES[group];
  const n = {
    i: nodes.length, g: group, label: label || "",
    r: r, x: h[0] + (rnd() - 0.5) * 80, y: h[1] + (rnd() - 0.5) * 80,
    vx: 0, vy: 0, homeX: h[0], homeY: h[1],
  };
  nodes.push(n);
  return n;
}
function link(a, b) { links.push({ source: a, target: b }); }

const hub = {};
for (const g of GROUPS) {
  const big = g.id === "orion" ? 9 : 6.2;
  hub[g.id] = addNode(g.id, g.id === "orion" ? NAME : g.name, big);
  legendEl.insertAdjacentHTML("beforeend", `<div class="row"><span class="dot" style="background:${g.color}"></span>${g.name}</div>`);
}
for (const id of ["escuta", "voz", "tempo", "sessao"]) link(hub.orion, hub[id]);
const words = {
  escuta: ["nome", "janela", "acordo"],
  voz: ["kokoro", "pt-br", "ritmo"],
  tempo: ["hora", "data", "hoje"],
  sessao: ["fala", "resposta"],
};
for (const [g, list] of Object.entries(words)) {
  for (const word of list) link(hub[g], addNode(g, word, 3.4));
}
for (const g of GROUPS) {
  const kids = nodes.filter((n) => n.g === g.id && n !== hub[g.id]);
  const count = 28;
  for (let i = 0; i < count; i++) {
    const parent = kids.length && rnd() > 0.25 ? kids[Math.floor(rnd() * kids.length)] : hub[g.id];
    const dust = addNode(g.id, "", 1.15 + rnd() * 3.1, [parent.homeX + (rnd() - 0.5) * 40, parent.homeY + (rnd() - 0.5) * 40]);
    link(parent, dust);
  }
}
for (let i = 0; i < 48; i++) {
  const a = nodes[Math.floor(rnd() * nodes.length)];
  const b = nodes[Math.floor(rnd() * nodes.length)];
  if (a !== b) link(a, b);
}
const labeled = nodes.filter((n) => n.label && n.r < 6);
for (let i = 0; i < labeled.length; i++) {
  link(labeled[i], labeled[(i + 3) % labeled.length]);
}

function step(times) {
  const list = nodes;
  for (let s = 0; s < times; s++) {
    for (const n of list) { n.ax = 0; n.ay = 0; }
    for (let i = 0; i < list.length; i++) {
      const a = list[i];
      for (let j = i + 1; j < list.length; j++) {
        const b = list[j];
        let dx = b.x - a.x, dy = b.y - a.y;
        let d2 = dx * dx + dy * dy + 8;
        let d = Math.sqrt(d2);
        let f = 900 / d2;
        let fx = f * dx / d, fy = f * dy / d;
        a.ax -= fx; a.ay -= fy; b.ax += fx; b.ay += fy;
      }
    }
    for (const l of links) {
      const a = l.source, b = l.target;
      let dx = b.x - a.x, dy = b.y - a.y;
      let dist = Math.hypot(dx, dy) || 0.01;
      let diff = (dist - (a.r + b.r + 62)) * 0.06;
      let fx = diff * dx / dist, fy = diff * dy / dist;
      a.ax += fx; a.ay += fy; b.ax -= fx; b.ay -= fy;
    }
    for (const n of list) {
      if (n.pinx != null) { n.x = n.pinx; n.y = n.piny; n.vx = 0; n.vy = 0; continue; }
      n.ax += (n.homeX - n.x) * 0.006;
      n.ay += (n.homeY - n.y) * 0.006;
      n.ax += -n.x * 0.004;
      n.ay += -n.y * 0.004;
      n.vx = (n.vx + n.ax) * 0.55;
      n.vy = (n.vy + n.ay) * 0.55;
      n.x += n.vx; n.y += n.vy;
    }
  }
}
step(420);

function resize() {
  W = innerWidth; H = innerHeight;
  canvas.width = Math.floor(W * DPR); canvas.height = Math.floor(H * DPR);
  canvas.style.width = W + "px"; canvas.style.height = H + "px";
  if (!userCam) fit();
}
function stage() {
  const dock = document.querySelector(".dock").getBoundingClientRect();
  if (dock.width > W * 0.8) {
    return { cx: W / 2, cy: Math.max(80, (H - dock.height) / 2), vw: W - 36, vh: Math.max(120, H - dock.height - 36) };
  }
  return { cx: (W - dock.width) / 2, cy: H / 2, vw: W - dock.width - 36, vh: H - 36 };
}
function fit() {
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
  for (const n of nodes) {
    minX = Math.min(minX, n.x - n.r); minY = Math.min(minY, n.y - n.r);
    maxX = Math.max(maxX, n.x + n.r); maxY = Math.max(maxY, n.y + n.r);
  }
  const box = stage();
  const bw = Math.max(40, maxX - minX), bh = Math.max(40, maxY - minY);
  view.k = Math.max(0.45, Math.min(1.8, Math.min(box.vw / bw, box.vh / bh)));
  view.x = (minX + maxX) / 2;
  view.y = (minY + maxY) / 2;
}
function world(px, py) {
  const box = stage();
  return [(px - box.cx) / view.k + view.x, (py - box.cy) / view.k + view.y];
}
function hit(px, py) {
  const [x, y] = world(px, py);
  let best = null, bestD = 14 / view.k;
  for (const n of nodes) {
    const d = Math.hypot(n.x - x, n.y - y);
    if (d < n.r + bestD) { best = n; bestD = d; }
  }
  return best;
}
const colorOf = Object.fromEntries(GROUPS.map((g) => [g.id, g.color]));
function draw() {
  ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
  ctx.fillStyle = "#07090d";
  ctx.fillRect(0, 0, W, H);
  const box = stage();
  ctx.translate(box.cx, box.cy);
  ctx.scale(view.k, view.k);
  ctx.translate(-view.x, -view.y);
  const focus = selected || hover;
  let lit = null;
  if (focus) {
    lit = new Set([focus.i]);
    for (const l of links) {
      if (l.source === focus) lit.add(l.target.i);
      if (l.target === focus) lit.add(l.source.i);
    }
  }
  ctx.lineWidth = 1.05 / view.k;
  for (const l of links) {
    const on = lit && lit.has(l.source.i) && lit.has(l.target.i);
    ctx.strokeStyle = lit ? (on ? "rgba(170,196,220,.85)" : "rgba(90,110,140,.06)") : "rgba(150,175,205,.42)";
    ctx.beginPath();
    ctx.moveTo(l.source.x, l.source.y);
    ctx.lineTo(l.target.x, l.target.y);
    ctx.stroke();
  }
  for (const n of nodes) {
    const dim = lit && !lit.has(n.i);
    ctx.globalAlpha = dim ? 0.1 : 1;
    ctx.fillStyle = colorOf[n.g];
    ctx.beginPath();
    ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.globalAlpha = 1;
  ctx.textAlign = "center";
  ctx.font = `500 ${12 / view.k}px Geist, ui-sans-serif, sans-serif`;
  ctx.fillStyle = "rgba(231,233,238,.9)";
  for (const n of nodes) {
    if (!n.label) continue;
    const show = lit ? lit.has(n.i) : (n.r > 3 || view.k > 1.35);
    if (!show) continue;
    ctx.fillText(n.label, n.x, n.y - n.r - 6 / view.k);
  }
  ctx.setTransform(1, 0, 0, 1, 0, 0);
}

let panning = false, dragN = null, mx = 0, my = 0, moved = 0;
canvas.addEventListener("wheel", (e) => {
  e.preventDefault();
  userCam = true;
  const k2 = Math.max(0.25, Math.min(4, view.k * Math.exp(-e.deltaY * 0.0014)));
  const [wx, wy] = world(e.clientX, e.clientY);
  const box = stage();
  view.x = wx - (e.clientX - box.cx) / k2;
  view.y = wy - (e.clientY - box.cy) / k2;
  view.k = k2;
}, { passive: false });
canvas.addEventListener("pointerdown", (e) => {
  moved = 0; mx = e.clientX; my = e.clientY;
  dragN = hit(e.clientX, e.clientY);
  if (dragN) { dragN.pinx = dragN.x; dragN.piny = dragN.y; }
  else panning = true;
  canvas.classList.add("drag");
  canvas.setPointerCapture(e.pointerId);
});
canvas.addEventListener("pointermove", (e) => {
  moved += Math.abs(e.clientX - mx) + Math.abs(e.clientY - my);
  if (dragN) {
    const [wx, wy] = world(e.clientX, e.clientY);
    dragN.pinx = wx; dragN.piny = wy; dragN.x = wx; dragN.y = wy;
  } else if (panning) {
    userCam = true;
    view.x -= (e.clientX - mx) / view.k;
    view.y -= (e.clientY - my) / view.k;
  } else hover = hit(e.clientX, e.clientY);
  mx = e.clientX; my = e.clientY;
});
canvas.addEventListener("pointerup", (e) => {
  if (moved < 5) {
    const n = hit(e.clientX, e.clientY);
    selected = n && n !== selected ? n : null;
  }
  if (dragN) { dragN.pinx = null; dragN.piny = null; }
  dragN = null; panning = false;
  canvas.classList.remove("drag");
});
addEventListener("keydown", (e) => {
  if (e.target.tagName === "INPUT") return;
  if (e.key === "Escape") selected = null;
});
document.getElementById("find-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const q = document.getElementById("find").value.trim().toLowerCase();
  const input = document.getElementById("find");
  if (!q) return;
  const n = nodes.find((node) => node.label && node.label.toLowerCase().includes(q));
  if (!n) { input.dataset.state = "error"; return; }
  delete input.dataset.state;
  selected = n; userCam = true; view.x = n.x; view.y = n.y; view.k = Math.max(view.k, 1.8);
});

function frame() {
  draw();
  requestAnimationFrame(frame);
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
function remember(phrase) {
  const clean = (phrase || "").trim();
  if (!clean) return;
  const label = clean.length > 26 ? clean.slice(0, 25) + "…" : clean;
  const n = addNode("sessao", label, 3.6, HOMES.sessao);
  link(hub.sessao, n);
  step(28);
  if (!userCam) fit();
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
  if (data.heard) { addLine("user", data.heard); remember(data.heard); }
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
  if (data.reply) { addLine("agent", data.reply); remember(data.reply); }
  if (data.audio_b64) await playWav(data.audio_b64);
  else setState("idle");
  if (sourceBtn && data.reply) mark(sourceBtn, "success");
}
form.addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const value = text.value.trim();
  if (!value) { text.dataset.state = "error"; return; }
  delete text.dataset.state;
  text.value = "";
  setState("thinking");
  try { await showTurn(await post("/api/turn", { text: value }), submitBtn); }
  catch (err) { setState("idle"); addLine("meta", "Não consegui falar agora."); mark(submitBtn, "error"); }
});
voiceBtn.addEventListener("click", async () => {
  setState("thinking");
  try {
    const data = await post("/api/greeting", {});
    if (data.reply) { addLine("agent", data.reply); remember(data.reply); }
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
  setState("listening");
}
async function stopMic(ev) {
  if (!capturing) return;
  ev.preventDefault();
  capturing = false;
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
