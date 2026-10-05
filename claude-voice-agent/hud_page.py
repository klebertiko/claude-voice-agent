"""Painel do Orion: a carta da constelação, no azul da prancha.

Sem vídeo e sem reator. Uma ordem no computador aparece inteira e espera permissão.
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
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;1,500;1,600&family=Source+Sans+3:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet" />
<style>
  /* Carta XXIX. Escala 16 × 1.25. Duas famílias: Cormorant na prancha, Source Sans no miolo.
   * As margens são rótulos de carta (16px), não faixas de painel.
   * Um acento só: o marfim da permissão. O chão é o azul medido da prancha.
   */
  :root {
    color-scheme: dark;
    --color-paper: #f3f0e6;
    --color-plate: #0a427d;
    --color-ink: #f7f5ef;
    --color-ink-2: #d5dce8;
    --color-accent: #f3e6c4;
    --color-rule: rgba(247, 245, 239, 0.4);
    --color-focus: #f7f5ef;
    --color-ok: #d5eadc;
    --color-bad: #f0c8be;
    --font-display: "Cormorant Garamond", Palatino, "Palatino Linotype", Georgia, serif;
    --font-body: "Source Sans 3", "Segoe UI", sans-serif;
    --text-support: 0.875rem;
    --text-body: 1rem;
    --text-lead: 1.25rem;
    --text-display: 3.052rem;
    --space-1: 0.5rem;
    --space-2: 1rem;
    --space-3: 1.5rem;
    --space-4: 2rem;
    --space-5: 3rem;
    --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
    --dur-short: 180ms;
  }
  * { box-sizing: border-box; }
  html, body { margin: 0; min-height: 100%; background: var(--color-paper); color: var(--color-ink); }
  body {
    font-family: var(--font-body);
    font-size: var(--text-body);
    font-weight: 400;
    line-height: 1.5;
    font-style: normal;
  }
  h1, h2, p { margin: 0; }
  #field { position: fixed; inset: 0; width: 100%; height: 100%; z-index: 0; display: block; }
  .room {
    position: relative; z-index: 1;
    margin: var(--space-2);
    min-height: calc(100vh - 2rem);
    display: grid;
    grid-template-columns: 1fr;
    grid-template-rows: auto minmax(70vh, auto) auto auto auto auto;
    background: transparent;
    border: 1px solid var(--color-ink);
    box-shadow: 0 0 0 4px var(--color-paper), 0 0 0 5px var(--color-ink);
    user-select: none;
  }
  #log, #text, #permit-cmd { user-select: text; }
  .strip {
    display: flex; align-items: baseline; justify-content: space-between;
    gap: var(--space-2); padding: var(--space-3) var(--space-2) var(--space-1);
  }
  #status {
    font-family: var(--font-body); font-size: var(--text-support); font-weight: 600;
    letter-spacing: 0.12em; text-transform: uppercase; color: var(--color-ink-2);
  }
  body[data-state="listening"] #status,
  body[data-state="speaking"] #status,
  body[data-state="thinking"] #status { color: var(--color-accent); }
  body[data-state="ignored"] #status { color: var(--color-bad); }
  #clock {
    font-family: var(--font-display); font-weight: 600; font-size: var(--text-lead);
    line-height: 1.2; font-variant-numeric: tabular-nums; letter-spacing: 0.04em;
  }
  .well { position: relative; min-height: 70vh; cursor: grab; touch-action: none; }
  .well:active { cursor: grabbing; }
  .hero { position: absolute; left: var(--space-2); bottom: var(--space-3); max-width: 16rem; pointer-events: none; }
  .plate-num {
    margin: 0 0 var(--space-1);
    font-family: var(--font-display); font-weight: 600; font-size: var(--text-support);
    letter-spacing: 0.16em;
  }
  .hero h1 {
    margin: 0 0 var(--space-4);
    font-family: var(--font-display); font-weight: 600; font-style: normal;
    font-size: clamp(2.441rem, 8vw, var(--text-display));
    line-height: 1; letter-spacing: 0.08em; text-transform: uppercase;
  }
  .epithet {
    font-family: var(--font-display); font-style: italic; font-weight: 500;
    font-size: var(--text-lead); line-height: 1.3;
  }
  #sky-read {
    position: absolute; left: var(--space-2); right: var(--space-2); bottom: 11rem;
    max-width: 22rem; pointer-events: none;
    font-family: var(--font-display); font-style: italic; font-weight: 500;
    font-size: var(--text-body); line-height: 1.5;
  }
  .telemetry, .talk {
    min-width: 0; min-height: 0;
    padding: var(--space-4) var(--space-2);
  }
  h2 {
    margin: 0 0 var(--space-2);
    font-family: var(--font-body); font-size: var(--text-body); font-weight: 600;
    font-style: normal; line-height: 1.25; letter-spacing: 0.12em;
    text-transform: uppercase; color: var(--color-ink-2);
  }
  .systems { margin: 0; display: flex; flex-direction: column; gap: var(--space-1); }
  .systems div {
    display: flex; flex-direction: row; justify-content: space-between; align-items: baseline;
    gap: var(--space-2); min-width: 0;
  }
  .systems dt {
    font-family: var(--font-body); font-size: var(--text-support); font-weight: 600;
    letter-spacing: 0.08em; text-transform: uppercase; color: var(--color-ink-2);
  }
  .systems dd {
    margin: 0; font-family: var(--font-display); font-style: italic; font-weight: 500;
    font-size: var(--text-body); line-height: 1.3; text-align: right; color: var(--color-ink);
    overflow-wrap: anywhere;
  }
  .systems dd.is-down { color: var(--color-ink-2); }
  .talk { display: flex; flex-direction: column; }
  #log {
    flex: 1; min-height: 0; max-height: 24rem; overflow: auto;
    display: flex; flex-direction: column; gap: var(--space-2); max-width: 65ch;
  }
  #log p { margin: 0; line-height: 1.5; overflow-wrap: anywhere; min-width: 0; font-size: var(--text-body); }
  #log .empty, #log .meta { color: var(--color-ink-2); }
  #log p[data-speaker]::before {
    content: attr(data-speaker);
    display: block; margin: 0 0 var(--space-1);
    font-family: var(--font-body); font-size: var(--text-support); font-weight: 600;
    letter-spacing: 0.12em; text-transform: uppercase; color: var(--color-ink-2);
  }
  #permit {
    display: flex; align-items: center; flex-wrap: wrap; gap: var(--space-2);
    padding: var(--space-2);
    border-top: 1px solid var(--color-accent);
  }
  #permit[hidden] { display: none; }
  #permit p {
    font-family: var(--font-body); font-size: var(--text-body); font-weight: 600;
    letter-spacing: 0.12em; text-transform: uppercase; color: var(--color-accent);
  }
  #permit-cmd {
    flex: 1 1 12rem; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
    font-family: var(--font-body); font-size: var(--text-body); color: var(--color-ink);
  }
  .floor {
    display: flex; align-items: center; flex-wrap: wrap; gap: var(--space-2);
    padding: var(--space-1) var(--space-2) var(--space-3);
  }
  #text {
    flex: 1 1 12rem; min-width: 0; min-height: 44px;
    background: transparent; color: var(--color-ink);
    border: 0; border-bottom: 1px solid var(--color-rule); border-radius: 0;
    font-family: var(--font-body); font-size: var(--text-body); line-height: 1.5;
    padding: 0.75rem 0; outline: none;
  }
  #text::placeholder { color: var(--color-ink-2); }
  #text:hover { border-bottom-color: var(--color-ink-2); }
  #text:focus-visible, .act:focus-visible { outline: 2px solid var(--color-focus); outline-offset: 2px; }
  #text:disabled, .act:disabled { color: var(--color-ink-2); cursor: not-allowed; }
  #text[data-state="loading"] { border-bottom-color: var(--color-accent); }
  #text[data-state="error"] { border-bottom-color: var(--color-bad); }
  #text[data-state="success"] { border-bottom-color: var(--color-ok); }
  .act {
    font-family: var(--font-body); font-size: var(--text-body); font-weight: 400;
    letter-spacing: 0.08em; text-transform: uppercase; text-decoration: none; white-space: nowrap;
    cursor: pointer; min-height: 44px; min-width: 44px; padding: 0.75rem var(--space-2);
    border: 0; border-radius: 0; background: transparent; color: var(--color-ink);
    transition: color var(--dur-short) var(--ease-out);
  }
  .act:hover { color: var(--color-accent); }
  .act:active { color: var(--color-ink); }
  .act[data-state="loading"] { color: var(--color-accent); }
  .act[data-state="error"] { color: var(--color-bad); }
  .act[data-state="success"] { color: var(--color-ok); }
  #send, #allow { color: var(--color-accent); font-weight: 600; }
  #send:hover, #allow:hover { color: var(--color-ink); }
  #mic[data-hot="1"] { color: var(--color-bad); }
  @media (min-width: 900px) {
    .room {
      margin: var(--space-3);
      min-height: calc(100vh - 3rem);
      grid-template-columns: minmax(16rem, 20rem) minmax(0, 1fr) minmax(18rem, 24rem);
      grid-template-rows: auto minmax(0, 1fr) auto auto;
    }
    .strip, #permit, .floor { grid-column: 1 / -1; }
    .strip { padding: var(--space-3) var(--space-4) var(--space-1); }
    .well { grid-column: 2; grid-row: 2; min-height: 0; }
    .telemetry { grid-column: 1; grid-row: 2; overflow: auto; padding: var(--space-5) var(--space-4); }
    .talk { grid-column: 3; grid-row: 2; overflow: hidden; padding: var(--space-5) var(--space-4) var(--space-4); }
    #log { max-height: none; }
    .hero { left: var(--space-4); bottom: var(--space-4); }
    #sky-read { left: var(--space-4); }
    #permit, .floor { padding-left: var(--space-4); padding-right: var(--space-4); }
    .floor { padding-bottom: var(--space-4); }
  }
  @media (prefers-reduced-motion: reduce) { .act { transition: none; } }
</style>
</head>
<body data-state="idle" data-name="__NAME__" data-load="0">
<canvas id="field" aria-label="constelação"></canvas>
<div class="room">
  <header class="strip">
    <p id="status">pronto</p>
    <p id="clock">00:00:00</p>
  </header>
  <div class="well">
    <p id="sky-read">Arraste o céu.</p>
    <div class="hero">
      <p class="plate-num">XXIX</p>
      <h1>__NAME__</h1>
      <p class="epithet">(the Glorious One)</p>
    </div>
  </div>
  <aside class="telemetry">
    <h2>Observações</h2>
    <dl class="systems">
      <div><dt>codex</dt><dd class="is-down" id="brain-codex">ausente</dd></div>
      <div><dt>cursor</dt><dd class="is-down" id="brain-cursor">ausente</dd></div>
      <div><dt>claude</dt><dd class="is-down" id="brain-claude">ausente</dd></div>
      <div><dt>cérebro</dt><dd class="is-down" id="brain">ausente</dd></div>
      <div><dt>céu</dt><dd id="sky">0</dd></div>
      <div><dt>lembretes</dt><dd id="notes">0</dd></div>
      <div><dt>voz</dt><dd id="voice-name">george</dd></div>
      <div><dt>ritmo</dt><dd>1.08</dd></div>
      <div><dt>carga</dt><dd id="load">—</dd></div>
      <div><dt>fuso</dt><dd>Brasília</dd></div>
      <div><dt>data</dt><dd id="date">—</dd></div>
      <div><dt>sessão</dt><dd id="sess">à espera do nome</dd></div>
    </dl>
  </aside>
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
  paper: tok("--color-paper"), plate: tok("--color-plate"),
  ink: tok("--color-ink"), ink2: tok("--color-ink-2"), accent: tok("--color-accent"),
  display: tok("--font-display"), body: tok("--font-body"),
};
const room = document.querySelector(".room");
const well = document.querySelector(".well");
const skyRead = document.getElementById("sky-read");
let permitId = "";
let memory = [];
let memoryLinks = [];
let namedOnScreen = [];
let picked = "";
let yawUser = 0;
let pitchUser = 0;
let zoom = 1;
let drag = null;
let dragMoved = 0;
const ambient = [];
(function buildAmbient() {
  let seed = 2166136261;
  const rnd = () => {
    seed = Math.imul(seed ^ 0x9e3779b9, 16777619) >>> 0;
    return seed / 4294967295;
  };
  for (let i = 0; i < 150; i++) {
    ambient.push({
      x: (rnd() - 0.5) * 4.6,
      y: (rnd() - 0.5) * 5.8,
      z: (rnd() - 0.5) * 0.05,
      s: rnd() < 0.05 ? 1.8 : 0.4 + rnd() * 0.5,
      a: 0.28 + rnd() * 0.55,
    });
  }
})();
const MYTH = [
  { name: "Meissa", greek: "λ", x: 54, y: 28, dx: 0, dy: -28, align: "center" },
  { name: "Betelgeuse", greek: "α", x: 38, y: 54, dx: -46, dy: 2, align: "right" },
  { name: "Bellatrix", greek: "γ", x: 66, y: 52, dx: 28, dy: -30, align: "left" },
  { name: "Mintaka", greek: "δ", x: 38, y: 82, dx: -52, dy: 12, align: "right" },
  { name: "Alnilam", greek: "ε", x: 50, y: 86, dx: 0, dy: -32, align: "center" },
  { name: "Alnitak", greek: "ζ", x: 64, y: 90, dx: 64, dy: 4, align: "left" },
  { name: "Rigel", greek: "β", x: 30, y: 122, dx: -28, dy: 20, align: "right" },
  { name: "Saiph", greek: "κ", x: 76, y: 104, dx: 48, dy: 16, align: "left" },
  { name: "", greek: "", x: 51, y: 100, dx: 0, dy: 0, align: "center" },
];
const MYTH_LINKS = [[0, 1], [0, 2], [1, 2], [1, 3], [2, 5], [3, 4], [4, 5], [3, 6], [5, 7], [6, 7], [4, 8]];
function hash01(text) {
  let h = 2166136261;
  for (let i = 0; i < text.length; i++) {
    h ^= text.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return (h >>> 0) / 4294967295;
}
function placeNamed(star, index) {
  const slots = [
    { x: -1.78, y: 1.35 },
    { x: 1.95, y: 1.25 },
    { x: -1.78, y: -1.35 },
    { x: 1.95, y: -1.05 },
    { x: -1.7, y: 0.15 },
    { x: 1.85, y: -0.15 },
  ];
  const slot = slots[index % slots.length];
  return {
    x: slot.x + (hash01(star.id + "x") - 0.5) * 0.18,
    y: slot.y + (hash01(star.id + "y") - 0.5) * 0.18,
    z: (hash01(star.id + "z") - 0.5) * 0.12,
  };
}
function figPoint(x, y) {
  return { x: (x - 52) / 32, y: (70 - y) / 32, z: 0 };
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
  return { x: cx + p.x * persp * scale, y: cy - p.y * persp * scale, persp, z: p.z };
}
function resize() {
  const w = window.innerWidth, h = window.innerHeight;
  canvas.width = Math.max(1, Math.floor(w * DPR));
  canvas.height = Math.max(1, Math.floor(h * DPR));
  canvas.style.width = w + "px";
  canvas.style.height = h + "px";
  ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
}
function curve(pts, map, width, alpha) {
  if (pts.length < 2) return;
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.lineWidth = width;
  ctx.beginPath();
  const first = map(pts[0][0], pts[0][1]);
  ctx.moveTo(first.x, first.y);
  if (pts.length === 2) {
    const last = map(pts[1][0], pts[1][1]);
    ctx.lineTo(last.x, last.y);
  } else {
    for (let i = 1; i < pts.length - 1; i++) {
      const c = map(pts[i][0], pts[i][1]);
      const n = map(pts[i + 1][0], pts[i + 1][1]);
      ctx.quadraticCurveTo(c.x, c.y, (c.x + n.x) / 2, (c.y + n.y) / 2);
    }
    const last = map(pts[pts.length - 1][0], pts[pts.length - 1][1]);
    ctx.lineTo(last.x, last.y);
  }
  ctx.stroke();
  ctx.restore();
}
function poly(pts, map, width, alpha) {
  if (pts.length < 2) return;
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.lineWidth = width;
  ctx.beginPath();
  pts.forEach((pt, i) => {
    const p = map(pt[0], pt[1]);
    if (i === 0) ctx.moveTo(p.x, p.y);
    else ctx.lineTo(p.x, p.y);
  });
  ctx.stroke();
  ctx.restore();
}
function q(a, c, b, map, width, alpha) {
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.lineWidth = width;
  ctx.beginPath();
  const start = map(a[0], a[1]);
  const ctrl = map(c[0], c[1]);
  const end = map(b[0], b[1]);
  ctx.moveTo(start.x, start.y);
  ctx.quadraticCurveTo(ctrl.x, ctrl.y, end.x, end.y);
  ctx.stroke();
  ctx.restore();
}
function ellipse(cx, cy, rx, ry, map, width, alpha) {
  const pts = [];
  for (let i = 0; i <= 28; i++) {
    const a = (i / 28) * Math.PI * 2;
    pts.push([cx + Math.cos(a) * rx, cy + Math.sin(a) * ry]);
  }
  poly(pts, map, width, alpha);
}
function engrave(map, minSide) {
  const line = Math.max(1.25, minSide * 0.0024);
  const hair = Math.max(0.9, minSide * 0.00125);
  ctx.lineJoin = "round";
  ctx.lineCap = "round";
  ctx.strokeStyle = ink.ink;
  ctx.fillStyle = ink.ink;
  poly([[22, 8], [34, 2], [48, 34], [40, 42], [26, 16], [22, 8]], map, line, 1);
  poly([[28, 16], [36, 22]], map, hair, 0.7);
  poly([[32, 24], [40, 30]], map, hair, 0.7);
  poly([[36, 52], [30, 40], [36, 30]], map, line, 1);
  poly([[44, 54], [38, 42], [42, 34]], map, line, 0.9);
  ellipse(54, 36, 10, 12, map, line, 1);
  q([44, 30], [54, 14], [66, 28], map, hair, 0.85);
  poly([[49, 34], [58, 33]], map, hair, 0.95);
  poly([[54, 35], [56, 42]], map, hair, 0.95);
  poly([[49, 44], [58, 45]], map, hair, 0.95);
  poly([[44, 36], [41, 40], [45, 44]], map, hair, 0.75);
  poly([[48, 48], [46, 56]], map, line, 0.9);
  poly([[60, 47], [62, 55]], map, line, 0.9);
  poly([[40, 56], [34, 80]], map, line, 1);
  poly([[66, 52], [64, 86]], map, line, 1);
  q([42, 60], [54, 68], [64, 58], map, hair, 0.6);
  poly([[66, 52], [78, 44], [84, 42]], map, line, 1);
  ellipse(92, 40, 11, 12, map, line, 1);
  for (let i = 0; i < 7; i++) {
    const a = -2.6 + i * 0.55;
    poly([
      [92 + Math.cos(a) * 12, 40 + Math.sin(a) * 13],
      [92 + Math.cos(a) * 18, 40 + Math.sin(a) * 19],
    ], map, hair, 0.6);
  }
  poly([[88, 38], [90, 40]], map, hair, 0.9);
  poly([[96, 38], [98, 40]], map, hair, 0.9);
  q([90, 44], [94, 48], [98, 44], map, hair, 0.8);
  poly([[82, 50], [76, 66], [84, 74]], map, line, 0.75);
  poly([[32, 80], [68, 90]], map, line, 1);
  poly([[34, 83], [66, 93]], map, hair, 0.55);
  poly([[50, 86], [47, 106]], map, line, 0.9);
  poly([[55, 88], [52, 108]], map, line, 0.9);
  poly([[46, 90], [58, 96]], map, line, 0.85);
  poly([[34, 82], [26, 118]], map, line, 1);
  poly([[46, 84], [36, 120]], map, line, 1);
  poly([[24, 118], [42, 126]], map, line, 1);
  poly([[64, 88], [80, 102], [72, 116]], map, line, 1);
  poly([[58, 90], [72, 104], [66, 114]], map, line, 0.9);
  poly([[46, 130], [64, 128], [70, 134], [62, 140], [44, 138], [40, 132], [46, 130]], map, line, 1);
  poly([[48, 130], [46, 120], [52, 126]], map, line, 0.9);
  poly([[54, 130], [56, 120], [52, 126]], map, line, 0.9);
  poly([[42, 136], [36, 142]], map, line, 0.85);
  poly([[58, 140], [60, 146]], map, line, 0.85);
  poly([[68, 134], [74, 130]], map, hair, 0.7);
  ctx.globalAlpha = 1;
}
function drawPlate(now) {
  const w = canvas.width / DPR, h = canvas.height / DPR;
  const plate = room.getBoundingClientRect();
  const rect = well.getBoundingClientRect();
  ctx.clearRect(0, 0, w, h);
  ctx.fillStyle = ink.paper;
  ctx.fillRect(0, 0, w, h);
  ctx.fillStyle = ink.plate;
  ctx.fillRect(plate.left, plate.top, plate.width, plate.height);
  if (rect.width < 40 || rect.height < 40) return;
  const cx = rect.left + rect.width / 2;
  const cy = rect.top + rect.height * 0.4;
  const minSide = Math.min(rect.width, rect.height);
  const scale = minSide * 0.36 * zoom;
  const yaw = Math.max(-0.4, Math.min(0.4, yawUser));
  const pitch = Math.max(-0.28, Math.min(0.28, pitchUser));
  const map = (x, y) => project(rotate(figPoint(x, y), yaw, pitch), cx, cy, scale);
  ctx.save();
  ctx.beginPath();
  ctx.rect(rect.left, rect.top, rect.width, rect.height);
  ctx.clip();
  for (const star of ambient) {
    const p = project(rotate(star, yaw, pitch), cx, cy, scale);
    ctx.globalAlpha = star.a;
    ctx.fillStyle = ink.ink;
    ctx.beginPath();
    ctx.arc(p.x, p.y, Math.max(0.4, star.s * 0.7), 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.globalAlpha = 0.55;
  ctx.strokeStyle = ink.ink;
  ctx.lineWidth = 1;
  ctx.setLineDash([2, 6]);
  curve([[6, 16], [28, 8], [50, 4], [72, 8], [94, 18]], map, 1, 0.55);
  ctx.setLineDash([]);
  ctx.globalAlpha = 0.8;
  ctx.fillStyle = ink.ink;
  ctx.font = "600 14px " + ink.display;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  const ecl = map(50, 4);
  ctx.fillText("ECLIPTIC", ecl.x, ecl.y - 14);
  engrave(map, minSide);
  const placedMyth = MYTH.map((star) => ({ star, p: map(star.x, star.y) }));
  ctx.setLineDash([1.5, 5]);
  ctx.lineWidth = 1;
  ctx.strokeStyle = ink.ink;
  ctx.globalAlpha = 0.75;
  for (const link of MYTH_LINKS) {
    const a = placedMyth[link[0]].p;
    const b = placedMyth[link[1]].p;
    ctx.beginPath();
    ctx.moveTo(a.x, a.y);
    ctx.lineTo(b.x, b.y);
    ctx.stroke();
  }
  ctx.setLineDash([]);
  const pulse = reduce ? 1 : 1 + (document.body.dataset.state === "speaking" ? level * 0.35 : 0);
  for (const item of placedMyth) {
    const bright = item.star.name === "Betelgeuse" || item.star.name === "Rigel";
    const radius = (bright ? 3.2 : 2.1) * pulse;
    ctx.globalAlpha = 0.95;
    ctx.fillStyle = ink.ink;
    ctx.beginPath();
    ctx.arc(item.p.x, item.p.y, radius, 0, Math.PI * 2);
    ctx.fill();
    if (bright) {
      ctx.globalAlpha = 0.7;
      ctx.lineWidth = 1;
      ctx.strokeStyle = ink.ink;
      ctx.beginPath();
      ctx.arc(item.p.x, item.p.y, radius + 3.5, 0, Math.PI * 2);
      ctx.stroke();
    }
  }
  ctx.font = "italic 600 14px " + ink.display;
  ctx.fillStyle = ink.ink;
  ctx.textBaseline = "middle";
  for (const item of placedMyth) {
    if (!item.star.name) continue;
    ctx.globalAlpha = 0.92;
    ctx.textAlign = item.star.align;
    ctx.fillText(item.star.name, item.p.x + item.star.dx, item.p.y + item.star.dy);
    if (item.star.greek) {
      ctx.globalAlpha = 0.75;
      ctx.textAlign = "center";
      const gx = item.star.align === "left" ? -12 : 12;
      ctx.fillText(item.star.greek, item.p.x + gx, item.p.y);
    }
  }
  ctx.font = "600 14px " + ink.display;
  ctx.textBaseline = "middle";
  ctx.globalAlpha = 0.62;
  ctx.textAlign = "left";
  ctx.fillText("GEMINI", rect.left + 16, rect.top + 56);
  ctx.fillText("CANIS MAJOR", rect.left + 16, rect.bottom - 196);
  ctx.textAlign = "right";
  ctx.fillText("TAURUS", rect.right - 16, rect.top + 56);
  const lepus = map(74, 136);
  ctx.textAlign = "left";
  ctx.fillText("LEPUS", lepus.x, lepus.y);
  const sirius = map(16, 108);
  ctx.globalAlpha = 0.95;
  ctx.beginPath();
  ctx.arc(sirius.x, sirius.y, 2.6, 0, Math.PI * 2);
  ctx.fill();
  ctx.globalAlpha = 0.8;
  ctx.fillText("Sirius", sirius.x + 10, sirius.y);
  const placed = memory.map((star, index) => {
    const p = project(rotate(placeNamed(star, index), yaw, pitch), cx, cy, scale);
    return { star, p };
  });
  ctx.setLineDash([1.5, 5]);
  ctx.lineWidth = 1;
  for (const link of memoryLinks) {
    const a = placed.find((item) => item.star.id === link.a);
    const b = placed.find((item) => item.star.id === link.b);
    if (!a || !b) continue;
    ctx.globalAlpha = 0.8;
    ctx.strokeStyle = ink.accent;
    ctx.beginPath();
    ctx.moveTo(a.p.x, a.p.y);
    ctx.lineTo(b.p.x, b.p.y);
    ctx.stroke();
  }
  ctx.setLineDash([]);
  namedOnScreen = [];
  for (const item of placed) {
    const inside = item.p.x >= rect.left && item.p.x <= rect.right && item.p.y >= rect.top && item.p.y <= rect.bottom;
    namedOnScreen.push({ star: item.star, x: item.p.x, y: item.p.y, outside: inside });
    if (!inside) continue;
    const chosen = item.star.id === picked;
    ctx.globalAlpha = 1;
    ctx.strokeStyle = chosen ? ink.accent : ink.ink;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.arc(item.p.x, item.p.y, 7, 0, Math.PI * 2);
    ctx.stroke();
    ctx.fillStyle = chosen ? ink.accent : ink.ink;
    ctx.beginPath();
    ctx.arc(item.p.x, item.p.y, 2.4, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.font = "italic 600 14px " + ink.display;
  ctx.textAlign = "center";
  ctx.textBaseline = "bottom";
  for (const item of namedOnScreen) {
    if (!item.outside) continue;
    if (memory.length > 8 && item.star.id !== picked) continue;
    ctx.globalAlpha = 1;
    ctx.fillStyle = item.star.id === picked ? ink.accent : ink.ink;
    item.labelW = ctx.measureText(item.star.label).width;
    ctx.fillText(item.star.label, item.x, item.y - 12);
  }
  ctx.restore();
  ctx.globalAlpha = 1;
  ctx.setLineDash([]);
}
function starAt(x, y) {
  let best = null;
  let bestD = 36;
  for (const item of namedOnScreen) {
    if (!item.outside) continue;
    const dot = Math.hypot(item.x - x, item.y - y);
    if (dot < bestD) { best = item; bestD = dot; }
    const half = (item.labelW || 0) / 2 + 8;
    if (half > 8 && Math.abs(x - item.x) <= half && y <= item.y - 4 && y >= item.y - 28) {
      best = item;
      bestD = 0;
    }
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
  drawPlate(now || 0);
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
    brainEl.classList.toggle("is-down", !data.up);
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
      if (!el) continue;
      el.textContent = brain.up ? "pronto" : "ausente";
      el.classList.toggle("is-down", !brain.up);
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
  yawUser = Math.max(-0.4, Math.min(0.4, drag.yaw + dx * 0.004));
  pitchUser = Math.max(-0.28, Math.min(0.28, drag.pitch + dy * 0.003));
  if (reduce) drawPlate(0);
});
well.addEventListener("pointerup", (ev) => {
  if (drag && dragMoved < 12) pointStar({ clientX: drag.x, clientY: drag.y }, true);
  drag = null;
  if (reduce) drawPlate(0);
});
well.addEventListener("pointerleave", () => {
  if (!drag && !picked) skyRead.textContent = "Arraste o céu.";
});
well.addEventListener("wheel", (ev) => {
  ev.preventDefault();
  zoom = Math.max(0.82, Math.min(1.35, zoom * (ev.deltaY > 0 ? 0.94 : 1.06)));
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
addEventListener("resize", () => { resize(); if (reduce) drawPlate(0); });
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
