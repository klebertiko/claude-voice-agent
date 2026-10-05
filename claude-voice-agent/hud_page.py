"""Painel do Orion: céu das notas e dos sistemas.

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
<link href="https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600&display=swap" rel="stylesheet" />
<style>
  /* Uma família. 16 no corpo, 14 no apoio. Sem filete em cada linha. */
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
    --font-body: "Source Sans 3", "Segoe UI", sans-serif;
    --text-support: 0.875rem;
    --text-body: 1rem;
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
    display: flex; align-items: baseline; justify-content: space-between;
    gap: 24px; padding: 24px;
    background: var(--color-bg);
  }
  .strip h1 {
    display: flex; align-items: center; gap: 10px;
    font-family: var(--font-body); font-weight: 600; font-size: var(--text-body);
    line-height: 1.25; letter-spacing: 0;
  }
  .belt { width: 22px; height: 14px; flex: none; }
  .meta { display: flex; align-items: baseline; gap: 24px; }
  #status { font-size: var(--text-body); color: var(--color-ink-2); }
  body[data-state="listening"] #status,
  body[data-state="speaking"] #status,
  body[data-state="thinking"] #status { color: var(--color-accent); }
  body[data-state="ignored"] #status { color: var(--color-bad); }
  #clock { font-size: var(--text-body); font-variant-numeric: tabular-nums; letter-spacing: 0.04em; }
  .well { position: relative; min-height: 28rem; cursor: grab; touch-action: none; }
  .well:active { cursor: grabbing; }
  #sky-read {
    position: absolute; top: auto; bottom: 16px; left: 16px; right: 16px; margin: 0;
    text-align: center; pointer-events: none;
    font-size: var(--text-body); line-height: 1.5; color: var(--color-ink-2);
  }
  .telemetry, .talk {
    min-width: 0; min-height: 0; padding: 8px 24px 32px;
    background: var(--color-bg);
  }
  .systems {
    margin: 0; display: flex; flex-flow: row nowrap; gap: 8px 16px; overflow-x: auto;
    scrollbar-width: thin; scrollbar-color: rgba(232, 238, 246, 0.35) transparent;
  }
  .systems div, .systems button.fact {
    display: flex; justify-content: flex-start; align-items: baseline;
    gap: 8px; min-width: 0; min-height: 44px;
    margin: 0; padding: 0; border: 0; background: transparent;
    font: inherit; color: inherit; cursor: pointer; text-align: left;
  }
  .systems button.fact[aria-pressed="true"] { color: var(--color-accent); }
  .systems .k, .systems dt { font-size: var(--text-body); font-weight: 400; color: var(--color-ink-2); }
  .systems .v, .systems dd {
    margin: 0; font-size: var(--text-body); line-height: 1.5; text-align: left;
    font-variant-numeric: tabular-nums; color: var(--color-ink); overflow-wrap: anywhere;
  }
  .systems .is-down { color: var(--color-ink-2); }
  .talk { display: flex; flex-direction: column; gap: 16px; }
  #note { display: flex; flex-direction: column; gap: 8px; max-width: 72ch; }
  #note[hidden] { display: none; }
  #note-text { font-size: var(--text-body); line-height: 1.5; }
  #note-links { display: flex; flex-wrap: wrap; gap: 8px 16px; }
  #log {
    flex: 1; min-height: 0; max-height: 11rem; overflow: auto;
    display: flex; flex-direction: column; max-width: 72ch;
    scrollbar-width: thin; scrollbar-color: rgba(232, 238, 246, 0.35) transparent;
  }
  #log-lines { margin-top: auto; display: flex; flex-direction: column; gap: 8px; }
  #log p { margin: 0; line-height: 1.5; overflow-wrap: anywhere; font-size: var(--text-body); }
  #log .empty, #log .meta { color: var(--color-ink-2); }
  #log p[data-speaker]::before {
    content: attr(data-speaker);
    margin-right: 8px;
    font-size: var(--text-support); font-weight: 600; color: var(--color-ink-2);
  }
  #permit {
    display: flex; align-items: center; flex-wrap: wrap; gap: 16px;
    padding: 16px 24px; background: var(--color-bg);
  }
  #permit[hidden] { display: none; }
  #permit p { font-size: var(--text-body); font-weight: 600; color: var(--color-accent); }
  #permit-cmd {
    flex: 1 1 12rem; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
    font-size: var(--text-body); color: var(--color-ink);
  }
  .floor {
    display: flex; align-items: center; flex-wrap: wrap; gap: 16px;
    padding: 8px 24px 24px; background: var(--color-bg);
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
    letter-spacing: 0; text-decoration: none; white-space: nowrap;
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
    body { overflow: hidden; }
    .room {
      height: 100vh; min-height: 0;
      grid-template-columns: 1fr;
      grid-template-rows: auto auto minmax(0, 1fr) minmax(7rem, 11rem) auto auto;
    }
    .strip, .telemetry, .well, .talk, #permit, .floor { grid-column: 1; }
    .strip { grid-row: 1; }
    .telemetry { grid-row: 2; padding-top: 0; padding-bottom: 8px; }
    .well { grid-row: 3; min-height: 0; }
    .talk { grid-row: 4; min-height: 0; overflow: hidden; padding-top: 8px; padding-bottom: 8px; }
    #permit { grid-row: 5; }
    .floor { grid-row: 6; }
    #log { max-height: none; }
    .strip, #permit, .floor, .telemetry, .talk { padding-left: 24px; padding-right: 24px; }
  }
  @media (max-width: 959px) {
    #log { max-height: none; overflow: visible; }
  }
  @media (max-width: 640px) {
    .strip, .floor, .telemetry, .talk, #permit { padding-left: 16px; padding-right: 16px; }
    .meta { gap: 16px; }
    .well { min-height: 62vh; }
  }
  @media (prefers-reduced-motion: reduce) { .act { transition: none; } }
</style>
</head>
<body data-state="idle" data-name="__NAME__" data-load="0">
<canvas id="field" aria-label="constelação"></canvas>
<div class="room">
  <header class="strip">
    <h1><svg class="belt" viewBox="0 0 22 14" aria-hidden="true"><circle cx="3" cy="11" r="1.35" fill="currentColor"/><circle cx="11" cy="7" r="1.55" fill="currentColor"/><circle cx="19" cy="3" r="1.35" fill="currentColor"/></svg>__NAME__</h1>
    <div class="meta">
      <p id="status">pronto</p>
      <p id="clock">00:00:00</p>
    </div>
  </header>
  <div class="well">
    <p id="sky-read">Arraste para orbitar. A roda aproxima.</p>
  </div>
  <aside class="telemetry">
    <div class="systems">
      <button type="button" class="fact" data-brain="codex"><span class="k">Codex</span><span class="v is-down" id="brain-codex">ausente</span></button>
      <button type="button" class="fact" data-brain="cursor"><span class="k">Cursor</span><span class="v is-down" id="brain-cursor">ausente</span></button>
      <button type="button" class="fact" data-brain="claude"><span class="k">Claude</span><span class="v is-down" id="brain-claude">ausente</span></button>
      <button type="button" class="fact" data-brain="ollama"><span class="k">Cérebro</span><span class="v is-down" id="brain">ausente</span></button>
      <button type="button" class="fact" data-ask="quais lembretes"><span class="k">Céu</span><span class="v" id="sky">0</span></button>
      <button type="button" class="fact" data-ask="quais lembretes"><span class="k">Lembretes</span><span class="v" id="notes">0</span></button>
      <button type="button" class="fact" data-voice="1"><span class="k">Voz</span><span class="v" id="voice-name">daniel</span></button>
      <button type="button" class="fact" data-ask="qual o ritmo"><span class="k">Ritmo</span><span class="v">1.2</span></button>
      <button type="button" class="fact" data-ask="qual a carga"><span class="k">Carga</span><span class="v" id="load">—</span></button>
      <button type="button" class="fact" data-ask="qual o fuso"><span class="k">Fuso</span><span class="v">Brasília</span></button>
      <button type="button" class="fact" data-ask="qual a data"><span class="k">Data</span><span class="v" id="date">—</span></button>
      <button type="button" class="fact" data-ask="qual seu nome"><span class="k">Sessão</span><span class="v" id="sess">à espera do nome</span></button>
      <button type="button" class="fact" data-draft="anote "><span class="k">Nova nota</span></button>
      <button type="button" class="fact" data-draft="buscar nota "><span class="k">Buscar nota</span></button>
    </div>
  </aside>
  <section class="talk">
    <article id="note" hidden>
      <p id="note-text"></p>
      <div id="note-links"></div>
    </article>
    <div id="log" aria-live="polite"><div id="log-lines"><p class="empty" id="empty">Diga, Senhor.</p></div></div>
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
const logLines = document.getElementById("log-lines");
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
const noteEl = document.getElementById("note");
const noteText = document.getElementById("note-text");
const noteLinks = document.getElementById("note-links");
let permitId = "";
let memory = [];
let memoryLinks = [];
let noteQuery = "";
let namedOnScreen = [];
let picked = "";
let hovered = "";
let yawUser = 0;
let pitchUser = 0;
let yawTarget = 0;
let pitchTarget = 0;
let zoom = 1;
let drag = null;
let dragMoved = 0;
const orbitHint = "Arraste para orbitar. A roda aproxima.";
const GROUPS = {
  notas: { name: "Notas", rgb: "186, 92, 140" },
  sistemas: { name: "Sistemas", rgb: "64, 112, 196" },
};
const SYSTEMS = [
  { id: "sys-cerebro", label: "Cérebro" },
  { id: "sys-codex", label: "Codex" },
  { id: "sys-cursor", label: "Cursor" },
  { id: "sys-claude", label: "Claude" },
  { id: "sys-clima", label: "Clima" },
  { id: "sys-noticias", label: "Notícias" },
  { id: "sys-busca", label: "Busca" },
  { id: "sys-lembretes", label: "Lembretes" },
  { id: "sys-voz", label: "Voz" },
];
const INNER_RING = ["sys-codex", "sys-cursor", "sys-claude"];
const OUTER_RING = ["sys-clima", "sys-noticias", "sys-busca", "sys-lembretes", "sys-voz"];
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
  "sys-clima": "De qual lugar, Senhor?",
  "sys-noticias": "Sobre o que, Senhor?",
  "sys-busca": "Busca na web.",
  "sys-lembretes": "Notas deste céu.",
  "sys-voz": "Voz daniel, ritmo 1.2.",
};
const CAMERA = 4.15;
const FOCAL = 2.55;
const DEPTH = 2.35;
function sceneScale(rect) {
  return Math.max(1, Math.min(rect.width, rect.height) * 0.92);
}
function fitScene(rect) {
  const scale = sceneScale(rect);
  const persp = FOCAL / CAMERA;
  const k = persp * scale;
  const at = (sx, sy) => ({ x: sx / k, y: -sy / k, z: 0 });
  const wide = rect.width >= 700;
  if (wide) {
    const radiusPx = Math.max(84, Math.min(rect.height * 0.34, rect.width * 0.2, (rect.height - 72) / 2));
    const reach = Math.max(radiusPx * 0.85, rect.width / 2 - radiusPx - 56);
    const offset = Math.min(rect.width * 0.28, reach);
    return {
      notas: Object.assign(at(-offset, 0), { radius: radiusPx / k, name: GROUPS.notas.name, rgb: GROUPS.notas.rgb }),
      sistemas: Object.assign(at(offset, 0), { radius: radiusPx / k, name: GROUPS.sistemas.name, rgb: GROUPS.sistemas.rgb }),
    };
  }
  const radiusPx = Math.max(64, Math.min(rect.width * 0.3, rect.height * 0.17, (rect.width - 48) / 2));
  const reach = Math.max(radiusPx * 0.9, rect.height / 2 - radiusPx - 48);
  const offset = Math.min(rect.height * 0.24, reach);
  return {
    notas: Object.assign(at(0, -offset), { radius: radiusPx / k, name: GROUPS.notas.name, rgb: GROUPS.notas.rgb }),
    sistemas: Object.assign(at(0, offset), { radius: radiusPx / k, name: GROUPS.sistemas.name, rgb: GROUPS.sistemas.rgb }),
  };
}
function ringPos(index, total, center, radius, tilt) {
  const n = Math.max(total, 1);
  if (n === 1 || radius <= 0) return { x: center.x, y: center.y, z: center.z || 0 };
  const theta = -Math.PI / 2 + (index / n) * Math.PI * 2;
  const lean = tilt == null ? 0.9 : tilt;
  return {
    x: center.x + Math.cos(theta) * radius,
    y: center.y + Math.sin(theta) * radius * Math.cos(lean),
    z: (center.z || 0) + Math.sin(theta) * radius * Math.sin(lean),
  };
}
function notePos(index, total, center) {
  const n = Math.max(total, 1);
  const ring = n === 1 ? 0 : center.radius * 0.72;
  return ringPos(index, n, center, ring, 0.95);
}
function systemPos(star, center) {
  if (star.id === "sys-cerebro") return { x: center.x, y: center.y, z: center.z || 0 };
  const ringIds = INNER_RING.indexOf(star.id) >= 0 ? INNER_RING : OUTER_RING;
  const index = Math.max(0, ringIds.indexOf(star.id));
  const ring = (ringIds === INNER_RING ? 0.48 : 0.95) * center.radius;
  const tilt = ringIds === INNER_RING ? 1.05 : 0.8;
  return ringPos(index, ringIds.length, center, ring, tilt);
}
let restKey = "";
let rest = {};
function settle() {
  const key = memory.map((star) => star.id).join(",") + "|" + memoryLinks.map((link) => link.a + "-" + link.b).join(",");
  if (key === restKey) return rest;
  restKey = key;
  const nodes = [];
  memory.forEach((star, index) => {
    const p = notePos(index, memory.length, { x: 0, y: 0, z: 0, radius: 1 });
    nodes.push({ id: star.id, x: p.x, y: p.y, z: p.z, hx: p.x, hy: p.y, hz: p.z, group: "nota" });
  });
  SYSTEMS.forEach((star) => {
    const p = systemPos(star, { x: 0, y: 0, z: 0, radius: 1 });
    nodes.push({ id: star.id, x: p.x, y: p.y, z: p.z, hx: p.x, hy: p.y, hz: p.z, group: "sistema" });
  });
  const by = {};
  for (const node of nodes) by[node.id] = node;
  const pairs = [];
  const add = (a, b) => {
    if (by[a] && by[b] && by[a].group === by[b].group) pairs.push([by[a], by[b]]);
  };
  for (const link of memoryLinks) add(link.a, link.b);
  for (const link of SYSTEM_LINKS) add(link[0], link[1]);
  for (let step = 0; step < 40; step++) {
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const a = nodes[i];
        const b = nodes[j];
        if (a.group !== b.group) continue;
        const dx = a.x - b.x;
        const dy = a.y - b.y;
        const dz = a.z - b.z;
        const dist = Math.max(0.05, Math.hypot(dx, dy, dz));
        const push = Math.min(0.06, 0.012 / (dist * dist));
        a.x += dx / dist * push; a.y += dy / dist * push; a.z += dz / dist * push;
        b.x -= dx / dist * push; b.y -= dy / dist * push; b.z -= dz / dist * push;
      }
    }
    for (const pair of pairs) {
      const a = pair[0];
      const b = pair[1];
      a.x += (b.x - a.x) * 0.045; a.y += (b.y - a.y) * 0.045; a.z += (b.z - a.z) * 0.045;
      b.x += (a.x - b.x) * 0.045; b.y += (a.y - b.y) * 0.045; b.z += (a.z - b.z) * 0.045;
    }
    for (const node of nodes) {
      node.x += (node.hx - node.x) * 0.08;
      node.y += (node.hy - node.y) * 0.08;
      node.z += (node.hz - node.z) * 0.08;
      const limit = node.group === "nota" ? 0.95 : 1.2;
      const mag = Math.hypot(node.x, node.y, node.z);
      if (mag > limit) {
        node.x *= limit / mag; node.y *= limit / mag; node.z *= limit / mag;
      }
    }
  }
  rest = {};
  for (const node of nodes) rest[node.id] = node;
  return rest;
}
function place(local, center) {
  return {
    x: center.x + local.x * center.radius,
    y: center.y + local.y * center.radius,
    z: (center.z || 0) + local.z * center.radius * DEPTH,
  };
}
function buildWorld(fit) {
  const scene = fit || fitScene(well.getBoundingClientRect());
  const laid = settle();
  const notes = memory.map((star, index) => ({
    star: { id: star.id, label: star.label, text: star.text, kind: "nota" },
    pos: place(laid[star.id] || notePos(index, memory.length, { x: 0, y: 0, z: 0, radius: 1 }), scene.notas),
  }));
  const systems = SYSTEMS.map((star) => ({
    star: { id: star.id, label: star.label, text: systemText[star.id] || star.label, kind: "sistema" },
    pos: place(laid[star.id] || systemPos(star, { x: 0, y: 0, z: 0, radius: 1 }), scene.sistemas),
  }));
  const all = notes.concat(systems);
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
  const z = p.z + CAMERA / zoom;
  const persp = FOCAL / Math.max(0.35, z);
  return { x: cx + p.x * persp * scale, y: cy - p.y * persp * scale, persp, z: p.z };
}
const glowCache = {};
function glowSprite(rgb) {
  const cached = glowCache[rgb];
  if (cached) return cached;
  const sprite = document.createElement("canvas");
  sprite.width = 64;
  sprite.height = 64;
  const pen = sprite.getContext("2d");
  const grad = pen.createRadialGradient(32, 32, 0, 32, 32, 32);
  grad.addColorStop(0, "rgba(" + rgb + ",0.92)");
  grad.addColorStop(0.2, "rgba(" + rgb + ",0.4)");
  grad.addColorStop(1, "rgba(" + rgb + ",0)");
  pen.fillStyle = grad;
  pen.beginPath();
  pen.arc(32, 32, 32, 0, Math.PI * 2);
  pen.fill();
  glowCache[rgb] = sprite;
  return sprite;
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
function labelSpots(x, y, cx0, cy0) {
  const spots = [
    { x: x + 14, y, align: "left" },
    { x: x - 14, y, align: "right" },
    { x, y: y - 18, align: "center" },
    { x, y: y + 18, align: "center" },
  ];
  if (cx0 != null) {
    const dx = x - cx0;
    const dy = y - cy0;
    const len = Math.hypot(dx, dy) || 1;
    const align = dx >= 0 ? "left" : "right";
    spots.unshift({
      x: x + (dx / len) * 18 + (align === "left" ? 6 : -6),
      y: y + (dy / len) * 14,
      align,
    });
  }
  return spots;
}
function paintNebula(cloud) {
  const rad = Math.max(96, cloud.maxD * 1.75);
  ctx.save();
  ctx.translate(cloud.x, cloud.y);
  ctx.rotate(cloud.angle || 0);
  ctx.scale(1, 0.58);
  const disc = ctx.createRadialGradient(0, 0, 0, 0, 0, rad);
  disc.addColorStop(0, "rgba(" + cloud.rgb + ",0.5)");
  disc.addColorStop(0.22, "rgba(" + cloud.rgb + ",0.26)");
  disc.addColorStop(0.55, "rgba(" + cloud.rgb + ",0.1)");
  disc.addColorStop(1, "rgba(" + cloud.rgb + ",0)");
  ctx.fillStyle = disc;
  ctx.beginPath();
  ctx.arc(0, 0, rad, 0, Math.PI * 2);
  ctx.fill();
  const arm = rad * 0.34;
  const dust = ctx.createRadialGradient(arm, 0, 0, arm, 0, rad * 0.62);
  dust.addColorStop(0, "rgba(" + cloud.rgb + ",0.2)");
  dust.addColorStop(1, "rgba(" + cloud.rgb + ",0)");
  ctx.fillStyle = dust;
  ctx.beginPath();
  ctx.arc(arm, 0, rad * 0.62, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();
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
  const fit = fitScene(rect);
  const scale = sceneScale(rect) * zoom;
  const yaw = yawUser;
  const pitch = pitchUser;
  const world = buildWorld(fit);
  ctx.save();
  ctx.beginPath();
  ctx.rect(rect.left, rect.top, rect.width, rect.height);
  ctx.clip();
  const view = world.all.map((node) => {
    const rot = rotate(node.pos, yaw, pitch);
    return { star: node.star, pos: node.pos, p: project(rot, cx, cy, scale) };
  }).sort((a, b) => b.p.z - a.p.z);
  const centroids = {};
  for (const key of ["nota", "sistema"]) {
    const pts = view.filter((item) => item.star.kind === key);
    if (!pts.length) continue;
    let sx = 0, sy = 0, sz = 0;
    for (const item of pts) { sx += item.p.x; sy += item.p.y; sz += item.p.z; }
    sx /= pts.length; sy /= pts.length; sz /= pts.length;
    let maxD = 0, sxx = 0, syy = 0, sxy = 0;
    for (const item of pts) {
      const dx = item.p.x - sx;
      const dy = item.p.y - sy;
      maxD = Math.max(maxD, Math.hypot(dx, dy));
      sxx += dx * dx;
      syy += dy * dy;
      sxy += dx * dy;
    }
    const angle = 0.5 * Math.atan2(2 * sxy, sxx - syy);
    const meta = key === "nota" ? fit.notas : fit.sistemas;
    centroids[key] = { x: sx, y: sy, z: sz, maxD, angle, name: meta.name, rgb: meta.rgb };
  }
  const clouds = Object.values(centroids).sort((a, b) => b.z - a.z);
  for (const cloud of clouds) paintNebula(cloud);
  const byId = {};
  for (const item of view) byId[item.star.id] = item;
  const focusId = picked || hovered;
  const neigh = new Set();
  if (focusId) {
    neigh.add(focusId);
    for (const pair of world.links) {
      const a = pair[0].star.id;
      const b = pair[1].star.id;
      if (a === focusId) neigh.add(b);
      if (b === focusId) neigh.add(a);
    }
  }
  ctx.lineCap = "round";
  for (const pair of world.links) {
    const a = byId[pair[0].star.id];
    const b = byId[pair[1].star.id];
    if (!a || !b) continue;
    const hot = picked && (a.star.id === picked || b.star.id === picked);
    const aside = focusId && !neigh.has(a.star.id) && !neigh.has(b.star.id);
    const dx = b.p.x - a.p.x;
    const dy = b.p.y - a.p.y;
    const len = Math.hypot(dx, dy) || 1;
    const pad = 16;
    if (len < pad * 2 + 8) continue;
    const ux = dx / len;
    const uy = dy / len;
    const depth = Math.max(0.45, Math.min(1, ((a.p.persp + b.p.persp) / 2) / 0.62));
    ctx.strokeStyle = hot ? ink.accent : ink.ink;
    ctx.globalAlpha = (hot ? 1 : aside ? 0.14 : 0.9) * depth;
    ctx.lineWidth = hot ? 1.6 : 1.25;
    ctx.setLineDash(hot ? [5, 6] : [8, 10]);
    ctx.beginPath();
    ctx.moveTo(a.p.x + ux * pad, a.p.y + uy * pad);
    ctx.lineTo(b.p.x - ux * pad, b.p.y - uy * pad);
    ctx.stroke();
  }
  ctx.setLineDash([]);
  namedOnScreen = [];
  for (const item of view) {
    const inside = item.p.x >= rect.left + 4 && item.p.x <= rect.right - 4 && item.p.y >= rect.top + 8 && item.p.y <= rect.bottom - 28;
    const chosen = item.star.id === picked;
    const near = item.p.persp;
    const pulse = chosen ? 1 + level * 0.65 : 1;
    const dim = item.star.kind === "nota" && noteQuery && !noteHit(item.star);
    const aside = focusId && !neigh.has(item.star.id);
    const rgb = chosen ? "212, 196, 168" : item.star.kind === "nota" ? GROUPS.notas.rgb : GROUPS.sistemas.rgb;
    ctx.globalAlpha = (dim ? 0.16 : aside ? 0.2 : 1) * Math.max(0.45, Math.min(1, 0.35 + near * 0.6));
    const size = (item.star.kind === "sistema" ? 42 : 34) * Math.max(0.75, near) * pulse;
    const sprite = glowSprite(rgb);
    ctx.drawImage(sprite, item.p.x - size / 2, item.p.y - size / 2, size, size);
    ctx.fillStyle = chosen ? ink.accent : ink.ink;
    ctx.beginPath();
    ctx.arc(item.p.x, item.p.y, (item.star.kind === "sistema" ? 3.1 : 2.8) * pulse, 0, Math.PI * 2);
    ctx.fill();
    if (item.star.kind === "sistema") {
      ctx.strokeStyle = chosen ? ink.accent : ink.ink;
      ctx.lineWidth = 1.35;
      ctx.beginPath();
      ctx.arc(item.p.x, item.p.y, Math.max(7, 11 * near) * pulse, 0, Math.PI * 2);
      ctx.stroke();
    }
    namedOnScreen.push({
      star: item.star, pos: item.pos, x: item.p.x, y: item.p.y,
      outside: inside, align: "left", lx: item.p.x + 12, ly: item.p.y, labelW: 0,
    });
  }
  const boxes = [];
  ctx.textBaseline = "middle";
  ctx.font = "600 14px " + ink.body;
  ctx.textAlign = "center";
  for (const cloud of Object.values(centroids)) {
    const y = cloud.y - Math.max(36, cloud.maxD) - 10;
    if (y < rect.top + 12 || y > rect.bottom - 36) continue;
    const width = ctx.measureText(cloud.name).width;
    const box = labelBox(cloud.x, y, "center", width);
    if (box.l < rect.left + 4 || box.r > rect.right - 4) continue;
    boxes.push(box);
    ctx.globalAlpha = 0.82;
    ctx.fillStyle = ink.ink2;
    ctx.fillText(cloud.name, cloud.x, y);
  }
  ctx.font = "400 14px " + ink.body;
  const ranked = view.slice().sort((a, b) => {
    const af = a.star.id === picked || a.star.id === hovered;
    const bf = b.star.id === picked || b.star.id === hovered;
    if (af !== bf) return af ? -1 : 1;
    const rank = { nota: 0, sistema: 1 };
    return (rank[a.star.kind] || 3) - (rank[b.star.kind] || 3) || (b.p.persp - a.p.persp);
  });
  for (const item of ranked) {
    if (!item.star.label) continue;
    if (item.star.kind === "nota" && noteQuery && !noteHit(item.star) && item.star.id !== picked) continue;
    const focus = item.star.id === picked || item.star.id === hovered;
    if (focusId && !neigh.has(item.star.id) && !focus) continue;
    if (item.p.persp < 0.42 && !focus) continue;
    const onStage = item.p.x >= rect.left + 8 && item.p.x <= rect.right - 8 && item.p.y >= rect.top + 12 && item.p.y <= rect.bottom - 36;
    if (!onStage && item.star.id !== picked) continue;
    const width = ctx.measureText(item.star.label).width;
    const home = centroids[item.star.kind];
    const options = labelSpots(item.p.x, item.p.y, home && home.x, home && home.y);
    let spot = null;
    let box = null;
    for (const opt of options) {
      const trial = labelBox(opt.x, opt.y, opt.align, width);
      if (trial.l < rect.left + 4 || trial.r > rect.right - 4 || trial.t < rect.top + 4 || trial.b > rect.bottom - 28) continue;
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
  ctx.restore();
  ctx.globalAlpha = 1;
  ctx.setLineDash([]);
}
function starAt(x, y) {
  let best = null;
  let bestD = 32;
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
let raf = 0;
function wake() {
  if (reduce) { drawPlate(); return; }
  if (raf) return;
  raf = requestAnimationFrame(frame);
}
function frame() {
  sampleLevel();
  let moving = !!drag || level > 0.03;
  if (!drag) {
    const k = picked ? 0.08 : 1;
    const nextYaw = dampAngle(yawUser, yawTarget, k);
    let nextPitch = pitchUser + (pitchTarget - pitchUser) * k;
    nextPitch = Math.max(-1.15, Math.min(1.15, nextPitch));
    if (Math.abs(nextYaw - yawUser) > 0.0006 || Math.abs(nextPitch - pitchUser) > 0.0006) moving = true;
    yawUser = nextYaw;
    pitchUser = nextPitch;
  }
  drawPlate();
  raf = moving ? requestAnimationFrame(frame) : 0;
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
  wake();
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
  if (cls === "user") p.dataset.speaker = "Senhor";
  if (cls === "agent") p.dataset.speaker = "Orion";
  (logLines || logEl).appendChild(p);
  requestAnimationFrame(() => { logEl.scrollTop = logEl.scrollHeight; });
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
    const choice = data.choice || "";
    systemText["sys-codex"] = (choice === "codex" ? "Codex, escolhido." : "Codex, " + stateWord(brainById.codex) + ".");
    systemText["sys-cursor"] = (choice === "cursor" ? "Cursor, escolhido." : "Cursor, " + stateWord(brainById.cursor) + ".");
    systemText["sys-claude"] = (choice === "claude" ? "Claude, escolhido." : "Claude, " + stateWord(brainById.claude) + ".");
    systemText["sys-cerebro"] = (choice === "ollama" ? "Cérebro local, escolhido." : (data.up ? "Cérebro, " + (data.model || "pronto") + "." : "Cérebro, ausente."));
    for (const btn of document.querySelectorAll(".fact[data-brain]")) {
      btn.setAttribute("aria-pressed", btn.dataset.brain === choice ? "true" : "false");
    }
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
    wake();
  } catch (err) { /* o céu fica como está */ }
}
function fold(value) {
  return (value || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
}
function noteHit(star) {
  if (!noteQuery) return true;
  return fold(star.text || star.label).includes(noteQuery);
}
function linksOf(id) {
  const ids = new Set();
  for (const link of memoryLinks) {
    if (link.a === id) ids.add(link.b);
    if (link.b === id) ids.add(link.a);
  }
  return memory.filter((star) => ids.has(star.id));
}
function openNote(star) {
  if (!noteEl) return;
  noteEl.hidden = false;
  noteText.textContent = star.text || star.label;
  noteLinks.replaceChildren();
  const linked = linksOf(star.id);
  if (!linked.length) {
    const empty = document.createElement("p");
    empty.className = "meta";
    empty.textContent = "Sem ligações.";
    noteLinks.appendChild(empty);
    return;
  }
  for (const other of linked) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "act";
    btn.textContent = other.label;
    btn.addEventListener("click", () => focusStar(other.id));
    noteLinks.appendChild(btn);
  }
}
function focusStar(id) {
  const star = memory.find((item) => item.id === id);
  if (!star) return;
  picked = id;
  skyRead.textContent = star.text || star.label;
  const node = buildWorld(fitScene(well.getBoundingClientRect())).all.find((item) => item.star.id === id);
  if (node) {
    const aim = anglesToward(node.pos);
    yawTarget = aim.yaw;
    pitchTarget = aim.pitch;
  }
  openNote(star);
}
async function sendText(value) {
  const folded = fold(value);
  if (folded.startsWith("buscar nota ")) noteQuery = folded.slice("buscar nota ".length).trim();
  else if (folded.startsWith("notas sobre ")) noteQuery = folded.slice("notas sobre ".length).trim();
  else if (folded.startsWith("anote ") || folded.startsWith("anota ")) noteQuery = "";
  setState("thinking");
  try { await showTurn(await post("/api/turn", { text: value }), null); }
  catch (err) { setState("idle"); addLine("meta", "Não consegui falar agora."); }
}
async function chooseBrain(id) {
  setState("thinking");
  try {
    const data = await post("/api/use", { id });
    for (const btn of document.querySelectorAll(".fact[data-brain]")) {
      btn.setAttribute("aria-pressed", btn.dataset.brain === data.choice ? "true" : "false");
    }
    if (data.reply) {
      addLine("agent", data.reply);
      skyRead.textContent = data.reply;
    }
    if (data.audio_b64) await playWav(data.audio_b64);
    else setState("idle");
  } catch (err) {
    setState("idle");
    addLine("meta", "Não consegui escolher o cérebro.");
  }
}
function runSystem(id) {
  const brains = { "sys-codex": "codex", "sys-cursor": "cursor", "sys-claude": "claude", "sys-cerebro": "ollama" };
  if (brains[id]) { chooseBrain(brains[id]); return; }
  if (id === "sys-clima") {
    text.value = "tempo em ";
    text.focus();
    skyRead.textContent = "De qual lugar, Senhor?";
    return;
  }
  if (id === "sys-noticias") {
    text.value = "notícias sobre ";
    text.focus();
    skyRead.textContent = "Sobre o que, Senhor?";
    return;
  }
  if (id === "sys-lembretes") { sendText("quais lembretes"); return; }
  if (id === "sys-voz") { voiceBtn.click(); return; }
  if (id === "sys-busca") {
    text.value = "busque ";
    text.focus();
    skyRead.textContent = "O que devo procurar, Senhor?";
  }
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
    if (hit.star.kind === "nota") openNote(hit.star);
    else runSystem(hit.star.id);
  }
  skyRead.textContent = hit.star.kind === "sistema" ? (systemText[hit.star.id] || hit.star.text) : hit.star.text;
}
well.addEventListener("pointerdown", (ev) => {
  drag = { x: ev.clientX, y: ev.clientY, yaw: yawUser, pitch: pitchUser };
  dragMoved = 0;
  well.setPointerCapture(ev.pointerId);
  wake();
});
well.addEventListener("pointermove", (ev) => {
  if (!drag) { pointStar(ev, false); wake(); return; }
  const dx = ev.clientX - drag.x;
  const dy = ev.clientY - drag.y;
  dragMoved = Math.max(dragMoved, Math.hypot(dx, dy));
  yawUser = drag.yaw + dx * 0.006;
  pitchUser = Math.max(-1.15, Math.min(1.15, drag.pitch + dy * 0.004));
  yawTarget = yawUser;
  pitchTarget = pitchUser;
  wake();
});
well.addEventListener("pointerup", () => {
  if (drag && dragMoved < 12) pointStar({ clientX: drag.x, clientY: drag.y }, true);
  drag = null;
  wake();
});
well.addEventListener("pointerleave", () => {
  if (!drag) hovered = "";
  if (!drag && !picked) skyRead.textContent = orbitHint;
  wake();
});
well.addEventListener("wheel", (ev) => {
  ev.preventDefault();
  zoom = Math.max(0.45, Math.min(3.2, zoom * (ev.deltaY > 0 ? 0.92 : 1.08)));
  wake();
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
  refreshSky();
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
  const folded = fold(value);
  if (folded.startsWith("buscar nota ")) noteQuery = folded.slice("buscar nota ".length).trim();
  else if (folded.startsWith("notas sobre ")) noteQuery = folded.slice("notas sobre ".length).trim();
  else if (folded.startsWith("anote ") || folded.startsWith("anota ")) noteQuery = "";
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
for (const btn of document.querySelectorAll(".fact")) {
  btn.addEventListener("click", () => {
    if (btn.dataset.brain) { chooseBrain(btn.dataset.brain); return; }
    if (btn.dataset.voice) { voiceBtn.click(); return; }
    if (btn.dataset.draft) { text.value = btn.dataset.draft; text.focus(); return; }
    if (btn.dataset.ask) sendText(btn.dataset.ask);
  });
}
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
addEventListener("resize", () => { resize(); wake(); });
resize();
tickClock();
setInterval(tickClock, 1000);
refreshBrain();
setInterval(refreshBrain, 5000);
wake();
</script>
</body>
</html>
"""


def render_page(name: str, wake: str) -> str:
    """Injeta o nome da persona. O microfone pede só áudio."""
    safe_name = name.replace("<", "").replace(">", "").replace('"', "").replace("&", "")
    safe_wake = wake.replace("<", "").replace(">", "").replace('"', "").replace("&", "")
    return _PAGE.replace("__NAME__", safe_name).replace("__WAKE__", safe_wake)
