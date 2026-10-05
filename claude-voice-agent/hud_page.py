"""Painel do Orion: o reator é o centro, a casa fica nas laterais.

Sem vídeo. Uma ordem no computador aparece inteira e espera permissão.
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
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Rajdhani:wght@500;600;700&display=swap" rel="stylesheet" />
<style>
  :root {
    color-scheme: dark;
    --color-paper: oklch(0.12 0.02 250);
    --color-paper-2: oklch(0.18 0.025 250);
    --color-ink: oklch(0.94 0.015 220);
    --color-ink-2: oklch(0.74 0.03 220);
    --color-rule: oklch(0.42 0.04 230);
    --color-accent: oklch(0.82 0.13 85);
    --color-ring: oklch(0.82 0.08 220);
    --color-core: oklch(0.97 0.04 200);
    --color-copper: oklch(0.55 0.11 68);
    --color-copper-2: oklch(0.78 0.12 82);
    --color-plasma: oklch(0.88 0.1 205);
    --color-void: oklch(0.07 0.03 265);
    --color-focus: oklch(0.86 0.08 220);
    --color-ok: oklch(0.8 0.1 165);
    --color-bad: oklch(0.7 0.15 25);
    --font-display: "Rajdhani", "Segoe UI", sans-serif;
    --font-body: "Rajdhani", "Segoe UI", sans-serif;
    --font-mono: "IBM Plex Mono", ui-monospace, monospace;
    --space-3xs: 0.25rem;
    --space-2xs: 0.5rem;
    --space-xs: 0.75rem;
    --space-sm: 1rem;
    --space-md: 1.5rem;
    --space-lg: 2rem;
    --text-xs: 0.75rem;
    --text-sm: 0.875rem;
    --text-md: 1.125rem;
    --text-lg: 1.5rem;
    --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
    --dur-short: 180ms;
  }
  * { box-sizing: border-box; }
  html, body { margin: 0; min-height: 100%; overflow-x: clip; background: var(--color-paper); color: var(--color-ink); }
  body { font-family: var(--font-body); font-size: var(--text-md); font-style: normal; }
  #field { position: fixed; inset: 0; width: 100%; height: 100%; z-index: 0; display: block; }
  .room {
    position: relative; z-index: 1; min-height: 100vh; min-width: 0;
    display: grid;
    grid-template-columns: 17rem minmax(0, 1fr) 24rem;
    grid-template-rows: auto minmax(0, 1fr) auto auto;
  }
  .strip, .telemetry, .talk, .floor, #permit {
    background: color-mix(in oklch, var(--color-paper) 86%, transparent);
  }
  .strip {
    grid-column: 1 / -1;
    display: flex; align-items: baseline; justify-content: space-between;
    gap: var(--space-sm); padding: var(--space-xs) var(--space-md);
    border-bottom: 1px solid var(--color-rule);
  }
  .brand { display: flex; align-items: baseline; gap: var(--space-sm); min-width: 0; }
  .brand strong {
    font-family: var(--font-display); font-weight: 700; font-style: normal;
    font-size: var(--text-lg); letter-spacing: 0.22em;
  }
  #status { font-family: var(--font-mono); font-size: var(--text-xs); color: var(--color-ring); letter-spacing: 0.14em; }
  body[data-state="listening"] #status, body[data-state="speaking"] #status { color: var(--color-accent); }
  body[data-state="ignored"] #status { color: var(--color-bad); }
  #clock { margin: 0; font-family: var(--font-mono); font-size: var(--text-md); color: var(--color-ring); font-variant-numeric: tabular-nums; }
  .telemetry { grid-column: 1; grid-row: 2; border-right: 1px solid var(--color-rule); padding: var(--space-sm) var(--space-md); }
  .talk { grid-column: 3; grid-row: 2; border-left: 1px solid var(--color-rule); display: flex; flex-direction: column; min-width: 0; min-height: 0; padding: var(--space-sm) var(--space-md); }
  .well {
    grid-column: 2; grid-row: 2; position: relative; min-width: 0; min-height: 16rem;
    cursor: grab; touch-action: none;
  }
  .well:active { cursor: grabbing; }
  #sky-read {
    position: absolute; left: var(--space-sm); right: var(--space-sm); bottom: var(--space-sm);
    margin: 0; pointer-events: none; text-align: center;
    font-family: var(--font-mono); font-size: var(--text-xs); letter-spacing: 0.06em;
    color: var(--color-core);
  }
  h2 {
    margin: 0 0 var(--space-sm); font-family: var(--font-mono); font-size: var(--text-xs);
    font-weight: 500; font-style: normal; letter-spacing: 0.16em; text-transform: uppercase; color: var(--color-ink-2);
  }
  .systems { margin: 0; }
  .systems div {
    display: flex; justify-content: space-between; gap: var(--space-xs);
    padding: var(--space-2xs) 0; border-bottom: 1px solid color-mix(in oklch, var(--color-rule) 55%, transparent);
  }
  .systems dt { font-family: var(--font-mono); font-size: var(--text-xs); color: var(--color-ink-2); font-weight: 400; }
  .systems dd { margin: 0; font-family: var(--font-mono); font-size: var(--text-xs); text-align: right; }
  #log { flex: 1; min-height: 0; overflow: auto; display: flex; flex-direction: column; gap: var(--space-2xs); }
  #log p { margin: 0; line-height: 1.35; overflow-wrap: anywhere; min-width: 0; font-size: var(--text-md); }
  #log .empty, #log .meta { color: var(--color-ink-2); font-size: var(--text-sm); }
  #log p[data-speaker]::before {
    content: attr(data-speaker);
    display: block; font-family: var(--font-mono); font-size: var(--text-xs);
    letter-spacing: 0.12em; color: var(--color-ring);
  }
  #permit {
    grid-column: 1 / -1;
    display: flex; align-items: center; gap: var(--space-sm);
    padding: var(--space-xs) var(--space-md);
    border-top: 1px solid var(--color-accent);
  }
  #permit[hidden] { display: none; }
  #permit p { margin: 0; font-family: var(--font-mono); font-size: var(--text-xs); letter-spacing: 0.14em; color: var(--color-accent); }
  #permit-cmd {
    flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
    font-family: var(--font-mono); font-size: var(--text-sm); color: var(--color-ink);
  }
  .floor {
    grid-column: 1 / -1;
    display: flex; align-items: center; gap: var(--space-sm);
    padding: var(--space-xs) var(--space-md);
    border-top: 1px solid var(--color-rule);
  }
  #text {
    flex: 1; min-width: 0; background: transparent; color: var(--color-ink);
    border: 0; border-bottom: 1px solid var(--color-rule); border-radius: 0;
    font-family: var(--font-mono); font-size: var(--text-sm); padding: var(--space-2xs) 0; outline: none;
  }
  #text::placeholder { color: var(--color-ink-2); }
  #text:hover { border-bottom-color: var(--color-ink-2); }
  #text:focus-visible, .act:focus-visible { outline: 2px solid var(--color-focus); outline-offset: 2px; }
  #text:active { color: var(--color-ink); }
  #text:disabled, .act:disabled { color: var(--color-rule); cursor: not-allowed; }
  #text[data-state="loading"] { border-bottom-color: var(--color-ring); }
  #text[data-state="error"] { border-bottom-color: var(--color-bad); }
  #text[data-state="success"] { border-bottom-color: var(--color-ok); }
  .act {
    font-family: var(--font-mono); font-size: var(--text-xs); font-weight: 500;
    letter-spacing: 0.14em; text-transform: uppercase; white-space: nowrap;
    cursor: pointer; padding: var(--space-2xs) 0; border: 0; border-radius: 0;
    background: transparent; color: var(--color-ink-2);
    transition: color var(--dur-short) var(--ease-out);
  }
  .act:hover { color: var(--color-accent); }
  .act:active { color: var(--color-ink); }
  .act[data-state="loading"] { color: var(--color-ring); }
  .act[data-state="error"] { color: var(--color-bad); }
  .act[data-state="success"] { color: var(--color-ok); }
  #allow { color: var(--color-accent); }
  #mic[data-hot="1"] { color: var(--color-bad); }
  @media (max-width: 900px) {
    .room { grid-template-columns: 1fr; grid-template-rows: auto auto minmax(16rem, 48vh) minmax(8rem, 1fr) auto auto; }
    .telemetry, .well, .talk, .strip, #permit, .floor { grid-column: 1; grid-row: auto; }
    .telemetry, .talk { border: 0; border-top: 1px solid var(--color-rule); }
    .systems { display: flex; flex-wrap: wrap; gap: var(--space-2xs) var(--space-md); }
    .systems div { border: 0; padding: 0; }
    #log { max-height: 24vh; }
    .floor { flex-wrap: wrap; }
    #text { flex: 1 1 100%; }
  }
  @media (prefers-reduced-motion: reduce) { .act { transition: none; } }
</style>
</head>
<body data-state="idle" data-name="__NAME__" data-load="0">
<canvas id="field" aria-label="reator e constelação"></canvas>
<div class="room">
  <header class="strip">
    <div class="brand">
      <strong>__NAME__</strong>
      <span id="status">pronto</span>
    </div>
    <p id="clock">00:00:00</p>
  </header>
  <aside class="telemetry">
    <h2>Casa</h2>
    <dl class="systems">
      <div><dt>cérebro</dt><dd id="brain">—</dd></div>
      <div><dt>codex</dt><dd id="brain-codex">ausente</dd></div>
      <div><dt>cursor</dt><dd id="brain-cursor">ausente</dd></div>
      <div><dt>claude</dt><dd id="brain-claude">ausente</dd></div>
      <div><dt>carga</dt><dd id="load">—</dd></div>
      <div><dt>voz</dt><dd id="voice-name">george</dd></div>
      <div><dt>ritmo</dt><dd>1.08</dd></div>
      <div><dt>céu</dt><dd id="sky">0</dd></div>
      <div><dt>lembretes</dt><dd id="notes">0</dd></div>
      <div><dt>fuso</dt><dd>Brasília</dd></div>
      <div><dt>sessão</dt><dd id="sess">à espera do nome</dd></div>
      <div><dt>data</dt><dd id="date">—</dd></div>
    </dl>
  </aside>
  <div class="well"><p id="sky-read">Arraste o céu.</p></div>
  <section class="talk">
    <h2>Conversa</h2>
    <div id="log" aria-live="polite"><p class="empty" id="empty">Diga, Senhor.</p></div>
  </section>
  <div id="permit" hidden>
    <p>permissão</p>
    <code id="permit-cmd"></code>
    <button class="act" type="button" id="allow">permitir</button>
    <button class="act" type="button" id="deny">recusar</button>
  </div>
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
const brainEl = document.getElementById("brain");
const loadEl = document.getElementById("load");
const logEl = document.getElementById("log");
const emptyEl = document.getElementById("empty");
const form = document.getElementById("form");
const text = document.getElementById("text");
const player = document.getElementById("player");
const micBtn = document.getElementById("mic");
const voiceBtn = document.getElementById("voice");
const submitBtn = document.getElementById("send");
const permitEl = document.getElementById("permit");
const permitCmd = document.getElementById("permit-cmd");
const allowBtn = document.getElementById("allow");
const denyBtn = document.getElementById("deny");
const DPR = Math.min(devicePixelRatio || 1, 2);
const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
const labels = { idle: "pronto", listening: "ouvindo", thinking: "pensando", speaking: "falando", ignored: "sem o nome" };
const css = getComputedStyle(document.documentElement);
const tok = (name) => css.getPropertyValue(name).trim();
const ink = {
  paper: tok("--color-paper"), paper2: tok("--color-paper-2"), ink2: tok("--color-ink-2"),
  ring: tok("--color-ring"), accent: tok("--color-accent"), core: tok("--color-core"), mono: tok("--font-mono"),
  copper: tok("--color-copper"), copper2: tok("--color-copper-2"), plasma: tok("--color-plasma"), void: tok("--color-void"),
};
const well = document.querySelector(".well");
const skyRead = document.getElementById("sky-read");
let permitId = "";
let memory = [];
let memoryLinks = [];
let namedOnScreen = [];
let picked = "";
let yawUser = 0;
let pitchUser = 0.36;
let zoom = 1;
let drag = null;
let dragMoved = 0;
const ambient = [];
const nebulas = [
  { x: -1.3, y: 0.35, z: 0.2, r: 1.15, rgb: "96, 64, 210" },
  { x: 1.45, y: -0.15, z: -0.35, r: 1.25, rgb: "32, 150, 196" },
  { x: 0.15, y: 0.55, z: 1.2, r: 0.85, rgb: "196, 122, 48" },
  { x: -0.55, y: -0.45, z: -1.15, r: 1.0, rgb: "64, 48, 150" },
  { x: 0.8, y: 0.1, z: 0.7, r: 0.7, rgb: "70, 120, 190" },
];
(function buildAmbient() {
  let seed = 2166136261;
  const rnd = () => {
    seed = Math.imul(seed ^ 0x9e3779b9, 16777619) >>> 0;
    return seed / 4294967295;
  };
  for (let i = 0; i < 780; i++) {
    const arm = i % 4;
    const along = rnd();
    const theta = along * Math.PI * 5.4 + arm * (Math.PI / 2);
    const rad = 0.25 + Math.pow(along, 0.72) * 2.35;
    const jitter = (rnd() - 0.5) * 0.16;
    ambient.push({
      x: Math.cos(theta) * rad + jitter,
      y: (rnd() - 0.5) * 0.16 * rad,
      z: Math.sin(theta) * rad + (rnd() - 0.5) * 0.12,
      s: rnd() < 0.07 ? 2.1 : 0.7 + rnd() * 0.6,
      warm: rnd() < 0.18,
    });
  }
  for (let i = 0; i < 160; i++) {
    const theta = rnd() * Math.PI * 2;
    const phi = Math.acos(2 * rnd() - 1);
    const rad = 1.8 + rnd() * 1.5;
    ambient.push({
      x: rad * Math.sin(phi) * Math.cos(theta),
      y: rad * Math.cos(phi) * 0.42,
      z: rad * Math.sin(phi) * Math.sin(theta),
      s: 0.45 + rnd() * 0.4,
      warm: rnd() < 0.1,
    });
  }
})();
function hash01(text) {
  let h = 2166136261;
  for (let i = 0; i < text.length; i++) {
    h ^= text.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return (h >>> 0) / 4294967295;
}
function placeNamed(star, index) {
  const spin = hash01(star.id + "a") * Math.PI * 2;
  const arm = index % 3;
  const theta = spin * 0.4 + arm * (Math.PI * 2 / 3) + index * 0.72;
  const radius = 1.75 + hash01(star.id + "r") * 0.75;
  return {
    x: Math.cos(theta) * radius,
    y: (hash01(star.id + "y") - 0.5) * 0.62,
    z: Math.sin(theta) * radius * 0.78,
  };
}
function rotate(p, yaw, pitch) {
  const cy = Math.cos(yaw), sy = Math.sin(yaw);
  const x1 = p.x * cy - p.z * sy;
  const z1 = p.x * sy + p.z * cy;
  const cp = Math.cos(pitch), sp = Math.sin(pitch);
  return { x: x1, y: p.y * cp - z1 * sp, z: p.y * sp + z1 * cp };
}
function project(p, cx, cy, scale) {
  const z = p.z + 4.15 / zoom;
  const persp = 2.55 / Math.max(0.35, z);
  return { x: cx + p.x * persp * scale, y: cy + p.y * persp * scale, persp, z: p.z };
}

function resize() {
  const w = window.innerWidth, h = window.innerHeight;
  canvas.width = Math.max(1, Math.floor(w * DPR));
  canvas.height = Math.max(1, Math.floor(h * DPR));
  canvas.style.width = w + "px";
  canvas.style.height = h + "px";
  ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
}
function sector(r0, r1, a0, a1) {
  ctx.beginPath();
  ctx.arc(0, 0, r1, a0, a1);
  ctx.arc(0, 0, r0, a1, a0, true);
  ctx.closePath();
}
function drawArc(cx, cy, R, now) {
  const state = document.body.dataset.state;
  const beat = reduce ? 1 : 0.86 + 0.14 * Math.sin(now / 340);
  const hot = beat + (state === "speaking" ? level * 0.35 : state === "thinking" ? 0.12 : 0);
  ctx.save();
  ctx.translate(cx, cy);
  ctx.beginPath();
  ctx.arc(0, 0, R, 0, Math.PI * 2);
  const metal = ctx.createRadialGradient(-R * 0.25, -R * 0.3, R * 0.1, 0, 0, R);
  metal.addColorStop(0, ink.copper2);
  metal.addColorStop(0.45, ink.copper);
  metal.addColorStop(1, "oklch(0.32 0.06 60)");
  ctx.fillStyle = metal;
  ctx.fill();
  ctx.beginPath();
  ctx.arc(0, 0, R * 0.9, 0, Math.PI * 2);
  ctx.fillStyle = "oklch(0.1 0.02 250)";
  ctx.fill();
  ctx.strokeStyle = ink.copper2;
  ctx.globalAlpha = 0.85;
  ctx.lineWidth = Math.max(2, R * 0.018);
  ctx.beginPath();
  ctx.arc(0, 0, R * 0.96, 0, Math.PI * 2);
  ctx.stroke();
  ctx.beginPath();
  ctx.arc(0, 0, R * 0.9, 0, Math.PI * 2);
  ctx.lineWidth = Math.max(1, R * 0.008);
  ctx.stroke();
  const count = 10;
  const pitch = (Math.PI * 2) / count;
  const span = pitch * 0.58;
  for (let i = 0; i < count; i++) {
    const a = -Math.PI / 2 + i * pitch;
    const glow = reduce ? 1 : 0.78 + 0.22 * (0.5 + 0.5 * Math.sin(now / 460 - i * 0.55));
    sector(R * 0.5, R * 0.8, a - span / 2, a + span / 2);
    ctx.globalAlpha = Math.min(1, 0.72 + glow * 0.28);
    ctx.fillStyle = ink.plasma;
    ctx.fill();
    ctx.globalAlpha = 0.95;
    ctx.strokeStyle = ink.core;
    ctx.lineWidth = 1;
    ctx.stroke();
  }
  ctx.globalAlpha = 1;
  ctx.beginPath();
  ctx.arc(0, 0, R * 0.44, 0, Math.PI * 2);
  ctx.fillStyle = "oklch(0.08 0.02 255)";
  ctx.fill();
  ctx.strokeStyle = ink.copper2;
  ctx.lineWidth = Math.max(1.5, R * 0.012);
  ctx.stroke();
  ctx.beginPath();
  const tr = R * 0.23;
  for (let i = 0; i < 3; i++) {
    const a = -Math.PI / 2 + i * (Math.PI * 2 / 3);
    const x = Math.cos(a) * tr;
    const y = Math.sin(a) * tr;
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }
  ctx.closePath();
  ctx.strokeStyle = ink.core;
  ctx.lineWidth = Math.max(2, R * 0.016);
  ctx.stroke();
  const coreR = R * (0.055 + (state === "speaking" ? level * 0.03 : 0)) * hot;
  const bloom = ctx.createRadialGradient(0, 0, 0, 0, 0, R * 0.34 * hot);
  bloom.addColorStop(0, ink.core);
  bloom.addColorStop(0.25, ink.plasma);
  bloom.addColorStop(1, "rgba(0,0,0,0)");
  ctx.fillStyle = bloom;
  ctx.beginPath();
  ctx.arc(0, 0, R * 0.34 * hot, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillStyle = "#f7fbff";
  ctx.beginPath();
  ctx.arc(0, 0, coreR, 0, Math.PI * 2);
  ctx.fill();
  ctx.globalAlpha = 0.45;
  ctx.strokeStyle = "rgba(255,255,255,0.85)";
  ctx.lineWidth = Math.max(2, R * 0.02);
  ctx.beginPath();
  ctx.arc(0, 0, R * 0.93, -2.5, -0.7);
  ctx.stroke();
  ctx.restore();
  ctx.globalAlpha = 1;
}
function drawGlobe(cx, cy, radius, now) {
  const spin = reduce ? 0.2 : now / 8000;
  ctx.save();
  ctx.translate(cx, cy);
  ctx.rotate(spin);
  ctx.strokeStyle = "rgba(150, 214, 230, 0.42)";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.arc(0, 0, radius, 0, Math.PI * 2);
  ctx.stroke();
  for (let i = 1; i <= 4; i++) {
    const frac = i / 5;
    ctx.beginPath();
    ctx.ellipse(0, 0, radius * frac, radius, 0, 0, Math.PI * 2);
    ctx.stroke();
    ctx.beginPath();
    ctx.ellipse(0, 0, radius, radius * frac, 0, 0, Math.PI * 2);
    ctx.stroke();
  }
  ctx.restore();
  ctx.save();
  ctx.translate(cx, cy);
  ctx.setLineDash([11, 9]);
  ctx.strokeStyle = "rgba(198, 236, 246, 0.7)";
  ctx.lineWidth = 1.25;
  ctx.beginPath();
  ctx.arc(0, 0, radius * 1.08, 0, Math.PI * 2);
  ctx.stroke();
  ctx.lineDashOffset = reduce ? 0 : -now / 80;
  ctx.beginPath();
  ctx.arc(0, 0, radius * 1.18, 0, Math.PI * 2);
  ctx.stroke();
  ctx.setLineDash([]);
  ctx.restore();
  ctx.globalAlpha = 0.28;
  ctx.strokeStyle = "rgba(190, 232, 242, 0.9)";
  ctx.beginPath();
  ctx.moveTo(cx - radius * 1.28, cy);
  ctx.lineTo(cx + radius * 1.28, cy);
  ctx.stroke();
  ctx.globalAlpha = 1;
}
function drawBrackets(rect) {
  const inset = 16;
  const arm = Math.min(36, rect.width * 0.05);
  const x0 = rect.left + inset;
  const y0 = rect.top + inset;
  const x1 = rect.right - inset;
  const y1 = rect.bottom - inset;
  ctx.strokeStyle = "rgba(176, 226, 238, 0.75)";
  ctx.lineWidth = 1.5;
  const corners = [[x0, y0, 1, 1], [x1, y0, -1, 1], [x0, y1, 1, -1], [x1, y1, -1, -1]];
  for (const [x, y, sx, sy] of corners) {
    ctx.beginPath();
    ctx.moveTo(x, y + arm * sy);
    ctx.lineTo(x, y);
    ctx.lineTo(x + arm * sx, y);
    ctx.stroke();
  }
}
function drawReactor(now) {
  const w = canvas.width / DPR, h = canvas.height / DPR;
  const rect = well.getBoundingClientRect();
  ctx.clearRect(0, 0, w, h);
  ctx.fillStyle = ink.paper;
  ctx.fillRect(0, 0, w, h);
  if (rect.width < 40 || rect.height < 40) return;
  const cx = rect.left + rect.width / 2;
  const cy = rect.top + rect.height / 2;
  const minSide = Math.min(rect.width, rect.height);
  const R = minSide * 0.22;
  const globe = minSide * 0.36;
  const scale = minSide * 0.3;
  const yaw = (reduce ? 0.8 : now / 14000) + yawUser;
  const pitch = pitchUser;
  ctx.save();
  ctx.beginPath();
  ctx.rect(rect.left, rect.top, rect.width, rect.height);
  ctx.clip();
  const voidGrad = ctx.createRadialGradient(cx, cy, globe * 0.15, cx, cy, minSide * 0.72);
  voidGrad.addColorStop(0, "oklch(0.14 0.04 255)");
  voidGrad.addColorStop(1, ink.void);
  ctx.fillStyle = voidGrad;
  ctx.fillRect(rect.left, rect.top, rect.width, rect.height);
  for (const cloud of nebulas) {
    const p = project(rotate(cloud, yaw, pitch), cx, cy, scale);
    const rad = Math.max(8, cloud.r * p.persp * scale);
    const g = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, rad);
    g.addColorStop(0, "rgba(" + cloud.rgb + ",0.34)");
    g.addColorStop(0.55, "rgba(" + cloud.rgb + ",0.12)");
    g.addColorStop(1, "rgba(" + cloud.rgb + ",0)");
    ctx.fillStyle = g;
    ctx.beginPath();
    ctx.arc(p.x, p.y, rad, 0, Math.PI * 2);
    ctx.fill();
  }
  const dust = ambient.map((star) => {
    const p = project(rotate(star, yaw, pitch), cx, cy, scale);
    return { p, s: star.s, warm: star.warm };
  }).sort((a, b) => b.p.z - a.p.z);
  for (const star of dust) {
    const alpha = Math.max(0.15, Math.min(0.95, star.p.persp * 0.85));
    ctx.globalAlpha = alpha;
    ctx.fillStyle = star.warm ? "rgb(255, 214, 170)" : "rgb(196, 220, 255)";
    ctx.beginPath();
    ctx.arc(star.p.x, star.p.y, Math.max(0.4, star.s * star.p.persp), 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.globalAlpha = 1;
  const placed = memory.map((star, index) => {
    const p = project(rotate(placeNamed(star, index), yaw, pitch), cx, cy, scale);
    return { star, p };
  });
  ctx.lineWidth = 1;
  for (const link of memoryLinks) {
    const a = placed.find((item) => item.star.id === link.a);
    const b = placed.find((item) => item.star.id === link.b);
    if (!a || !b) continue;
    ctx.globalAlpha = 0.45;
    ctx.strokeStyle = ink.plasma;
    ctx.beginPath();
    ctx.moveTo(a.p.x, a.p.y);
    ctx.lineTo(b.p.x, b.p.y);
    ctx.stroke();
  }
  namedOnScreen = [];
  for (const item of placed) {
    const outside = Math.hypot(item.p.x - cx, item.p.y - cy) > R * 0.92;
    namedOnScreen.push({ star: item.star, x: item.p.x, y: item.p.y, outside });
    if (!outside) continue;
    const glow = ctx.createRadialGradient(item.p.x, item.p.y, 0, item.p.x, item.p.y, 16 * item.p.persp);
    glow.addColorStop(0, "rgba(230, 246, 255, 0.95)");
    glow.addColorStop(1, "rgba(80, 170, 220, 0)");
    ctx.globalAlpha = 1;
    ctx.fillStyle = glow;
    ctx.beginPath();
    ctx.arc(item.p.x, item.p.y, 16 * item.p.persp, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = item.star.id === picked ? ink.accent : "#f4fbff";
    ctx.beginPath();
    ctx.arc(item.p.x, item.p.y, Math.max(1.6, 2.4 * item.p.persp), 0, Math.PI * 2);
    ctx.fill();
  }
  drawGlobe(cx, cy, globe, now);
  drawArc(cx, cy, R, now);
  drawBrackets(rect);
  ctx.font = "500 12px " + ink.mono;
  ctx.textAlign = "center";
  ctx.textBaseline = "bottom";
  for (const item of namedOnScreen) {
    if (!item.outside) continue;
    if (memory.length > 8 && item.star.id !== picked) continue;
    ctx.globalAlpha = item.star.id === picked ? 1 : 0.8;
    ctx.fillStyle = ink.core;
    ctx.fillText(item.star.label, item.x, item.y - 10);
  }
  ctx.restore();
  ctx.globalAlpha = 1;
}
function starAt(x, y) {
  let best = null;
  let bestD = 28;
  for (const item of namedOnScreen) {
    if (!item.outside) continue;
    const d = Math.hypot(item.x - x, item.y - y);
    if (d < bestD) { best = item; bestD = d; }
  }
  return best;
}
let level = 0;
const timeBuf = new Uint8Array(256);
function sampleLevel() {
  if (!analyser || document.body.dataset.state !== "speaking") { level *= 0.9; return; }
  analyser.getByteTimeDomainData(timeBuf);
  let s = 0;
  for (let i = 0; i < timeBuf.length; i++) { const v = (timeBuf[i] - 128) / 128; s += v * v; }
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
  for (const btn of [submitBtn, voiceBtn, micBtn, allowBtn, denyBtn]) {
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
function showPermit(id, command) {
  permitId = id || "";
  permitCmd.textContent = command || "";
  permitEl.hidden = !permitId;
}
async function refreshBrain() {
  try {
    const data = await (await fetch("/api/status")).json();
    brainEl.textContent = data.up ? (data.model || "sem modelo") : "ausente";
    if (data.load && data.load.length) {
      loadEl.textContent = String(data.load[0]);
      document.body.dataset.load = String(data.load[0]);
    }
    if (typeof data.notes === "number") {
      const notesEl = document.getElementById("notes");
      if (notesEl) notesEl.textContent = String(data.notes);
    }
    for (const brain of data.brains || []) {
      const el = document.getElementById("brain-" + brain.id);
      if (el) el.textContent = brain.up ? "pronto" : "ausente";
    }
    refreshSky();
  } catch (err) {
    brainEl.textContent = "ausente";
  }
}
async function refreshSky() {
  try {
    const data = await (await fetch("/api/sky")).json();
    memory = data.stars || [];
    memoryLinks = data.links || [];
    const el = document.getElementById("sky");
    if (el) el.textContent = String(memory.length);
  } catch (err) { /* o céu fica como está */ }
}
function pointStar(ev, choose) {
  const hit = starAt(ev.clientX, ev.clientY);
  if (!hit) {
    if (choose) {
      picked = "";
      skyRead.textContent = "Arraste o céu.";
    }
    return;
  }
  if (choose) picked = hit.star.id;
  skyRead.textContent = hit.star.text;
}
well.addEventListener("pointerdown", (ev) => {
  drag = { x: ev.clientX, y: ev.clientY, yaw: yawUser, pitch: pitchUser };
  dragMoved = 0;
  well.setPointerCapture(ev.pointerId);
});
well.addEventListener("pointermove", (ev) => {
  if (!drag) { pointStar(ev, false); return; }
  const dx = ev.clientX - drag.x;
  const dy = ev.clientY - drag.y;
  dragMoved = Math.max(dragMoved, Math.hypot(dx, dy));
  yawUser = drag.yaw + dx * 0.005;
  pitchUser = Math.max(-0.7, Math.min(0.7, drag.pitch + dy * 0.004));
});
well.addEventListener("pointerup", (ev) => {
  if (drag && dragMoved < 6) pointStar(ev, true);
  drag = null;
});
well.addEventListener("pointerleave", () => {
  if (!drag && !picked) skyRead.textContent = "Arraste o céu.";
});
well.addEventListener("wheel", (ev) => {
  ev.preventDefault();
  zoom = Math.max(0.7, Math.min(1.8, zoom * (ev.deltaY > 0 ? 0.94 : 1.06)));
}, { passive: false });
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
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body || {}),
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
  if (data.status === "permit") {
    sessEl.textContent = "ordem pendente";
    showPermit(data.permit_id, data.command);
    if (data.reply) addLine("agent", data.reply);
    if (data.audio_b64) await playWav(data.audio_b64);
    else setState("idle");
    return;
  }
  if (data.status === "replied") sessEl.textContent = "acordado";
  if (data.reply) addLine("agent", data.reply);
  if (data.output) addLine("meta", data.output);
  if (data.audio_b64) await playWav(data.audio_b64);
  else setState("idle");
  if (sourceBtn && data.reply) mark(sourceBtn, "success");
}
async function decide(allow) {
  if (!permitId) return;
  const id = permitId;
  showPermit("", "");
  setState("thinking");
  try { await showTurn(await post("/api/permit", { id, allow }), allow ? allowBtn : denyBtn); }
  catch (err) { setState("idle"); addLine("meta", "Não consegui cumprir a ordem."); }
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
allowBtn.addEventListener("click", () => decide(true));
denyBtn.addEventListener("click", () => decide(false));
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
  try { await showTurn(await post("/api/turn", { pcm_b64: btoa(binary), sample_rate: rate }), micBtn); }
  catch (err) { setState("idle"); addLine("meta", "Não consegui ouvir agora."); mark(micBtn, "error"); }
}
micBtn.addEventListener("pointerdown", startMic);
micBtn.addEventListener("pointerup", stopMic);
micBtn.addEventListener("pointerleave", stopMic);
addEventListener("resize", resize);
resize();
tickClock();
setInterval(tickClock, 1000);
refreshBrain();
setInterval(refreshBrain, 5000);
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
