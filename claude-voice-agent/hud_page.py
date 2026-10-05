"""Painel do Orion: asterismo no centro, céu de lembretes ao redor.

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
<link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,500;1,6..72,400&family=Source+Sans+3:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet" />
<style>
  /* Painel. Escala 16 × 1.25. Source Sans no miolo, Newsreader só no nome.
   * Um acento. Grelha de 8. A carta é o asterismo, com posições reais.
   */
  :root {
    color-scheme: dark;
    --color-bg: #070d16;
    --color-ink: #e8eef6;
    --color-ink-2: #a9b9cb;
    --color-line: rgba(232, 238, 246, 0.14);
    --color-accent: #d4c4a8;
    --color-focus: #e8eef6;
    --color-ok: #b7d4c4;
    --color-bad: #e7b2a8;
    --font-display: "Newsreader", Georgia, serif;
    --font-body: "Source Sans 3", "Segoe UI", sans-serif;
    --text-support: 0.875rem;
    --text-body: 1rem;
    --text-title: 2rem;
  }
  * { box-sizing: border-box; }
  html, body { margin: 0; min-height: 100%; background: var(--color-bg); color: var(--color-ink); }
  body {
    font-family: var(--font-body);
    font-size: var(--text-body);
    font-weight: 400;
    line-height: 1.5;
  }
  h1, h2, p { margin: 0; }
  #field { position: fixed; inset: 0; width: 100%; height: 100%; z-index: 0; display: block; }
  .room {
    position: relative; z-index: 1;
    min-height: 100vh;
    display: grid;
    grid-template-columns: 1fr;
    grid-template-rows: auto minmax(28rem, auto) auto auto auto auto;
    background: transparent;
    user-select: none;
  }
  #log, #text, #permit-cmd { user-select: text; }
  .strip {
    display: flex; align-items: center; justify-content: space-between;
    gap: 16px; padding: 16px;
    border-bottom: 1px solid var(--color-line);
  }
  .brand { display: flex; align-items: baseline; gap: 12px; min-width: 0; }
  .plate-num {
    font-size: var(--text-support); font-weight: 600; letter-spacing: 0.14em; color: var(--color-ink-2);
  }
  .strip h1 {
    font-family: var(--font-display); font-weight: 500; font-size: clamp(1.5rem, 4vw, var(--text-title));
    line-height: 1; letter-spacing: -0.02em; text-transform: uppercase;
  }
  .epithet {
    font-family: var(--font-display); font-style: italic; font-weight: 400;
    font-size: var(--text-body); line-height: 1.2; color: var(--color-ink-2);
  }
  .meta { display: flex; align-items: baseline; gap: 16px; }
  #status {
    font-size: var(--text-support); font-weight: 600; letter-spacing: 0.12em;
    text-transform: uppercase; color: var(--color-ink-2);
  }
  body[data-state="listening"] #status,
  body[data-state="speaking"] #status,
  body[data-state="thinking"] #status { color: var(--color-accent); }
  body[data-state="ignored"] #status { color: var(--color-bad); }
  #clock { font-size: var(--text-body); font-variant-numeric: tabular-nums; letter-spacing: 0.04em; }
  .well { position: relative; min-height: 28rem; cursor: grab; touch-action: none; }
  .well:active { cursor: grabbing; }
  #sky-read {
    position: absolute; top: 16px; left: 16px; right: 16px; margin: 0;
    text-align: center; pointer-events: none;
    font-size: var(--text-body); line-height: 1.5; color: var(--color-ink-2);
  }
  .telemetry, .talk {
    min-width: 0; min-height: 0; padding: 24px 16px;
    border-top: 1px solid var(--color-line);
  }
  h2 {
    margin: 0 0 16px;
    font-family: var(--font-body); font-size: var(--text-support); font-weight: 600;
    line-height: 1.25; letter-spacing: 0.12em; text-transform: uppercase; color: var(--color-ink-2);
  }
  .systems { margin: 0; display: flex; flex-direction: column; }
  .systems div {
    display: flex; justify-content: space-between; align-items: baseline;
    gap: 16px; min-width: 0; padding: 8px 0;
    border-bottom: 1px solid var(--color-line);
  }
  .systems div:last-child { border-bottom: 0; }
  .systems dt {
    font-size: var(--text-support); font-weight: 600; letter-spacing: 0.06em;
    text-transform: uppercase; color: var(--color-ink-2);
  }
  .systems dd {
    margin: 0; font-size: var(--text-body); line-height: 1.3; text-align: right;
    font-variant-numeric: tabular-nums; color: var(--color-ink); overflow-wrap: anywhere;
  }
  .systems dd.is-down { color: var(--color-ink-2); }
  .talk { display: flex; flex-direction: column; }
  #log {
    flex: 1; min-height: 0; max-height: 24rem; overflow: auto;
    display: flex; flex-direction: column; gap: 16px; max-width: 65ch;
  }
  #log p { margin: 0; line-height: 1.5; overflow-wrap: anywhere; font-size: var(--text-body); }
  #log .empty, #log .meta { color: var(--color-ink-2); }
  #log p[data-speaker]::before {
    content: attr(data-speaker);
    display: block; margin: 0 0 8px;
    font-size: var(--text-support); font-weight: 600; letter-spacing: 0.12em;
    text-transform: uppercase; color: var(--color-ink-2);
  }
  #permit {
    display: flex; align-items: center; flex-wrap: wrap; gap: 16px;
    padding: 16px; border-top: 1px solid var(--color-accent);
  }
  #permit[hidden] { display: none; }
  #permit p {
    font-size: var(--text-body); font-weight: 600; letter-spacing: 0.12em;
    text-transform: uppercase; color: var(--color-accent);
  }
  #permit-cmd {
    flex: 1 1 12rem; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
    font-size: var(--text-body); color: var(--color-ink);
  }
  .floor {
    display: flex; align-items: center; flex-wrap: wrap; gap: 16px;
    padding: 8px 16px 16px; border-top: 1px solid var(--color-line);
  }
  #text {
    flex: 1 1 12rem; min-width: 0; min-height: 44px;
    background: transparent; color: var(--color-ink);
    border: 0; border-bottom: 1px solid var(--color-line); border-radius: 0;
    font-family: var(--font-body); font-size: var(--text-body); line-height: 1.5;
    padding: 12px 0; outline: none;
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
    letter-spacing: 0.06em; text-transform: uppercase; text-decoration: none; white-space: nowrap;
    cursor: pointer; min-height: 44px; padding: 8px 8px;
    border: 0; border-radius: 0; background: transparent; color: var(--color-ink-2);
    transition: color 180ms cubic-bezier(0.16, 1, 0.3, 1);
  }
  .act:hover { color: var(--color-ink); }
  .act:active { color: var(--color-accent); }
  .act[data-state="loading"] { color: var(--color-accent); }
  .act[data-state="error"] { color: var(--color-bad); }
  .act[data-state="success"] { color: var(--color-ok); }
  #send, #allow { color: var(--color-accent); font-weight: 600; }
  #mic[data-hot="1"] { color: var(--color-bad); }
  @media (min-width: 960px) {
    .room {
      grid-template-columns: 17.5rem minmax(0, 1fr) 22rem;
      grid-template-rows: auto minmax(0, 1fr) auto auto;
    }
    .strip, #permit, .floor { grid-column: 1 / -1; }
    .strip, #permit, .floor, .telemetry, .talk { padding-left: 24px; padding-right: 24px; }
    .well { grid-column: 2; grid-row: 2; min-height: 0; }
    .telemetry {
      grid-column: 1; grid-row: 2; overflow: auto;
      border-top: 0; border-right: 1px solid var(--color-line); padding-top: 24px; padding-bottom: 24px;
    }
    .talk {
      grid-column: 3; grid-row: 2; overflow: hidden;
      border-top: 0; border-left: 1px solid var(--color-line); padding-top: 24px; padding-bottom: 24px;
    }
    #log { max-height: none; }
    .floor { padding-bottom: 24px; }
  }
  @media (max-width: 640px) {
    .epithet { display: none; }
    .meta { gap: 8px; }
  }
  @media (prefers-reduced-motion: reduce) { .act { transition: none; } }
</style>
</head>
<body data-state="idle" data-name="__NAME__" data-load="0">
<canvas id="field" aria-label="constelação"></canvas>
<div class="room">
  <header class="strip">
    <div class="brand">
      <p class="plate-num">XXIX</p>
      <h1>__NAME__</h1>
      <p class="epithet">the Glorious One</p>
    </div>
    <div class="meta">
      <p id="status">pronto</p>
      <p id="clock">00:00:00</p>
    </div>
  </header>
  <div class="well">
    <p id="sky-read">Arraste para orbitar. A roda aproxima.</p>
  </div>
  <aside class="telemetry">
    <h2>Estado</h2>
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
  bg: tok("--color-bg"), ink: tok("--color-ink"), ink2: tok("--color-ink-2"),
  accent: tok("--color-accent"), body: tok("--font-body"),
};
const well = document.querySelector(".well");
const skyRead = document.getElementById("sky-read");
let permitId = "";
let memory = [];
let memoryLinks = [];
let namedOnScreen = [];
let picked = "";
let hovered = "";
let yawUser = 0.42;
let pitchUser = -0.16;
let yawTarget = 0.42;
let pitchTarget = -0.16;
let zoom = 1;
let drag = null;
let dragMoved = 0;
const orbitHint = "Arraste para orbitar. A roda aproxima.";
const GROUPS = {
  notas: { name: "Notas", x: -1.2, y: 0.05, z: 0.25, r: 1.15, rgb: "120, 86, 58" },
  sistemas: { name: "Sistemas", x: 1.25, y: -1.15, z: -0.1, r: 1.15, rgb: "64, 96, 168" },
  orion: { name: "Órion", x: 0.1, y: 1.45, z: -0.55, r: 1.05, rgb: "92, 64, 140" },
};
const MYTH = [
  { id: "meissa", name: "Meissa", greek: "λ", x: 51.2, y: 14.7, mag: 1.8 },
  { id: "betelgeuse", name: "Betelgeuse", greek: "α", x: 25.2, y: 22.9, mag: 3.6, warm: true },
  { id: "bellatrix", name: "Bellatrix", greek: "γ", x: 64.2, y: 26.4, mag: 2.5 },
  { id: "alnitak", name: "Alnitak", greek: "ζ", x: 43.9, y: 53.3, mag: 2.4 },
  { id: "alnilam", name: "Alnilam", greek: "ε", x: 49.8, y: 50.9, mag: 2.5 },
  { id: "mintaka", name: "Mintaka", greek: "δ", x: 55.2, y: 48.0, mag: 2.2 },
  { id: "saiph", name: "Saiph", greek: "κ", x: 34.8, y: 78.4, mag: 2.3 },
  { id: "rigel", name: "Rigel", greek: "β", x: 77.8, y: 73.7, mag: 4.0 },
  { id: "sword", name: "Espada", greek: "", x: 50.9, y: 66.2, mag: 1.6 },
];
const MYTH_LINKS = [
  ["meissa", "betelgeuse"], ["meissa", "bellatrix"], ["betelgeuse", "bellatrix"],
  ["betelgeuse", "alnitak"], ["bellatrix", "mintaka"],
  ["mintaka", "alnilam"], ["alnilam", "alnitak"],
  ["alnitak", "saiph"], ["mintaka", "rigel"], ["alnilam", "sword"],
];
const SYSTEMS = [
  { id: "sys-cerebro", label: "Cérebro", lx: 0, ly: 0, lz: 0 },
  { id: "sys-codex", label: "Codex", lx: -0.58, ly: 0.42, lz: 0.16 },
  { id: "sys-cursor", label: "Cursor", lx: 0.02, ly: 0.64, lz: -0.22 },
  { id: "sys-claude", label: "Claude", lx: 0.6, ly: 0.3, lz: 0.14 },
  { id: "sys-clima", label: "Clima", lx: -0.74, ly: -0.32, lz: 0.22 },
  { id: "sys-noticias", label: "Notícias", lx: -0.18, ly: -0.66, lz: -0.16 },
  { id: "sys-busca", label: "Busca", lx: 0.46, ly: -0.5, lz: 0.24 },
  { id: "sys-lembretes", label: "Lembretes", lx: 0.78, ly: -0.08, lz: -0.3 },
  { id: "sys-voz", label: "Voz", lx: 0.12, ly: 0.02, lz: 0.58 },
];
const SYSTEM_LINKS = [
  ["sys-cerebro", "sys-codex"], ["sys-cerebro", "sys-cursor"], ["sys-cerebro", "sys-claude"],
  ["sys-codex", "sys-cursor"], ["sys-cursor", "sys-claude"], ["sys-claude", "sys-codex"],
  ["sys-cerebro", "sys-clima"], ["sys-cerebro", "sys-noticias"], ["sys-cerebro", "sys-busca"],
  ["sys-cerebro", "sys-lembretes"], ["sys-cerebro", "sys-voz"],
];
const systemText = {
  "sys-cerebro": "Cérebro, ausente.",
  "sys-codex": "Codex, ausente.",
  "sys-cursor": "Cursor, ausente.",
  "sys-claude": "Claude, ausente.",
  "sys-clima": "Clima de São Paulo, ao vivo.",
  "sys-noticias": "Notícias por RSS.",
  "sys-busca": "Busca na web.",
  "sys-lembretes": "Notas deste céu.",
  "sys-voz": "Voz george, ritmo 1.08.",
};
function notePos(index, total) {
  const g = GROUPS.notas;
  const n = Math.max(total, 1);
  const y = ((index + 0.5) / n - 0.5) * 1.2;
  const ring = 0.38 + (index % 3) * 0.14;
  const theta = index * 2.399963 + 0.5;
  return {
    x: g.x + Math.cos(theta) * ring,
    y: g.y + y,
    z: g.z + Math.sin(theta) * ring,
  };
}
function mythPos(star) {
  const g = GROUPS.orion;
  return {
    x: g.x + (star.x - 50) / 42,
    y: g.y + (46 - star.y) / 42,
    z: g.z + ((star.x - 50) * (star.y - 40)) / 9000,
  };
}
function systemPos(star) {
  const g = GROUPS.sistemas;
  return { x: g.x + star.lx, y: g.y + star.ly, z: g.z + star.lz };
}
function buildWorld() {
  const notes = memory.map((star, index) => ({
    star: { id: star.id, label: star.label, text: star.text, kind: "nota" },
    pos: notePos(index, memory.length),
  }));
  const systems = SYSTEMS.map((star) => ({
    star: { id: star.id, label: star.label, text: systemText[star.id] || star.label, kind: "sistema" },
    pos: systemPos(star),
  }));
  const myth = MYTH.map((star) => ({
    star: {
      id: star.id,
      label: star.greek ? star.greek + "  " + star.name : star.name,
      text: star.name + ", da constelação de Órion.",
      kind: "mito",
      warm: !!star.warm,
      mag: star.mag,
    },
    pos: mythPos(star),
  }));
  const all = notes.concat(systems, myth);
  const byId = {};
  for (const node of all) byId[node.star.id] = node;
  const links = [];
  const add = (a, b) => {
    const left = byId[a];
    const right = byId[b];
    if (left && right) links.push([left, right]);
  };
  for (const link of memoryLinks) add(link.a, link.b);
  for (const link of SYSTEM_LINKS) add(link[0], link[1]);
  for (const link of MYTH_LINKS) add(link[0], link[1]);
  if (memory.length > 0 && memory.length <= 12) {
    for (const star of memory) add("sys-lembretes", star.id);
  }
  return { all, links };
}
function dampAngle(current, target, k) {
  let delta = target - current;
  while (delta > Math.PI) delta -= Math.PI * 2;
  while (delta < -Math.PI) delta += Math.PI * 2;
  return current + delta * k;
}
function anglesToward(p) {
  const yaw = Math.atan2(-p.x, -p.z);
  const z1 = p.x * Math.sin(yaw) + p.z * Math.cos(yaw);
  let pitch = Math.atan2(p.y, z1);
  if (z1 < 0) pitch += pitch > 0 ? -Math.PI : Math.PI;
  return { yaw, pitch: Math.max(-1.15, Math.min(1.15, pitch)) };
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
function labelBox(x, y, align, width) {
  const left = align === "right" ? x - width : align === "center" ? x - width / 2 : x;
  return { l: left - 4, r: left + width + 4, t: y - 9, b: y + 9 };
}
function boxesHit(a, b) {
  return !(a.r < b.l || a.l > b.r || a.b < b.t || a.t > b.b);
}
function drawPlate() {
  const w = canvas.width / DPR, h = canvas.height / DPR;
  const rect = well.getBoundingClientRect();
  ctx.clearRect(0, 0, w, h);
  ctx.fillStyle = ink.bg;
  ctx.fillRect(0, 0, w, h);
  if (rect.width < 40 || rect.height < 40) return;
  const cx = rect.left + rect.width / 2;
  const cy = rect.top + rect.height * 0.5;
  const minSide = Math.min(rect.width, rect.height);
  const scale = minSide * 0.32 * zoom;
  const yaw = yawUser;
  const pitch = pitchUser;
  const world = buildWorld();
  ctx.save();
  ctx.beginPath();
  ctx.rect(rect.left, rect.top, rect.width, rect.height);
  ctx.clip();
  const clouds = Object.values(GROUPS).map((group) => ({
    group,
    p: project(rotate(group, yaw, pitch), cx, cy, scale),
  })).sort((a, b) => b.p.z - a.p.z);
  for (const cloud of clouds) {
    const rad = Math.max(56, cloud.group.r * cloud.p.persp * scale);
    const g = ctx.createRadialGradient(cloud.p.x, cloud.p.y, 0, cloud.p.x, cloud.p.y, rad);
    g.addColorStop(0, "rgba(" + cloud.group.rgb + ",0.5)");
    g.addColorStop(0.45, "rgba(" + cloud.group.rgb + ",0.16)");
    g.addColorStop(1, "rgba(" + cloud.group.rgb + ",0)");
    ctx.fillStyle = g;
    ctx.beginPath();
    ctx.arc(cloud.p.x, cloud.p.y, rad, 0, Math.PI * 2);
    ctx.fill();
  }
  const view = world.all.map((node) => {
    const rot = rotate(node.pos, yaw, pitch);
    return { star: node.star, pos: node.pos, p: project(rot, cx, cy, scale) };
  }).sort((a, b) => b.p.z - a.p.z);
  const byId = {};
  for (const item of view) byId[item.star.id] = item;
  ctx.lineWidth = 1;
  for (const pair of world.links) {
    const a = byId[pair[0].star.id];
    const b = byId[pair[1].star.id];
    if (!a || !b) continue;
    const hot = picked && (a.star.id === picked || b.star.id === picked);
    ctx.strokeStyle = hot ? ink.accent : ink.ink2;
    ctx.globalAlpha = hot ? 0.95 : 0.55;
    ctx.setLineDash(hot ? [] : [1.5, 4.5]);
    ctx.beginPath();
    ctx.moveTo(a.p.x, a.p.y);
    ctx.lineTo(b.p.x, b.p.y);
    ctx.stroke();
  }
  ctx.setLineDash([]);
  namedOnScreen = [];
  for (const item of view) {
    const inside = item.p.x >= rect.left + 4 && item.p.x <= rect.right - 4 && item.p.y >= rect.top + 20 && item.p.y <= rect.bottom - 4;
    const chosen = item.star.id === picked;
    const near = item.p.persp;
    const pulse = chosen ? 1 + level * 0.65 : 1;
    ctx.globalAlpha = Math.max(0.4, Math.min(1, 0.3 + near * 0.65));
    if (item.star.kind === "sistema") {
      ctx.strokeStyle = chosen ? ink.accent : ink.ink;
      ctx.lineWidth = 1.25;
      ctx.beginPath();
      ctx.arc(item.p.x, item.p.y, Math.max(5, 8 * near) * pulse, 0, Math.PI * 2);
      ctx.stroke();
      ctx.fillStyle = chosen ? ink.accent : ink.ink;
      ctx.beginPath();
      ctx.arc(item.p.x, item.p.y, Math.max(1.6, 2.2 * near), 0, Math.PI * 2);
      ctx.fill();
    } else {
      const mag = item.star.kind === "mito" ? (item.star.mag || 2) : 3.2;
      ctx.fillStyle = (chosen || item.star.warm) ? ink.accent : ink.ink;
      ctx.beginPath();
      ctx.arc(item.p.x, item.p.y, Math.max(1.8, mag * 0.9 * near) * pulse, 0, Math.PI * 2);
      ctx.fill();
      if (chosen) {
        ctx.strokeStyle = ink.accent;
        ctx.globalAlpha = 0.85;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.arc(item.p.x, item.p.y, Math.max(8, 12 * near), 0, Math.PI * 2);
        ctx.stroke();
      }
    }
    namedOnScreen.push({
      star: item.star, pos: item.pos, x: item.p.x, y: item.p.y,
      outside: inside, align: "left", lx: item.p.x + 12, ly: item.p.y, labelW: 0,
    });
  }
  const boxes = [];
  ctx.font = "400 14px " + ink.body;
  ctx.textBaseline = "middle";
  const ranked = view.slice().sort((a, b) => {
    const af = a.star.id === picked || a.star.id === hovered;
    const bf = b.star.id === picked || b.star.id === hovered;
    if (af !== bf) return af ? -1 : 1;
    const rank = { nota: 0, sistema: 1, mito: 2 };
    return (rank[a.star.kind] || 3) - (rank[b.star.kind] || 3) || (b.p.persp - a.p.persp);
  });
  for (const item of ranked) {
    if (!item.star.label) continue;
    const focus = item.star.id === picked || item.star.id === hovered;
    if (item.star.kind === "mito" && !focus && zoom < 1.45) {
      if (item.star.id !== "betelgeuse" && item.star.id !== "rigel" && item.star.id !== "meissa") continue;
    }
    if (item.p.persp < 0.42 && !focus) continue;
    const onStage = item.p.x >= rect.left + 8 && item.p.x <= rect.right - 8 && item.p.y >= rect.top + 28 && item.p.y <= rect.bottom - 8;
    if (!onStage && item.star.id !== picked) continue;
    const width = ctx.measureText(item.star.label).width;
    const options = [
      { x: item.p.x + 12, y: item.p.y, align: "left" },
      { x: item.p.x - 12, y: item.p.y, align: "right" },
      { x: item.p.x, y: item.p.y - 16, align: "center" },
    ];
    let spot = null;
    let box = null;
    for (const opt of options) {
      const trial = labelBox(opt.x, opt.y, opt.align, width);
      if (trial.l < rect.left + 4 || trial.r > rect.right - 4) continue;
      if (boxes.some((held) => boxesHit(trial, held))) continue;
      spot = opt;
      box = trial;
      break;
    }
    if (!spot && item.star.id === picked) {
      spot = options[0];
      box = labelBox(spot.x, spot.y, spot.align, width);
    }
    if (!spot) continue;
    boxes.push(box);
    const row = namedOnScreen.find((entry) => entry.star.id === item.star.id);
    if (row) { row.align = spot.align; row.lx = spot.x; row.ly = spot.y; row.labelW = width; }
    ctx.globalAlpha = item.star.id === picked ? 1 : 0.92;
    ctx.fillStyle = item.star.id === picked ? ink.accent : ink.ink;
    ctx.textAlign = spot.align;
    ctx.fillText(item.star.label, spot.x, spot.y);
  }
  ctx.font = "600 14px " + ink.body;
  ctx.textAlign = "center";
  for (const group of Object.values(GROUPS)) {
    const above = { x: group.x, y: group.y + group.r * 0.78, z: group.z };
    const p = project(rotate(above, yaw, pitch), cx, cy, scale);
    if (p.persp < 0.4) continue;
    if (p.x < rect.left + 28 || p.x > rect.right - 28 || p.y < rect.top + 24 || p.y > rect.bottom - 12) continue;
    const width = ctx.measureText(group.name).width;
    const box = labelBox(p.x, p.y, "center", width);
    if (boxes.some((held) => boxesHit(box, held))) continue;
    boxes.push(box);
    ctx.globalAlpha = 0.82;
    ctx.fillStyle = ink.ink2;
    ctx.fillText(group.name, p.x, p.y);
  }
  ctx.restore();
  ctx.globalAlpha = 1;
  ctx.setLineDash([]);
}
function starAt(x, y) {
  let best = null;
  let bestD = 26;
  for (const item of namedOnScreen) {
    if (!item.outside) continue;
    const dot = Math.hypot(item.x - x, item.y - y);
    if (dot < bestD) { best = item; bestD = dot; }
    const width = item.labelW || 0;
    if (width > 8 && Math.abs(y - (item.ly || item.y)) <= 12) {
      const left = item.align === "center" ? item.lx - width / 2 : item.align === "right" ? item.lx - width : item.lx;
      if (x >= left - 4 && x <= left + width + 4) { best = item; bestD = 0; }
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
function frame() {
  sampleLevel();
  if (!drag) {
    const k = picked ? 0.08 : 1;
    yawUser = dampAngle(yawUser, yawTarget, k);
    pitchUser += (pitchTarget - pitchUser) * k;
    pitchUser = Math.max(-1.15, Math.min(1.15, pitchUser));
  }
  drawPlate();
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
    const brainById = {};
    for (const brain of data.brains || []) {
      brainById[brain.id] = brain;
      const el = document.getElementById("brain-" + brain.id);
      if (!el) continue;
      el.textContent = brain.up ? "pronto" : "ausente";
      el.classList.toggle("is-down", !brain.up);
    }
    const stateWord = (row) => (row && row.up ? "pronto" : "ausente");
    systemText["sys-codex"] = "Codex, " + stateWord(brainById.codex) + ".";
    systemText["sys-cursor"] = "Cursor, " + stateWord(brainById.cursor) + ".";
    systemText["sys-claude"] = "Claude, " + stateWord(brainById.claude) + ".";
    systemText["sys-cerebro"] = data.up ? "Cérebro, " + (data.model || "pronto") + "." : "Cérebro, ausente.";
    if (picked && String(picked).indexOf("sys-") === 0) {
      skyRead.textContent = systemText[picked] || skyRead.textContent;
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
  hovered = hit ? hit.star.id : "";
  if (!hit) {
    if (choose) {
      picked = "";
      skyRead.textContent = orbitHint;
    } else if (picked) {
      const held = namedOnScreen.find((item) => item.star.id === picked);
      if (held) skyRead.textContent = held.star.kind === "sistema" ? (systemText[held.star.id] || held.star.text) : held.star.text;
    }
    return;
  }
  if (choose) {
    picked = hit.star.id;
    const aim = anglesToward(hit.pos);
    yawTarget = aim.yaw;
    pitchTarget = aim.pitch;
  }
  skyRead.textContent = hit.star.kind === "sistema" ? (systemText[hit.star.id] || hit.star.text) : hit.star.text;
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
  yawUser = drag.yaw + dx * 0.006;
  pitchUser = Math.max(-1.15, Math.min(1.15, drag.pitch + dy * 0.004));
  yawTarget = yawUser;
  pitchTarget = pitchUser;
  if (reduce) drawPlate(0);
});
well.addEventListener("pointerup", () => {
  if (drag && dragMoved < 12) pointStar({ clientX: drag.x, clientY: drag.y }, true);
  drag = null;
  if (reduce) drawPlate(0);
});
well.addEventListener("pointerleave", () => {
  if (!drag && !picked) skyRead.textContent = orbitHint;
});
well.addEventListener("wheel", (ev) => {
  ev.preventDefault();
  zoom = Math.max(0.45, Math.min(3.2, zoom * (ev.deltaY > 0 ? 0.92 : 1.08)));
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
