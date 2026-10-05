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
    --color-line: rgba(232, 238, 246, 0.55);
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
    display: flex; align-items: center; justify-content: space-between;
    gap: 24px; padding: 24px;
    background: var(--color-bg);
  }
  .strip h1 {
    display: flex; align-items: center; gap: 10px;
    font-family: var(--font-body); font-weight: 600; font-size: var(--text-body);
    line-height: 1.25; letter-spacing: 0;
  }
  .mark { width: 40px; height: 40px; flex: none; color: var(--color-accent); }
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
    position: absolute; top: auto; bottom: 12px; left: 16px; right: 16px; margin: 0;
    text-align: center; pointer-events: none;
    font-size: var(--text-support); line-height: 1.4; color: var(--color-ink-2);
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }
  #sky-read[hidden] { display: none; }
  body:has(#note:not([hidden])) #sky-read { display: none; }
  .telemetry, .talk {
    min-width: 0; min-height: 0; padding: 8px 24px 32px;
    background: var(--color-bg);
  }
  .systems {
    margin: 0; display: flex; flex-flow: row nowrap; gap: 6px; overflow-x: auto;
    scrollbar-width: thin; scrollbar-color: rgba(232, 238, 246, 0.35) transparent;
  }
  .systems .band { display: contents; }
  .systems div, .systems button.fact {
    display: flex; justify-content: flex-start; align-items: baseline;
    gap: 8px; min-width: 0; min-height: 44px; flex: none; white-space: nowrap;
    margin: 0; padding: 0; border: 0; background: transparent;
    font: inherit; color: inherit; cursor: pointer; text-align: left;
  }
  .systems button.fact {
    flex-direction: column; align-items: flex-start; justify-content: flex-end;
    gap: 2px; min-width: 44px; padding-bottom: 2px;
  }
  .telemetry { position: relative; }
  .telemetry:has(.systems.has-more)::after {
    content: "";
    position: absolute; right: var(--more-x, 6px); top: 50%;
    width: 6px; height: 6px; margin-top: -3px;
    border-right: 1.5px solid var(--color-ink-2);
    border-bottom: 1.5px solid var(--color-ink-2);
    transform: rotate(-45deg);
    pointer-events: none;
  }
  .systems button.fact[aria-pressed="true"],
  .systems button.fact[aria-pressed="true"] .k,
  .systems button.fact[aria-pressed="true"] .v { color: var(--color-accent); }
  .systems .k, .systems dt { font-size: var(--text-support); font-weight: 400; line-height: 1.2; color: var(--color-ink-2); white-space: nowrap; }
  .systems .v, .systems dd {
    margin: 0; font-size: var(--text-body); line-height: 1.2; text-align: left; white-space: nowrap;
    font-variant-numeric: tabular-nums; color: var(--color-ink); overflow-wrap: normal;
  }
  .systems .is-down { color: var(--color-ink-2); }
  .systems button.fact:not(:has(.v)) .k { font-size: var(--text-body); line-height: 1.25; }
  .talk { display: flex; flex-direction: column; gap: 16px; }
  #note { display: flex; flex-direction: column; gap: 8px; max-width: 72ch; }
  #note[hidden] { display: none; }
  #note-text { font-size: var(--text-body); line-height: 1.5; }
  #note-links { display: flex; flex-wrap: wrap; align-items: center; gap: 8px 16px; }
  #note-links .k { font-size: var(--text-support); line-height: 1.2; color: var(--color-ink-2); }
  #note-links .act { color: var(--color-accent); }
  #log {
    flex: 1; min-height: 0; max-height: 11rem; overflow: auto;
    display: flex; flex-direction: column; max-width: 72ch;
    scrollbar-width: thin; scrollbar-color: rgba(232, 238, 246, 0.35) transparent;
  }
  #log-lines { margin-top: auto; display: flex; flex-direction: column; gap: 8px; }
  #log p { margin: 0; line-height: 1.5; overflow-wrap: anywhere; font-size: var(--text-body); }
  #log:has(#empty) { display: none; }
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
    .systems { justify-content: space-between; align-items: flex-end; gap: 32px; }
    .systems .band { display: flex; align-items: flex-end; gap: 20px; }
  }
  @media (min-width: 960px) {
    body { overflow: hidden; }
    .room {
      height: 100vh; min-height: 0;
      grid-template-columns: 1fr;
      grid-template-rows: auto minmax(0, 1fr) auto auto auto auto;
    }
    .strip, .telemetry, .well, .talk, #permit, .floor { grid-column: 1; }
    .strip { grid-row: 1; }
    .well { grid-row: 2; min-height: 0; }
    .telemetry { grid-row: 3; padding-top: 4px; padding-bottom: 4px; }
    .talk { grid-row: 4; min-height: 0; overflow: hidden; padding-top: 8px; padding-bottom: 8px; }
    #permit { grid-row: 5; }
    .floor { grid-row: 6; }
    #log { max-height: 9.5rem; }
    .strip, #permit, .floor, .telemetry, .talk { padding-left: 24px; padding-right: 24px; }
  }
  @media (max-width: 959px) {
    body { overflow: hidden; }
    .room {
      height: 100vh; min-height: 0;
      grid-template-rows: auto minmax(0, 1fr) auto auto auto auto;
    }
    .strip { grid-row: 1; }
    .well { grid-row: 2; min-height: 0; }
    .telemetry { grid-row: 3; padding-top: 4px; padding-bottom: 4px; }
    .talk { grid-row: 4; min-height: 0; overflow: hidden; padding-top: 8px; padding-bottom: 8px; }
    #permit { grid-row: 5; }
    .floor { grid-row: 6; }
    #log { max-height: 6rem; overflow: auto; }
  }
  @media (min-width: 641px) and (max-width: 959px) {
    .room:has(#note:not([hidden])) {
      grid-template-rows: auto minmax(0, 1fr) auto auto auto auto;
    }
    .room:has(#note:not([hidden])) #log { max-height: 5.5rem; }
  }
  @media (max-width: 640px) {
    .room {
      grid-template-rows: auto minmax(0, 1fr) auto minmax(2.75rem, 4rem) auto auto;
    }
    .room:not(:has(#empty)) {
      grid-template-rows: auto minmax(0, 1fr) auto minmax(2.75rem, 4rem) auto auto;
    }
    #log { max-height: 3.5rem; }
    /* A nota aberta fica na faixa dos instrumentos. O céu não encolhe. */
    #note:not([hidden]) {
      position: fixed;
      z-index: 5;
      left: 0;
      right: 0;
      bottom: var(--note-bottom, 65px);
      height: 52px;
      margin: 0;
      padding: 4px 16px;
      display: flex;
      flex-flow: row nowrap;
      align-items: center;
      gap: 16px;
      overflow: hidden;
      background: var(--color-bg);
      max-width: none;
    }
    #note:not([hidden]) #note-text {
      flex: 1 1 auto;
      min-width: 46%;
      overflow-x: auto;
      overflow-y: hidden;
      text-overflow: clip;
      white-space: nowrap;
      line-height: 1.25;
      scrollbar-width: none;
    }
    #note:not([hidden]) #note-text::-webkit-scrollbar { height: 0; display: none; }
    #note:not([hidden]) #note-links {
      flex: 0 1 auto;
      max-width: 50%;
      min-width: 0;
      flex-wrap: nowrap;
      overflow-x: auto;
      scrollbar-width: none;
    }
    #note:not([hidden]) #note-links .k,
    #note:not([hidden]) #note-links .act { flex: none; }
    #note:not([hidden]) #note-links .act { overflow: hidden; text-overflow: ellipsis; }
    #note:not([hidden]) #note-links.has-more {
      mask-image: linear-gradient(90deg, transparent 0, transparent var(--link-clip-left, 0px), #000 var(--link-clip-left, 0px), #000 var(--link-clip, 100%), transparent var(--link-clip, 100%));
    }
    #note:not([hidden]) #note-links::-webkit-scrollbar { height: 0; display: none; }
    .strip { padding: 12px 16px; }
    .mark { width: 32px; height: 32px; }
    .floor, .telemetry, .talk, #permit { padding-left: 16px; padding-right: 16px; }
    .well { grid-row: 2; min-height: 0; }
    .telemetry { grid-row: 3; padding-top: 4px; padding-bottom: 4px; }
    .talk { grid-row: 4; padding-top: 4px; padding-bottom: 4px; }
    #permit { grid-row: 5; }
    .floor { grid-row: 6; padding-top: 4px; padding-bottom: 12px; flex-wrap: nowrap; gap: 8px; }
    .floor .act { min-width: 44px; padding-left: 4px; padding-right: 4px; }
    /* A permissão cobre o piso. O céu não encolhe. */
    #permit:not([hidden]) {
      position: fixed;
      z-index: 6;
      left: 0;
      right: 0;
      bottom: var(--permit-bottom, 0px);
      height: var(--permit-height, 65px);
      margin: 0;
      padding: 0 16px;
      display: flex;
      flex-flow: row nowrap;
      align-items: center;
      gap: 8px;
      overflow: hidden;
      background: var(--color-bg);
      max-width: none;
    }
    #permit:not([hidden]) p { flex: none; }
    #permit:not([hidden]) #permit-cmd {
      flex: 1 1 0;
      min-width: 0;
      overflow-x: auto;
      overflow-y: hidden;
      text-overflow: clip;
      white-space: nowrap;
      scrollbar-width: none;
    }
    #permit:not([hidden]) #permit-cmd::-webkit-scrollbar { height: 0; display: none; }
    #permit:not([hidden]) .act { flex: none; min-width: 44px; padding-left: 4px; padding-right: 4px; }
    #text { flex: 1 1 auto; min-width: 0; }
    .meta { gap: 16px; }
    .systems { flex-flow: row nowrap; overflow-x: auto; }
    .systems button.fact { flex: none; }
  }
  @media (max-width: 640px) and (max-height: 700px) {
    .room,
    .room:has(#empty),
    .room:not(:has(#empty)),
    .room:has(#note:not([hidden])) {
      grid-template-rows: auto minmax(0, 1fr) auto 0 auto auto;
    }
    .talk { padding-top: 0; padding-bottom: 0; }
    /* A fala fica na folga sob os nomes. O céu não encolhe. */
    .room:not(:has(#empty)) #log {
      position: fixed;
      z-index: 4;
      left: 0;
      right: 0;
      bottom: var(--log-bottom, 117px);
      height: 1.5rem;
      max-height: 1.5rem;
      margin: 0;
      padding: 0 16px;
      background: var(--color-bg);
      overflow: auto;
      scrollbar-width: none;
    }
    .room:not(:has(#empty)) #log::-webkit-scrollbar { height: 0; display: none; }
    .room:not(:has(#empty)) #log p { white-space: nowrap; }
    .room:not(:has(#empty)) #sky-read { display: none; }
  }
  @media (max-height: 780px) and (min-width: 641px) {
    #log, .room:has(#note:not([hidden])) #log { max-height: 3.5rem; }
  }
  @media (max-height: 740px) and (min-width: 641px) {
    .strip { padding-top: 12px; padding-bottom: 12px; }
    .floor { padding-bottom: 12px; }
  }
  /* Numa janela baixa, a nota e a permissão não roubam o céu. */
  @media (min-width: 641px) and (max-height: 699px) {
    #note:not([hidden]) {
      position: fixed;
      z-index: 5;
      left: 0;
      right: 0;
      bottom: var(--note-bottom, 65px);
      height: 52px;
      margin: 0;
      padding: 4px 24px;
      display: flex;
      flex-flow: row nowrap;
      align-items: center;
      gap: 16px;
      overflow: hidden;
      background: var(--color-bg);
      max-width: none;
    }
    #note:not([hidden]) #note-text {
      flex: 1 1 auto;
      min-width: 8rem;
      overflow-x: auto;
      overflow-y: hidden;
      text-overflow: clip;
      white-space: nowrap;
      line-height: 1.25;
      scrollbar-width: none;
    }
    #note:not([hidden]) #note-text::-webkit-scrollbar { height: 0; display: none; }
    #note:not([hidden]) #note-links {
      flex: 0 1 auto;
      max-width: 62%;
      min-width: 0;
      flex-wrap: nowrap;
      overflow-x: auto;
      scrollbar-width: none;
    }
    #note:not([hidden]) #note-links::-webkit-scrollbar { height: 0; display: none; }
    #note:not([hidden]) #note-links .k,
    #note:not([hidden]) #note-links .act { flex: none; }
    #note:not([hidden]) #note-links .act { overflow: hidden; text-overflow: ellipsis; }
    #note:not([hidden]) #note-links.has-more {
      mask-image: linear-gradient(90deg, transparent 0, transparent var(--link-clip-left, 0px), #000 var(--link-clip-left, 0px), #000 var(--link-clip, 100%), transparent var(--link-clip, 100%));
    }
    #permit:not([hidden]) {
      position: fixed;
      z-index: 6;
      left: 0;
      right: 0;
      bottom: var(--permit-bottom, 0px);
      height: var(--permit-height, 65px);
      margin: 0;
      padding: 0 24px;
      display: flex;
      flex-flow: row nowrap;
      align-items: center;
      gap: 16px;
      overflow: hidden;
      background: var(--color-bg);
      max-width: none;
    }
    #permit:not([hidden]) p { flex: none; }
    #permit:not([hidden]) #permit-cmd {
      flex: 1 1 0;
      min-width: 0;
      overflow-x: auto;
      overflow-y: hidden;
      text-overflow: clip;
      white-space: nowrap;
      scrollbar-width: none;
    }
    #permit:not([hidden]) #permit-cmd::-webkit-scrollbar { height: 0; display: none; }
    #permit:not([hidden]) .act { flex: none; min-width: 44px; }
  }
  @media (prefers-reduced-motion: reduce) { .act { transition: none; } }
  @media (max-width: 1399px) {
    .systems { flex-flow: row nowrap; overflow-x: auto; overflow-y: hidden; scrollbar-width: none; --clip: 100%; }
    .systems::-webkit-scrollbar { height: 0; display: none; }
    .systems.has-more {
      mask-image: linear-gradient(90deg, #000 0, #000 var(--clip), transparent var(--clip));
    }
  }
  @media (max-width: 640px) {
    .systems { flex-flow: row nowrap; overflow-x: auto; }
    .systems .band { display: contents; }
    .systems .fact[data-brain] { order: 9; }
    .systems .fact[data-brain][aria-pressed="true"] { order: 0; }
    .systems:not(:has(.fact[aria-pressed="true"])) .fact[data-brain] { order: 0; }
    .systems .fact:has(#notes) { order: 1; }
    .systems .fact:has(#date) { order: 2; }
    .systems .fact[data-voice] { order: 3; }
    .systems .fact[data-draft="anote "] { order: 4; }
    .systems .fact[data-draft="buscar nota "] { order: 5; }
    .systems .fact:has(#sky),
    .systems .fact[data-ask="qual o ritmo"],
    .systems .fact[data-ask="qual a carga"],
    .systems .fact[data-ask="qual o fuso"],
    .systems .fact[data-ask="qual seu nome"] { order: 8; }
    .systems .fact:has(#sky) { margin-left: 16px; }
  }
</style>
</head>
<body data-state="idle" data-name="__NAME__" data-load="0">
<canvas id="field" aria-label="constelação"></canvas>
<div class="room">
  <header class="strip">
    <h1><svg class="mark" viewBox="0 0 32 32" aria-hidden="true"><g fill="none" stroke="currentColor" stroke-linejoin="round"><path stroke-linecap="round" stroke-width="1.7" d="M22.5 3.4C8.8 7.4 7.4 12.2 9.4 16 7.4 19.8 8.8 24.6 22.5 28.6"/><path stroke-linecap="butt" stroke-width="1.1" d="M22.5 3.4Q20.6 16 22.5 28.6"/></g><g fill="currentColor"><path d="M12.7 18.7l.85.85-.85.85-.85-.85z"/><path d="M15 15.85l1.15 1.15L15 18.15l-1.15-1.15z"/><path d="M17.3 13.05l.85.85-.85.85-.85-.85z"/></g></svg>__NAME__</h1>
    <div class="meta">
      <p id="status">pronto</p>
      <p id="clock">00:00:00</p>
    </div>
  </header>
  <div class="well">
    <p id="sky-read" hidden>Arraste para orbitar. A roda aproxima.</p>
  </div>
  <aside class="telemetry">
    <div class="systems">
      <div class="band">
      <button type="button" class="fact" data-brain="codex"><span class="k">Codex</span><span class="v is-down" id="brain-codex">ausente</span></button>
      <button type="button" class="fact" data-brain="cursor"><span class="k">Cursor</span><span class="v is-down" id="brain-cursor">ausente</span></button>
      <button type="button" class="fact" data-brain="claude"><span class="k">Claude</span><span class="v is-down" id="brain-claude">ausente</span></button>
      <button type="button" class="fact" data-brain="ollama"><span class="k">Cérebro</span><span class="v is-down" id="brain">ausente</span></button>
      </div>
      <div class="band">
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
let pinnedSky = null;
let hovered = "";
let yawUser = 0;
let pitchUser = -0.3;
let yawTarget = 0;
let pitchTarget = -0.3;
let zoom = 1;
let drag = null;
let dragMoved = 0;
const orbitHint = "Arraste para orbitar. A roda aproxima.";
function readSky(text) {
  const line = text || "";
  skyRead.textContent = line;
  skyRead.hidden = line === "" || line === orbitHint;
}
const draftAsk = {
  "anote ": "O que devo anotar, Senhor?",
  "buscar nota ": "O que devo buscar nas notas, Senhor?",
};
function readSkyFit(line) {
  readSky(line);
  if (!line) {
    pinnedSky = "";
    return;
  }
  const shown = getComputedStyle(skyRead).display !== "none";
  ctx.font = getComputedStyle(skyRead).font;
  const wide = ctx.measureText(line).width > 480;
  const cut = shown && skyRead.scrollWidth > skyRead.clientWidth + 1;
  if (wide || cut) readSky("");
  pinnedSky = skyRead.hidden ? "" : skyRead.textContent;
}
function askSky(line) {
  pinnedSky = null;
  readSky(line);
  if (!line || line === orbitHint) return;
  if (getComputedStyle(skyRead).display !== "none") return;
  const last = logLines && logLines.querySelector("p:last-child");
  if (last && last.textContent === line) return;
  addLine("agent", line);
}
const GROUPS = {
  notas: { name: "Notas", rgb: "214, 78, 112", link: "255, 220, 226" },
  sistemas: { name: "Sistemas", rgb: "64, 112, 196", link: "186, 214, 242" },
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
  "sys-busca": "O que devo procurar, Senhor?",
  "sys-lembretes": "Notas deste céu.",
  "sys-voz": "Voz daniel, ritmo 1.2.",
};
const WIDE = 641;
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
  const wide = rect.width >= WIDE;
  if (wide) {
    const radiusPx = Math.max(84, Math.min(rect.height * 0.34, rect.width * 0.2, (rect.height - 72) / 2));
    const reach = Math.max(radiusPx * 0.85, rect.width / 2 - radiusPx - 56);
    const offset = Math.min(reach, radiusPx * 1.22);
    return {
      notas: Object.assign(at(-offset, 0), { radius: radiusPx * 1.18 / k, zScale: 0.85, name: GROUPS.notas.name, rgb: GROUPS.notas.rgb }),
      sistemas: Object.assign(at(offset, 0), { radius: radiusPx / k, name: GROUPS.sistemas.name, rgb: GROUPS.sistemas.rgb }),
    };
  }
  const radiusPx = Math.max(48, Math.min(rect.width * 0.32, rect.height * 0.2, (rect.width - 40) / 2));
  const reach = Math.max(radiusPx * 0.70, rect.height / 2 - radiusPx - 16);
  const offset = Math.min(rect.height * 0.26, reach);
  const up = rect.height < 280 ? offset * 0.45 : offset;
  return {
    notas: Object.assign(at(0, -up), { radius: radiusPx / k, zScale: 0.7, name: GROUPS.notas.name, rgb: GROUPS.notas.rgb }),
    sistemas: Object.assign(at(0, offset * 0.8), { radius: radiusPx * 0.72 / k, zScale: 0.42, name: GROUPS.sistemas.name, rgb: GROUPS.sistemas.rgb }),
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
  return ringPos(index, n, center, ring, 0.88);
}
function systemPos(star, center) {
  if (star.id === "sys-cerebro") return { x: center.x, y: center.y, z: center.z || 0 };
  const ringIds = INNER_RING.indexOf(star.id) >= 0 ? INNER_RING : OUTER_RING;
  const index = Math.max(0, ringIds.indexOf(star.id));
  const ring = (ringIds === INNER_RING ? 0.48 : 0.62) * center.radius;
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
        const push = Math.min(0.02, 0.012 / (dist * dist));
        a.x += dx / dist * push; a.y += dy / dist * push; a.z += dz / dist * push;
        b.x -= dx / dist * push; b.y -= dy / dist * push; b.z -= dz / dist * push;
      }
    }
    for (const pair of pairs) {
      const a = pair[0];
      const b = pair[1];
      a.x += (b.x - a.x) * 0.018; a.y += (b.y - a.y) * 0.018; a.z += (b.z - a.z) * 0.018;
      b.x += (a.x - b.x) * 0.018; b.y += (a.y - b.y) * 0.018; b.z += (a.z - b.z) * 0.018;
    }
    for (const node of nodes) {
      node.x += (node.hx - node.x) * 0.22;
      node.y += (node.hy - node.y) * 0.22;
      node.z += (node.hz - node.z) * 0.22;
      const limit = node.group === "nota" ? 0.82 : 0.9;
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
  const zScale = center.zScale == null ? 1 : center.zScale;
  return {
    x: center.x + local.x * center.radius,
    y: center.y + local.y * center.radius,
    z: (center.z || 0) + local.z * center.radius * DEPTH * zScale,
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
const nebulaCache = {};
function nebulaSprite(rgb, strong) {
  const key = strong ? rgb + ":s" : rgb;
  const cached = nebulaCache[key];
  if (cached) return cached;
  const S = 384;
  const sprite = document.createElement("canvas");
  sprite.width = S;
  sprite.height = S;
  const pen = sprite.getContext("2d");
  const mid = S / 2;
  const rad = mid - 1;
  pen.save();
  pen.beginPath();
  pen.arc(mid, mid, rad, 0, Math.PI * 2);
  pen.clip();
  pen.globalCompositeOperation = "lighter";
  const knot = (x, y, radius, peak, shoulder) => {
    const disc = pen.createRadialGradient(x, y, 0, x, y, radius);
    disc.addColorStop(0, "rgba(" + rgb + "," + peak + ")");
    disc.addColorStop(0.46, "rgba(" + rgb + "," + shoulder + ")");
    disc.addColorStop(1, "rgba(" + rgb + ",0)");
    pen.fillStyle = disc;
    pen.beginPath();
    pen.arc(x, y, radius, 0, Math.PI * 2);
    pen.fill();
  };
  knot(mid, mid, rad, strong ? "0.28" : "0.18", strong ? "0.12" : "0.07");
  knot(mid * 0.62, mid * 0.74, rad * 0.72, strong ? "0.46" : "0.30", strong ? "0.16" : "0.09");
  knot(mid * 1.28, mid * 1.16, rad * 0.58, strong ? "0.34" : "0.22", strong ? "0.12" : "0.07");
  knot(mid * 1.08, mid * 0.58, rad * 0.36, strong ? "0.40" : "0.26", strong ? "0.10" : "0.06");
  knot(mid, mid, rad * 0.18, strong ? "0.72" : "0.58", "0");
  pen.restore();
  nebulaCache[key] = sprite;
  return sprite;
}
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
function toneLum(r, g, b) {
  const f = (v) => {
    v /= 255;
    return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
  };
  return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
}
function paintLabel(text, x, y, halo) {
  if (halo) {
    ctx.lineJoin = "round";
    ctx.miterLimit = 2;
    ctx.lineWidth = 3;
    ctx.strokeStyle = ink.bg;
    ctx.strokeText(text, x, y);
  }
  ctx.fillText(text, x, y);
}
function labelBox(x, y, align, width) {
  const left = align === "right" ? x - width : align === "center" ? x - width / 2 : x;
  return { l: left - 4, r: left + width + 4, t: y - 9, b: y + 9 };
}
function boxesHit(a, b) {
  return !(a.r <= b.l || a.l >= b.r || a.b <= b.t || a.t >= b.b);
}
function segmentPieces(x1, y1, x2, y2, boxes) {
  let parts = [[0, 1]];
  const dx = x2 - x1;
  const dy = y2 - y1;
  const span = (a, b, delta, origin) => {
    if (Math.abs(delta) < 1e-6) return origin >= a && origin <= b ? [-Infinity, Infinity] : null;
    let t0 = (a - origin) / delta;
    let t1 = (b - origin) / delta;
    if (t0 > t1) { const swap = t0; t0 = t1; t1 = swap; }
    return [t0, t1];
  };
  for (const box of boxes) {
    const next = [];
    for (const part of parts) {
      const xs = span(box.l, box.r, dx, x1);
      const ys = span(box.t, box.b, dy, y1);
      if (!xs || !ys) { next.push(part); continue; }
      const hit0 = Math.max(part[0], xs[0], ys[0]);
      const hit1 = Math.min(part[1], xs[1], ys[1]);
      if (hit1 - hit0 < 0.002) { next.push(part); continue; }
      if (hit0 > part[0] + 0.002) next.push([part[0], hit0]);
      if (hit1 < part[1] - 0.002) next.push([hit1, part[1]]);
    }
    parts = next;
  }
  const pieces = [];
  for (const part of parts) {
    if (part[1] - part[0] < 0.02) continue;
    pieces.push({
      x1: x1 + dx * part[0], y1: y1 + dy * part[0],
      x2: x1 + dx * part[1], y2: y1 + dy * part[1],
    });
  }
  return pieces;
}
function boxHitsSegment(box, seg) {
  let x1 = seg.x1, y1 = seg.y1, x2 = seg.x2, y2 = seg.y2;
  const l = box.l, r = box.r, t = box.t, b = box.b;
  const code = (x, y) => (x < l ? 1 : x > r ? 2 : 0) | (y < t ? 4 : y > b ? 8 : 0);
  let c1 = code(x1, y1);
  let c2 = code(x2, y2);
  for (let n = 0; n < 8; n++) {
    if (!(c1 | c2)) return true;
    if (c1 & c2) return false;
    const c = c1 || c2;
    let x = x1;
    let y = y1;
    if (c & 8) {
      const dy = y2 - y1;
      if (!dy) return false;
      y = b;
      x = x1 + (x2 - x1) * (b - y1) / dy;
    } else if (c & 4) {
      const dy = y2 - y1;
      if (!dy) return false;
      y = t;
      x = x1 + (x2 - x1) * (t - y1) / dy;
    } else if (c & 2) {
      const dx = x2 - x1;
      if (!dx) return false;
      x = r;
      y = y1 + (y2 - y1) * (r - x1) / dx;
    } else {
      const dx = x2 - x1;
      if (!dx) return false;
      x = l;
      y = y1 + (y2 - y1) * (l - x1) / dx;
    }
    if (c === c1) { x1 = x; y1 = y; c1 = code(x1, y1); }
    else { x2 = x; y2 = y; c2 = code(x2, y2); }
  }
  return false;
}
let liftSeats = false;
let fineSeats = false;
function labelSpots(x, y, cx0, cy0) {
  const spots = [
    { x: x + 14, y, align: "left" },
    { x: x - 14, y, align: "right" },
    { x, y: y - 18, align: "center" },
    { x, y: y + 18, align: "center" },
    { x, y: y - 36, align: "center" },
    { x, y: y + 36, align: "center" },
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
  spots.push(
    { x: x + 26, y: y - 18, align: "center" },
    { x: x - 26, y: y - 18, align: "center" },
    { x: x + 44, y: y - 18, align: "center" },
    { x: x - 44, y: y - 18, align: "center" },
    { x: x + 26, y: y - 34, align: "center" },
    { x: x - 26, y: y - 34, align: "center" },
    { x: x + 44, y: y - 34, align: "center" },
    { x: x - 44, y: y - 34, align: "center" },
    { x: x + 30, y, align: "left" },
    { x: x - 30, y, align: "right" },
    { x: x + 46, y, align: "left" },
    { x: x - 46, y, align: "right" },
    { x: x + 12, y: y + 36, align: "center" },
    { x: x - 12, y: y + 36, align: "center" },
    { x: x + 12, y: y - 36, align: "center" },
    { x: x - 12, y: y - 36, align: "center" },
    { x, y: y - 50, align: "center" },
    { x, y: y + 50, align: "center" },
    { x: x + 52, y, align: "left" },
    { x: x - 52, y, align: "right" }
  );
  if (liftSeats) {
    spots.push(
      { x, y: y - 40, align: "center" },
      { x, y: y + 40, align: "center" },
      { x, y: y - 44, align: "center" },
      { x, y: y + 44, align: "center" }
    );
  }
  if (fineSeats) {
    for (const dy of [-40, -32, -24, 24, 32, 40]) {
      for (const dx of [-40, -24, -16, 0, 16, 24, 40]) {
        spots.push({ x: x + dx, y: y + dy, align: "center" });
        if (dx > 0) spots.push({ x: x + dx, y: y + dy, align: "right" });
        if (dx < 0) spots.push({ x: x + dx, y: y + dy, align: "left" });
      }
    }
  }
  return spots;
}
function paintDisc(center, tilt, rgb, yaw, pitch, cx, cy, scale, strong, reach) {
  const R = center.radius * reach;
  const lean = tilt;
  const origin = { x: center.x, y: center.y, z: center.z || 0 };
  const rimU = { x: origin.x + R, y: origin.y, z: origin.z };
  const rimV = {
    x: origin.x,
    y: origin.y + R * Math.cos(lean),
    z: origin.z + R * Math.sin(lean) * DEPTH,
  };
  const pc = project(rotate(origin, yaw, pitch), cx, cy, scale);
  const pu = project(rotate(rimU, yaw, pitch), cx, cy, scale);
  const pv = project(rotate(rimV, yaw, pitch), cx, cy, scale);
  ctx.save();
  ctx.setTransform(
    (pu.x - pc.x) * DPR, (pu.y - pc.y) * DPR,
    (pv.x - pc.x) * DPR, (pv.y - pc.y) * DPR,
    pc.x * DPR, pc.y * DPR
  );
  ctx.drawImage(nebulaSprite(rgb, strong), -1, -1, 2, 2);
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
  const cy = rect.top + rect.height * (rect.width >= WIDE ? 0.48 : 0.545);
  const fit = fitScene(rect);
  let scale = sceneScale(rect) * zoom;
  const yaw = yawUser;
  const pitch = pitchUser;
  const world = buildWorld(fit);
  const projectView = (amount) => world.all.map((node) => {
    const rot = rotate(node.pos, yaw, pitch);
    return { star: node.star, pos: node.pos, p: project(rot, cx, cy, amount) };
  }).sort((a, b) => b.p.z - a.p.z);
  let view = projectView(scale);
  if (rect.width < WIDE) {
    const padX = 12;
    const padTop = 14;
    const padBottom = 32;
    for (let step = 0; step < 3; step++) {
      let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
      for (const item of view) {
        minX = Math.min(minX, item.p.x);
        maxX = Math.max(maxX, item.p.x);
        minY = Math.min(minY, item.p.y);
        maxY = Math.max(maxY, item.p.y);
      }
      const overflow = Math.max(
        padTop - (minY - rect.top),
        padBottom - (rect.bottom - maxY),
        padX - (minX - rect.left),
        padX - (rect.right - maxX),
        0
      );
      if (overflow < 2) break;
      scale *= 0.92;
      view = projectView(scale);
    }
  }
  ctx.save();
  ctx.beginPath();
  ctx.rect(rect.left, rect.top, rect.width, rect.height);
  ctx.clip();
  const centroids = {};
  for (const key of ["nota", "sistema"]) {
    const pts = view.filter((item) => item.star.kind === key);
    if (!pts.length) continue;
    let sx = 0, sy = 0, sz = 0;
    for (const item of pts) { sx += item.p.x; sy += item.p.y; sz += item.p.z; }
    sx /= pts.length; sy /= pts.length; sz /= pts.length;
    let maxD = 0;
    for (const item of pts) maxD = Math.max(maxD, Math.hypot(item.p.x - sx, item.p.y - sy));
    const meta = key === "nota" ? fit.notas : fit.sistemas;
    centroids[key] = { x: sx, y: sy, z: sz, maxD, name: meta.name, rgb: meta.rgb };
  }
  const discs = [
    { center: fit.notas, tilt: 0.88, rgb: GROUPS.notas.rgb, strong: true },
    { center: fit.sistemas, tilt: 0.9, rgb: GROUPS.sistemas.rgb, strong: false },
  ].map((disc) => {
    const rot = rotate(disc.center, yaw, pitch);
    return { disc, z: rot.z };
  }).sort((a, b) => b.z - a.z);
  const reachFor = (item) => {
    if (rect.width >= WIDE) return item.disc.strong ? 1.32 : 1.25;
    const base = 1.08;
    return item.disc.strong ? base * 1.18 : base * 1.48;
  };
  ctx.save();
  ctx.globalCompositeOperation = "lighter";
  for (const item of discs) {
    const reach = reachFor(item);
    const center = item.disc.center;
    const far = Object.assign({}, center, { z: (center.z || 0) + center.radius * 0.42 });
    ctx.globalAlpha = 0.5;
    paintDisc(far, item.disc.tilt, item.disc.rgb, yaw, pitch, cx, cy, scale, false, reach * 0.7);
    const quietNotes = item.disc.strong && rect.width < WIDE && rect.height >= 448 && rect.height <= 516;
    ctx.globalAlpha = quietNotes ? 0.86 : 0.88;
    paintDisc(center, item.disc.tilt, item.disc.rgb, yaw, pitch, cx, cy, scale, item.disc.strong, reach);
    const lean = item.disc.tilt;
    const zScale = center.zScale == null ? 1 : center.zScale;
    const narrow = rect.width < WIDE;
    const forward = item.disc.strong ? (narrow ? 1.15 : 0.9) : 0.8;
    const lobe = item.disc.strong ? (narrow ? 1.15 : 0.78) : (narrow ? 0.72 : 0.74);
    const near = Object.assign({}, center, {
      z: (center.z || 0) - Math.sin(lean) * center.radius * DEPTH * zScale * forward,
    });
    // O lóbulo dos sistemas clareia "Cérebro" entre 768 e 870.
    const calmSystems = !item.disc.strong && rect.width >= 768 && rect.width <= 800;
    const midSystems = !item.disc.strong && rect.width > 800 && rect.width <= 870;
    const sysLobe = calmSystems ? 0.56 : midSystems ? 0.28 : 0.75;
    ctx.globalAlpha = quietNotes ? 0.36 : (item.disc.strong ? 0.62 : sysLobe);
    paintDisc(near, lean, item.disc.rgb, yaw, pitch, cx, cy, scale, true, lobe);
  }
  ctx.restore();
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
  const segments = [];
  const strokes = [];
  ctx.lineCap = "round";
  for (const pair of world.links) {
    const a = byId[pair[0].star.id];
    const b = byId[pair[1].star.id];
    if (!a || !b) continue;
    const hot = picked && (a.star.id === picked || b.star.id === picked);
    const aside = focusId && !neigh.has(a.star.id) && !neigh.has(b.star.id);
    const missed = (star) => star.kind === "nota" && noteQuery && !noteHit(star);
    const quietLink = missed(a.star) || missed(b.star);
    const dx = b.p.x - a.p.x;
    const dy = b.p.y - a.p.y;
    const len = Math.hypot(dx, dy) || 1;
    const pad = 10;
    if (len < pad * 2 + 4) continue;
    const ux = dx / len;
    const uy = dy / len;
    const depth = Math.max(0.45, Math.min(1, ((a.p.persp + b.p.persp) / 2) / 0.62));
    const tone = a.star.kind === b.star.kind
      ? "rgb(" + (a.star.kind === "nota" ? GROUPS.notas.link : GROUPS.sistemas.link) + ")"
      : "rgb(232, 220, 196)";
    const alpha = (hot ? 1 : aside ? 0.45 : 1) * depth * (quietLink ? 0.16 : 1);
    const x1 = a.p.x + ux * pad;
    const y1 = a.p.y + uy * pad;
    const x2 = b.p.x - ux * pad;
    const y2 = b.p.y - uy * pad;
    segments.push({ x1, y1, x2, y2 });
    strokes.push({ x1, y1, x2, y2, hot, alpha, depth, tone });
  }
  ctx.setLineDash([]);
  namedOnScreen = [];
  for (const item of view) {
    const inside = item.p.x >= rect.left + 4 && item.p.x <= rect.right - 4 && item.p.y >= rect.top + 8 && item.p.y <= rect.bottom - 28;
    const chosen = item.star.id === picked;
    const near = item.p.persp;
    const depthScale = Math.max(0.55, Math.min(1.45, near / (FOCAL / CAMERA)));
    const pulse = chosen ? 1 + level * 0.65 : 1;
    const dim = item.star.kind === "nota" && noteQuery && !noteHit(item.star);
    const aside = focusId && !neigh.has(item.star.id);
    const rgb = chosen ? "212, 196, 168" : item.star.kind === "nota" ? GROUPS.notas.rgb : GROUPS.sistemas.rgb;
    const presence = (dim ? 0.16 : aside ? 0.55 : 1) * Math.max(0.42, Math.min(1, depthScale));
    const size = (item.star.kind === "sistema" ? 40 : 32) * depthScale * pulse;
    ctx.save();
    ctx.globalCompositeOperation = "lighter";
    ctx.globalAlpha = presence * 0.72;
    ctx.drawImage(glowSprite(rgb), item.p.x - size / 2, item.p.y - size / 2, size, size);
    ctx.restore();
    const point = (item.star.kind === "sistema" ? 2.15 : 1.85) * depthScale * pulse;
    ctx.globalAlpha = presence;
    ctx.fillStyle = chosen ? ink.accent : ink.ink;
    ctx.beginPath();
    ctx.arc(item.p.x, item.p.y, point, 0, Math.PI * 2);
    ctx.fill();
    namedOnScreen.push({
      star: item.star, pos: item.pos, x: item.p.x, y: item.p.y,
      outside: inside, align: "left", lx: item.p.x + 12, ly: item.p.y, labelW: 0,
    });
  }
  const plateX = Math.max(0, Math.floor(rect.left * DPR));
  const plateY = Math.max(0, Math.floor(rect.top * DPR));
  const plateW = Math.min(canvas.width - plateX, Math.floor(rect.width * DPR));
  const plateH = Math.min(canvas.height - plateY, Math.floor(rect.height * DPR));
  const plate = plateW > 0 && plateH > 0 ? ctx.getImageData(plateX, plateY, plateW, plateH).data : null;
  const toneAt = (x, y, kind) => {
    if (!plate) return 0;
    const px = Math.floor(x * DPR) - plateX;
    const py = Math.floor(y * DPR) - plateY;
    if (px < 0 || py < 0 || px >= plateW || py >= plateH) return 0;
    const i = (py * plateW + px) * 4;
    const r = plate[i], g = plate[i + 1], b = plate[i + 2];
    if (kind === "nota") return r > 40 && r > g + 18 && r > b + 8 && r < 190 && g < 140 ? 1 : 0;
    return b > 40 && b > r + 18 && g > r + 4 && r < 150 && b < 210 ? 1 : 0;
  };
  const boxes = [];
  const paints = [];
  ctx.textBaseline = "middle";
  ctx.font = "400 14px " + ink.body;
  const eligible = (item) => {
    if (!item.star.label) return false;
    if (item.star.kind === "nota" && noteQuery && !noteHit(item.star) && item.star.id !== picked) return false;
    const focus = item.star.id === picked || item.star.id === hovered;
    if (item.p.persp < 0.42 && !focus) return false;
    const onStage = item.p.x >= rect.left + 8 && item.p.x <= rect.right - 8 && item.p.y >= rect.top + 12 && item.p.y <= rect.bottom - 36;
    return onStage || item.star.id === picked;
  };
  const candidatesFor = (item, held) => {
    const full = item.star.label;
    const width = ctx.measureText(full).width;
    const home = centroids[item.star.kind];
    const options = labelSpots(item.p.x, item.p.y, home && home.x, home && home.y);
    const fits = (trial) => trial.l >= rect.left + 4 && trial.r <= rect.right - 4 && trial.t >= rect.top + 4 && trial.b <= rect.bottom - 28 && !held.some((box) => boxesHit(trial, box));
    const crosses = (trial) => segments.some((seg) => boxHitsSegment(trial, seg));
    const intrusion = (trial) => {
      let worst = 0;
      for (const other of view) {
        if (other.star.id === item.star.id) continue;
        const dx = other.p.x < trial.l ? trial.l - other.p.x : other.p.x > trial.r ? other.p.x - trial.r : 0;
        const dy = other.p.y < trial.t ? trial.t - other.p.y : other.p.y > trial.b ? other.p.y - trial.b : 0;
        if (dx === 0 && dy === 0) {
          const inset = Math.min(other.p.x - trial.l, trial.r - other.p.x, other.p.y - trial.t, trial.b - other.p.y);
          worst = Math.max(worst, 32 + inset);
        } else if (dx * dx + dy * dy < 64) {
          worst = Math.max(worst, 8 - Math.hypot(dx, dy));
        }
      }
      return worst;
    };
    const consider = [];
    const pushOpt = (opt, trial, wrapped) => {
      if (!fits(trial)) return;
      const mx = (trial.l + trial.r) / 2;
      const my = (trial.t + trial.b) / 2;
      const nest = home ? Math.hypot(mx - home.x, my - home.y) : 0;
      const outside = home && nest > home.maxD ? 1 : 0;
      let tone = 0;
      let seen = 0;
      let worst = plate ? 99 : 8;
      const fillLum = toneLum(232, 238, 246);
      const stepY = fineSeats ? 2 : 4;
      const stepX = fineSeats ? 2 : 6;
      for (let y = trial.t + 2; y <= trial.b - 2; y += stepY) {
        for (let x = trial.l + 2; x <= trial.r - 2; x += stepX) {
          seen++;
          tone += toneAt(x, y, item.star.kind);
          if (!plate) continue;
          const px = Math.floor(x * DPR) - plateX;
          const py = Math.floor(y * DPR) - plateY;
          if (px < 0 || py < 0 || px >= plateW || py >= plateH) continue;
          const i = (py * plateW + px) * 4;
          const lum = toneLum(plate[i], plate[i + 1], plate[i + 2]);
          const hi = Math.max(fillLum, lum);
          const lo = Math.min(fillLum, lum);
          worst = Math.min(worst, (hi + 0.05) / (lo + 0.05));
        }
      }
      const share = seen ? tone / seen : 0;
      const self = item.p.x >= trial.l && item.p.x <= trial.r && item.p.y >= trial.t && item.p.y <= trial.b ? 1 : 0;
      consider.push({ opt, trial, wrapped, cross: crosses(trial), intrusion: intrusion(trial), outside, share, contrast: worst, self });
    };
    for (const opt of options) pushOpt(opt, labelBox(opt.x, opt.y, opt.align, width), null);
    if (full.indexOf(" ") > 0) {
      const words = full.split(" ");
      let best = null;
      let bestW = Infinity;
      for (let cut = 1; cut < words.length; cut++) {
        const pair = [words.slice(0, cut).join(" "), words.slice(cut).join(" ")];
        const lineW = Math.max(ctx.measureText(pair[0]).width, ctx.measureText(pair[1]).width);
        if (lineW < bestW) { bestW = lineW; best = pair; }
      }
      for (const opt of options) {
        const trial = labelBox(opt.x, opt.y, opt.align, bestW);
        trial.t -= 8;
        trial.b += 8;
        pushOpt(opt, trial, best);
      }
    }
    const pool = consider.filter((spot) => spot.intrusion < 32);
    pool.sort((a, b) => {
      const hard = (spot) => spot.intrusion >= 16 ? 1 : 0;
      if (hard(a) !== hard(b)) return hard(a) - hard(b);
      if (a.self !== b.self) {
        const clear = a.self ? b : a;
        if (clear.share >= 0.8 && clear.intrusion < 16) return a.self - b.self;
      }
      if (Math.abs(a.share - b.share) >= 0.08) return b.share - a.share;
      if (a.intrusion !== b.intrusion) return a.intrusion - b.intrusion;
      if (a.share >= 0.85 && b.share >= 0.85 && (a.contrast < 4.5) !== (b.contrast < 4.5)) {
        return (a.contrast < 4.5 ? 1 : 0) - (b.contrast < 4.5 ? 1 : 0);
      }
      return (a.self - b.self) || (a.cross - b.cross) || (a.outside - b.outside) || ((a.wrapped ? 1 : 0) - (b.wrapped ? 1 : 0));
    });
    return { pool, options, width, full };
  };
  const queue = view.filter(eligible);
  const distOf = (item) => {
    const home = centroids[item.star.kind];
    return home ? Math.hypot(item.p.x - home.x, item.p.y - home.y) : 0;
  };
  const byFocus = (a, b) => {
    const af = a.star.id === picked || a.star.id === hovered;
    const bf = b.star.id === picked || b.star.id === hovered;
    if (af !== bf) return af ? -1 : 1;
    return 0;
  };
  const readable = (item) => {
    let best = 0;
    for (const spot of candidatesFor(item, []).pool) {
      if (spot.share < 0.8 || spot.intrusion >= 16 || spot.self) continue;
      if (spot.contrast > best) best = spot.contrast;
    }
    return best;
  };
  queue.sort((a, b) => {
    const focus = byFocus(a, b);
    if (focus) return focus;
    const rank = { nota: 0, sistema: 1 };
    const kind = (rank[a.star.kind] || 3) - (rank[b.star.kind] || 3);
    if (kind) return kind;
    if (rect.width < WIDE) return readable(a) - readable(b) || (b.p.persp - a.p.persp);
    const nearerFirst = a.star.kind === "sistema";
    return (nearerFirst ? distOf(a) - distOf(b) : distOf(b) - distOf(a)) || (b.p.persp - a.p.persp);
  });
  const paintOne = (item, held) => {
    const focus = item.star.id === picked || item.star.id === hovered;
    const quiet = focusId && !neigh.has(item.star.id) && !focus;
    const seated = candidatesFor(item, held);
    const { options, width, full } = seated;
    let chosen = seated.pool[0] || null;
    if (!chosen && item.star.id === picked) {
      const opt = options[0];
      chosen = { opt, trial: labelBox(opt.x, opt.y, opt.align, width), wrapped: null };
    }
    if (!chosen) return;
    const spot = chosen.opt;
    const box = chosen.trial;
    const lines = chosen.wrapped;
    boxes.push(box);
    const row = namedOnScreen.find((entry) => entry.star.id === item.star.id);
    if (row) {
      row.align = spot.align;
      row.lx = spot.x;
      row.ly = spot.y;
      row.labelW = lines ? Math.max(ctx.measureText(lines[0]).width, ctx.measureText(lines[1]).width) : width;
    }
    const fill = item.star.id === picked ? ink.accent : ink.ink;
    const fillLum = fill === ink.accent ? toneLum(212, 196, 168) : toneLum(232, 238, 246);
    let worst = plate ? 99 : 8;
    if (plate) {
      for (let y = box.t + 1; y <= box.b - 1; y += 3) {
        for (let x = box.l + 1; x <= box.r - 1; x += 4) {
          const px = Math.floor(x * DPR) - plateX;
          const py = Math.floor(y * DPR) - plateY;
          if (px < 0 || py < 0 || px >= plateW || py >= plateH) continue;
          const i = (py * plateW + px) * 4;
          const lum = toneLum(plate[i], plate[i + 1], plate[i + 2]);
          const hi = Math.max(fillLum, lum);
          const lo = Math.min(fillLum, lum);
          worst = Math.min(worst, (hi + 0.05) / (lo + 0.05));
        }
      }
    }
    paints.push({
      item, box, contrast: worst, lines, full, spot, halo: worst < 4.5,
      alpha: item.star.id === picked ? 1 : quiet ? 0.66 : 0.92,
      fill,
      font: "400 14px " + ink.body,
    });
  };
  const notes = queue.filter((item) => item.star.kind !== "sistema");
  const systems = queue.filter((item) => item.star.kind === "sistema");
  for (const item of notes) paintOne(item, boxes);
  let kept = null;
  if (rect.width < WIDE) {
    const busca = systems.find((item) => item.star.id === "sys-busca");
    const seated = busca && candidatesFor(busca, boxes);
    const best = seated && seated.pool[0];
    if (best && best.share >= 0.85 && best.intrusion < 8) kept = best.trial;
  }
  for (const item of systems) {
    const held = kept && item.star.id !== "sys-busca" ? boxes.concat([kept]) : boxes;
    paintOne(item, held);
  }
  const usable = (spot) => spot.contrast >= 4.5 && spot.share >= 0.8 && spot.intrusion < 16 && !spot.self;
  const applySeat = (paint, chosen) => {
    const spot = chosen.opt;
    const box = chosen.trial;
    const lines = chosen.wrapped;
    const index = boxes.indexOf(paint.box);
    if (index >= 0) boxes[index] = box;
    paint.box = box;
    paint.spot = spot;
    paint.lines = lines;
    paint.contrast = chosen.contrast;
    paint.halo = chosen.contrast < 4.5;
    const row = namedOnScreen.find((entry) => entry.star.id === paint.item.star.id);
    if (!row) return;
    row.align = spot.align;
    row.lx = spot.x;
    row.ly = spot.y;
    row.labelW = lines ? Math.max(ctx.measureText(lines[0]).width, ctx.measureText(lines[1]).width) : ctx.measureText(paint.full).width;
  };
  if (rect.width < WIDE) {
    for (const paint of paints.filter((entry) => entry.contrast < 4.5)) {
      const rest = boxes.filter((box) => box !== paint.box);
      const direct = candidatesFor(paint.item, rest).pool.find(usable);
      if (direct) { applySeat(paint, direct); continue; }
      const open = candidatesFor(paint.item, []).pool.filter(usable);
      for (const spot of open) {
        const blockers = paints.filter((other) => other !== paint && boxesHit(spot.trial, other.box));
        if (blockers.length !== 1) continue;
        const blocker = blockers[0];
        const held = boxes.filter((box) => box !== paint.box && box !== blocker.box).concat([spot.trial]);
        const next = candidatesFor(blocker.item, held).pool.find(usable);
        if (!next) continue;
        applySeat(paint, spot);
        applySeat(blocker, next);
        break;
      }
    }
    const nearerGuest = (box, item, other) => {
      const x = (box.l + box.r) / 2;
      const y = (box.t + box.b) / 2;
      const guest = Math.hypot(item.p.x - x, item.p.y - y);
      const own = Math.hypot(other.p.x - x, other.p.y - y);
      return guest + 8 < own;
    };
    const seatFresh = (item, chosen) => {
      const spot = chosen.opt;
      const box = chosen.trial;
      const lines = chosen.wrapped;
      boxes.push(box);
      const row = namedOnScreen.find((entry) => entry.star.id === item.star.id);
      if (row) {
        row.align = spot.align;
        row.lx = spot.x;
        row.ly = spot.y;
        row.labelW = lines ? Math.max(ctx.measureText(lines[0]).width, ctx.measureText(lines[1]).width) : ctx.measureText(item.star.label).width;
      }
      paints.push({
        item, box, contrast: chosen.contrast, lines, full: item.star.label, spot,
        halo: chosen.contrast < 4.5, alpha: 0.92, fill: ink.ink, font: "400 14px " + ink.body,
      });
    };
    const holeOf = (box, kind) => {
      let hole = 0;
      let seen = 0;
      for (let y = box.t + 2; y <= box.b - 2; y += 4) {
        for (let x = box.l + 2; x <= box.r - 2; x += 4) {
          if (!plate) return 0;
          const px = Math.floor(x * DPR) - plateX;
          const py = Math.floor(y * DPR) - plateY;
          if (px < 0 || py < 0 || px >= plateW || py >= plateH) continue;
          const i = (py * plateW + px) * 4;
          seen++;
          if (!toneAt(x, y, kind) && plate[i] + plate[i + 1] + plate[i + 2] < 80) hole++;
        }
      }
      return seen ? hole / seen : 0;
    };
    const needs = view.filter((item) => {
      if (!eligible(item)) return false;
      const paint = paints.find((entry) => entry.item.star.id === item.star.id);
      return !paint || holeOf(paint.box, item.star.kind) > 0.35;
    });
    const claimed = new Set();
    for (const item of needs) {
      if (claimed.has(item.star.id)) continue;
      const open = candidatesFor(item, []).pool.filter(usable);
      for (const spot of open) {
        const blockers = paints.filter((other) => other.item.star.id !== item.star.id && boxesHit(spot.trial, other.box));
        if (blockers.length !== 1) continue;
        const blocker = blockers[0];
        if (claimed.has(blocker.item.star.id)) continue;
        if (blocker.item.star.kind !== item.star.kind) continue;
        if (!nearerGuest(spot.trial, item, blocker.item) || !nearerGuest(blocker.box, item, blocker.item)) continue;
        const parkedX = (blocker.box.l + blocker.box.r) / 2;
        const parkedY = (blocker.box.t + blocker.box.b) / 2;
        if (Math.hypot(item.p.x - parkedX, item.p.y - parkedY) > 16) continue;
        const held = boxes.filter((box) => box !== blocker.box).concat([spot.trial]);
        const ownsSeat = (chosen, owner) => {
          const box = chosen.trial;
          const x = (box.l + box.r) / 2;
          const y = (box.t + box.b) / 2;
          const own = Math.hypot(owner.p.x - x, owner.p.y - y);
          let other = Infinity;
          for (const node of view) {
            if (node.star.id === owner.star.id) continue;
            other = Math.min(other, Math.hypot(node.p.x - x, node.p.y - y));
          }
          return own <= other + 8;
        };
        const next = candidatesFor(blocker.item, held).pool.find((chosen) => usable(chosen) && ownsSeat(chosen, blocker.item));
        if (next) applySeat(blocker, next);
        else {
          const index = boxes.indexOf(blocker.box);
          if (index >= 0) boxes.splice(index, 1);
          const paintIndex = paints.indexOf(blocker);
          if (paintIndex >= 0) paints.splice(paintIndex, 1);
          const row = namedOnScreen.find((entry) => entry.star.id === blocker.item.star.id);
          if (row) row.labelW = 0;
        }
        const existing = paints.find((entry) => entry.item.star.id === item.star.id);
        if (existing) applySeat(existing, spot);
        else seatFresh(item, spot);
        claimed.add(item.star.id);
        claimed.add(blocker.item.star.id);
        break;
      }
    }
    const coverOf = (box, kind) => {
      let tone = 0;
      let hole = 0;
      let seen = 0;
      let worst = 99;
      const fillLum = toneLum(232, 238, 246);
      for (let y = box.t + 2; y <= box.b - 2; y += 2) {
        for (let x = box.l + 2; x <= box.r - 2; x += 2) {
          if (!plate) return { tone: 0, hole: 1, contrast: 1 };
          const px = Math.floor(x * DPR) - plateX;
          const py = Math.floor(y * DPR) - plateY;
          if (px < 0 || py < 0 || px >= plateW || py >= plateH) continue;
          const i = (py * plateW + px) * 4;
          const r = plate[i];
          const g = plate[i + 1];
          const b = plate[i + 2];
          seen++;
          if (toneAt(x, y, kind)) tone++;
          else if (r + g + b < 80) hole++;
          const lum = toneLum(r, g, b);
          const hi = Math.max(fillLum, lum);
          const lo = Math.min(fillLum, lum);
          worst = Math.min(worst, (hi + 0.05) / (lo + 0.05));
        }
      }
      return {
        tone: seen ? tone / seen : 0,
        hole: seen ? hole / seen : 1,
        contrast: worst,
      };
    };
    const owned = (spot, item) => {
      const box = spot.trial;
      const x = (box.l + box.r) / 2;
      const y = (box.t + box.b) / 2;
      const own = Math.hypot(item.p.x - x, item.p.y - y);
      let other = Infinity;
      for (const node of view) {
        if (node.star.id === item.star.id) continue;
        other = Math.min(other, Math.hypot(node.p.x - x, node.p.y - y));
      }
      return own <= 48 && own + 8 < other;
    };
    fineSeats = true;
    try {
      const failing = paints.filter((paint) => {
        const cover = coverOf(paint.box, paint.item.star.kind);
        return cover.contrast < 4.5 || cover.tone < 0.8 || cover.hole > 0.2;
      });
      failing.sort((a, b) => coverOf(a.box, a.item.star.kind).tone - coverOf(b.box, b.item.star.kind).tone);
      for (const paint of failing) {
        const rest = boxes.filter((box) => box !== paint.box);
        const pool = candidatesFor(paint.item, rest).pool.filter((spot) => {
          if (spot.contrast < 4.5 || spot.share < 0.78 || spot.intrusion >= 16 || spot.self) return false;
          if (!owned(spot, paint.item)) return false;
          const cover = coverOf(spot.trial, paint.item.star.kind);
          return cover.hole <= 0.2 && cover.tone >= 0.78 && cover.contrast >= 4.5;
        });
        pool.sort((a, b) => {
          const dist = (spot) => Math.hypot(paint.item.p.x - (spot.trial.l + spot.trial.r) / 2, paint.item.p.y - (spot.trial.t + spot.trial.b) / 2);
          return (b.share - a.share) || (b.contrast - a.contrast) || (dist(a) - dist(b));
        });
        if (pool[0]) applySeat(paint, pool[0]);
      }
    } finally {
      fineSeats = false;
    }
  }
  if (rect.width >= WIDE) {
    liftSeats = true;
    try {
      for (const paint of paints.filter((entry) => entry.contrast < 4.5)) {
        const rest = boxes.filter((box) => box !== paint.box);
        const pool = candidatesFor(paint.item, rest).pool.filter((spot) => {
          if (!usable(spot)) return false;
          const box = spot.trial;
          const x = (box.l + box.r) / 2;
          const y = (box.t + box.b) / 2;
          const own = Math.hypot(paint.item.p.x - x, paint.item.p.y - y);
          let other = Infinity;
          for (const node of view) {
            if (node.star.id === paint.item.star.id) continue;
            other = Math.min(other, Math.hypot(node.p.x - x, node.p.y - y));
          }
          return own + 8 < other && spot.contrast > paint.contrast + 0.2;
        });
        pool.sort((a, b) => b.contrast - a.contrast);
        if (pool[0]) applySeat(paint, pool[0]);
      }
    } finally {
      liftSeats = false;
    }
  }
  ctx.lineCap = "round";
  for (const stroke of strokes) {
    const gaps = boxes.map((box) => ({ l: box.l - 4, r: box.r + 4, t: box.t - 4, b: box.b + 4 }));
    const pieces = segmentPieces(stroke.x1, stroke.y1, stroke.x2, stroke.y2, gaps);
    ctx.setLineDash(stroke.hot ? [5, 6] : [8, 10]);
    for (const piece of pieces) {
      ctx.beginPath();
      ctx.moveTo(piece.x1, piece.y1);
      ctx.lineTo(piece.x2, piece.y2);
      ctx.globalAlpha = stroke.alpha * 0.85;
      ctx.strokeStyle = "rgb(7, 13, 22)";
      ctx.lineWidth = (stroke.hot ? 2.2 : 1.9) * stroke.depth + 2.6;
      ctx.stroke();
      ctx.save();
      ctx.globalCompositeOperation = "lighter";
      ctx.globalAlpha = Math.min(1, stroke.alpha);
      ctx.strokeStyle = stroke.hot ? ink.accent : stroke.tone;
      ctx.lineWidth = (stroke.hot ? 2.4 : 2.1) * stroke.depth;
      ctx.stroke();
      ctx.restore();
    }
  }
  ctx.setLineDash([]);
  const contrastOf = (box, lumFill) => {
    let score = 99;
    if (!plate) return score;
    for (let y = box.t + 2; y <= box.b - 2; y += 2) {
      for (let x = box.l + 2; x <= box.r - 2; x += 2) {
        const px = Math.floor(x * DPR) - plateX;
        const py = Math.floor(y * DPR) - plateY;
        if (px < 0 || py < 0 || px >= plateW || py >= plateH) continue;
        const i = (py * plateW + px) * 4;
        const lum = toneLum(plate[i], plate[i + 1], plate[i + 2]);
        const hi = Math.max(lumFill, lum);
        const lo = Math.min(lumFill, lum);
        score = Math.min(score, (hi + 0.05) / (lo + 0.05));
      }
    }
    return score;
  };
  const inkLum = toneLum(232, 238, 246);
  const whiteLum = toneLum(255, 255, 255);
  for (const paint of paints) {
    if (paint.fill !== ink.ink) continue;
    const dense = contrastOf(paint.box, inkLum);
    if (dense >= 4.5) continue;
    const lifted = contrastOf(paint.box, whiteLum);
    if (lifted < 4.5) continue;
    paint.fill = "#ffffff";
    paint.alpha = 1;
    paint.halo = false;
  }
  for (const paint of paints) {
    ctx.font = paint.font;
    ctx.globalAlpha = paint.alpha;
    ctx.fillStyle = paint.fill;
    ctx.textAlign = paint.spot.align;
    if (paint.lines) {
      paintLabel(paint.lines[0], paint.spot.x, paint.spot.y - 8, paint.halo);
      paintLabel(paint.lines[1], paint.spot.x, paint.spot.y + 8, paint.halo);
    } else {
      paintLabel(paint.full, paint.spot.x, paint.spot.y, paint.halo);
    }
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
    if (width > 8 && bestD > 8 && Math.abs(y - (item.ly || item.y)) <= 16) {
      const left = item.align === "center" ? item.lx - width / 2 : item.align === "right" ? item.lx - width : item.lx;
      if (x >= left - 4 && x <= left + width + 4) { best = item; bestD = 12; }
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
function settleLog() {
  seatLog();
  if (!logEl || !logLines) return;
  const paras = [...logLines.querySelectorAll("p")];
  if (!paras.length) return;
  const line = parseFloat(getComputedStyle(paras[0]).lineHeight);
  if (!line) return;
  logLines.style.paddingBottom = "0px";
  logEl.style.maxHeight = "";
  logEl.scrollLeft = 0;
  logEl.scrollTop = logEl.scrollHeight;
  const box = logEl.getBoundingClientRect();
  let drop = 0;
  let align = 0;
  for (let i = 0; i < paras.length; i++) {
    const r = paras[i].getBoundingClientRect();
    if (r.top >= box.top - 0.5 || r.bottom <= box.top + 0.5) continue;
    const visible = r.bottom - box.top;
    const later = i < paras.length - 1;
    if (later && visible + 1 < logEl.clientHeight) drop = visible;
    else {
      const phase = (box.top - r.top) % line;
      if (phase > 0.75 && phase < line - 0.75) align = line - phase;
    }
    break;
  }
  if (drop > 0 && logEl.clientHeight - drop >= line) {
    logEl.style.maxHeight = Math.floor(logEl.clientHeight - drop) + "px";
    logEl.scrollTop = logEl.scrollHeight;
  } else if (align > 0 && line + align <= logEl.clientHeight) {
    logLines.style.paddingBottom = align + "px";
    logEl.scrollTop = logEl.scrollHeight;
  }
}
function addLine(cls, message) {
  if (emptyEl) emptyEl.remove();
  const p = document.createElement("p");
  p.className = cls;
  p.textContent = message;
  if (cls === "user") p.dataset.speaker = "Senhor";
  if (cls === "agent") p.dataset.speaker = "Orion";
  (logLines || logEl).appendChild(p);
  requestAnimationFrame(() => { settleLog(); wake(); });
}
function showPermit(id, command) {
  permitId = id || "";
  permitCmd.textContent = command || "";
  permitEl.hidden = !permitId;
  seatPermit();
  wake();
  requestAnimationFrame(() => { seatNote(); seatLog(); seatPermit(); settleLog(); });
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
    revealChoice();
    if (pinnedSky === null && picked && String(picked).indexOf("sys-") === 0) {
      readSky(systemText[picked] || skyRead.textContent);
    }
    await refreshSky();
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
  const ids = [];
  const seen = new Set();
  const push = (other) => {
    if (!other || other === id || seen.has(other)) return;
    seen.add(other);
    ids.push(other);
  };
  for (const link of memoryLinks) {
    if (link.a === id) push(link.b);
    if (link.b === id) push(link.a);
  }
  for (const link of SYSTEM_LINKS) {
    if (link[0] === id) push(link[1]);
    if (link[1] === id) push(link[0]);
  }
  if (memory.length > 0 && memory.length <= 12 && memory.some((star) => star.id === id)) push("sys-lembretes");
  return ids.map((other) => {
    const note = memory.find((star) => star.id === other);
    if (note) return { id: other, label: note.label, kind: "nota" };
    const system = SYSTEMS.find((star) => star.id === other);
    if (system) return { id: other, label: system.label, kind: "sistema" };
    return null;
  }).filter(Boolean);
}
function seatNote() {
  const tel = document.querySelector(".telemetry");
  if (!tel) return;
  const lift = Math.round(window.innerHeight - tel.getBoundingClientRect().bottom);
  document.documentElement.style.setProperty("--note-bottom", lift + "px");
}
function seatLog() {
  const sky = document.querySelector(".well");
  if (!sky) return;
  const lift = Math.round(window.innerHeight - sky.getBoundingClientRect().bottom);
  document.documentElement.style.setProperty("--log-bottom", lift + "px");
}
function seatPermit() {
  const floor = document.querySelector(".floor");
  if (!floor) return;
  const box = floor.getBoundingClientRect();
  const root = document.documentElement.style;
  root.setProperty("--permit-bottom", Math.round(window.innerHeight - box.bottom) + "px");
  root.setProperty("--permit-height", Math.max(44, Math.round(box.height)) + "px");
}
function closeNote() {
  if (!noteEl || noteEl.hidden) return;
  noteEl.hidden = true;
  noteText.textContent = "";
  noteLinks.replaceChildren();
  requestAnimationFrame(settleLog);
}
function openNote(star) {
  if (!noteEl) return;
  seatNote();
  noteEl.hidden = false;
  noteText.textContent = star.text || star.label;
  noteLinks.replaceChildren();
  const linked = linksOf(star.id);
  if (linked.length) {
    const cap = document.createElement("span");
    cap.className = "k";
    cap.textContent = "ligada a";
    noteLinks.appendChild(cap);
  }
  for (const other of linked) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "act";
    btn.textContent = other.label;
    btn.addEventListener("click", () => {
      if (other.kind === "nota") { focusStar(other.id); return; }
      const hit = namedOnScreen.find((item) => item.star.id === other.id);
      if (hit) focusStarItem(hit, true);
    });
    noteLinks.appendChild(btn);
  }
  requestAnimationFrame(() => { settleLog(); seatLinks(); });
}
function seatLinks() {
  if (!noteLinks || !noteEl || noteEl.hidden) return;
  if (!window.matchMedia("(max-width: 640px), (min-width: 641px) and (max-height: 699px)").matches) {
    noteLinks.classList.remove("has-more");
    noteLinks.style.removeProperty("--link-clip");
    noteLinks.style.removeProperty("--link-clip-left");
    for (const btn of noteLinks.querySelectorAll(".act")) btn.style.removeProperty("maxWidth");
    return;
  }
  const cap = noteLinks.querySelector(".k");
  const style = getComputedStyle(noteLinks);
  const gap = parseFloat(style.columnGap || style.gap) || 0;
  const box = noteLinks.getBoundingClientRect();
  const capW = cap ? cap.getBoundingClientRect().width : 0;
  const limit = Math.max(44, Math.floor(box.width - capW - (cap ? gap : 0)));
  for (const btn of noteLinks.querySelectorAll(".act")) btn.style.maxWidth = limit + "px";
  const edge = noteLinks.getBoundingClientRect();
  const kids = [...noteLinks.children];
  let clipL = 0;
  if (noteLinks.scrollLeft > 4) {
    for (let i = 0; i < kids.length; i++) {
      const row = kids[i].getBoundingClientRect();
      if (row.right <= edge.left + 1) continue;
      if (row.left < edge.left - 1 && i + 1 < kids.length) {
        clipL = kids[i + 1].getBoundingClientRect().left - edge.left;
      }
      break;
    }
  }
  const more = noteLinks.scrollWidth - noteLinks.clientWidth - noteLinks.scrollLeft > 4;
  let clip = edge.width;
  if (more) {
    let clipLeft = Infinity;
    for (const el of kids) {
      const row = el.getBoundingClientRect();
      if (row.left < edge.right - 1 && row.right > edge.right + 1 && row.left > edge.left + 8) {
        clipLeft = Math.min(clipLeft, row.left);
      }
    }
    if (clipLeft < Infinity) clip = clipLeft - edge.left;
  }
  noteLinks.style.setProperty("--link-clip-left", Math.max(0, clipL) + "px");
  noteLinks.style.setProperty("--link-clip", clip + "px");
  noteLinks.classList.toggle("has-more", clipL > 1 || clip < edge.width - 1);
}
function focusStar(id) {
  const star = memory.find((item) => item.id === id);
  if (!star) return;
  picked = id;
  pinnedSky = null;
  readSky(star.text || star.label);
  const node = buildWorld(fitScene(well.getBoundingClientRect())).all.find((item) => item.star.id === id);
  if (node) {
    const aim = anglesToward(node.pos);
    yawTarget = aim.yaw;
    pitchTarget = aim.pitch;
  }
  openNote(star);
}
async function sendText(value) {
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
    revealChoice();
    if (data.reply) {
      addLine("agent", data.reply);
      readSkyFit(data.reply);
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
    askSky("De qual lugar, Senhor?");
    return;
  }
  if (id === "sys-noticias") {
    text.value = "notícias sobre ";
    text.focus();
    askSky("Sobre o que, Senhor?");
    return;
  }
  if (id === "sys-lembretes") { sendText("quais lembretes"); return; }
  if (id === "sys-voz") { askSky(systemText["sys-voz"]); voiceBtn.click(); return; }
  if (id === "sys-busca") {
    text.value = "busque ";
    text.focus();
    askSky("O que devo procurar, Senhor?");
  }
}
function pointStar(ev, choose) {
  const hit = starAt(ev.clientX, ev.clientY);
  hovered = hit ? hit.star.id : "";
  if (!hit) {
    if (choose) {
      picked = "";
      closeNote();
      pinnedSky = null;
      readSky(orbitHint);
    } else if (pinnedSky !== null) {
      readSky(pinnedSky);
    } else if (picked) {
      const held = namedOnScreen.find((item) => item.star.id === picked);
      if (held) readSky(held.star.kind === "sistema" ? (systemText[held.star.id] || held.star.text) : held.star.text);
    }
    return;
  }
  if (!choose && pinnedSky !== null && hit.star.id === picked) {
    readSky(pinnedSky);
    return;
  }
  if (choose) {
    picked = hit.star.id;
    pinnedSky = null;
    const aim = anglesToward(hit.pos);
    yawTarget = aim.yaw;
    pitchTarget = aim.pitch;
  }
  readSky(hit.star.kind === "sistema" ? (systemText[hit.star.id] || hit.star.text) : hit.star.text);
  if (!choose) return;
  if (hit.star.kind === "nota") openNote(hit.star);
  else { closeNote(); runSystem(hit.star.id); }
}
function visibleStars() {
  return namedOnScreen.filter((item) => item.outside && item.star && item.star.label);
}
function nearestStar(key) {
  if (key !== "ArrowLeft" && key !== "ArrowRight" && key !== "ArrowUp" && key !== "ArrowDown") return null;
  const items = visibleStars();
  if (!items.length) return null;
  const cur = items.find((item) => item.star.id === (picked || hovered));
  const rect = well.getBoundingClientRect();
  const ox = cur ? cur.x : rect.left + rect.width / 2;
  const oy = cur ? cur.y : rect.top + rect.height / 2;
  let best = null;
  let bestScore = Infinity;
  for (const item of items) {
    if (cur && item.star.id === cur.star.id) continue;
    const dx = item.x - ox;
    const dy = item.y - oy;
    if (key === "ArrowRight" && dx <= 8) continue;
    if (key === "ArrowLeft" && dx >= -8) continue;
    if (key === "ArrowDown" && dy <= 8) continue;
    if (key === "ArrowUp" && dy >= -8) continue;
    const horizontal = key === "ArrowLeft" || key === "ArrowRight";
    const score = (horizontal ? Math.abs(dx) : Math.abs(dy)) + (horizontal ? Math.abs(dy) : Math.abs(dx)) * 1.6;
    if (score < bestScore) { best = item; bestScore = score; }
  }
  return best;
}
function focusStarItem(item, open) {
  picked = item.star.id;
  pinnedSky = null;
  const aim = anglesToward(item.pos);
  yawTarget = aim.yaw;
  pitchTarget = aim.pitch;
  readSky(item.star.kind === "sistema" ? (systemText[item.star.id] || item.star.text) : item.star.text);
  if (open && item.star.kind === "nota") openNote(item.star);
  else closeNote();
  if (open && item.star.kind === "sistema") runSystem(item.star.id);
  wake();
}
addEventListener("keydown", (ev) => {
  const el = document.activeElement;
  if (el && el !== document.body && el !== document.documentElement && el !== well) return;
  if (ev.key === "Escape" && noteEl && !noteEl.hidden) {
    ev.preventDefault();
    picked = "";
    hovered = "";
    closeNote();
    pinnedSky = null;
    readSky("");
    wake();
    return;
  }
  if (ev.key === "Enter" && picked) {
    const item = visibleStars().find((star) => star.star.id === picked);
    if (!item) return;
    ev.preventDefault();
    focusStarItem(item, true);
    return;
  }
  const item = nearestStar(ev.key);
  if (!item) return;
  ev.preventDefault();
  focusStarItem(item, false);
});
well.addEventListener("pointerdown", (ev) => {
  drag = { x: ev.clientX, y: ev.clientY, yaw: yawUser, pitch: pitchUser };
  dragMoved = 0;
  well.setPointerCapture(ev.pointerId);
  wake();
});
well.addEventListener("pointermove", (ev) => {
  if (!drag) {
    const before = hovered;
    pointStar(ev, false);
    if (hovered !== before) wake();
    return;
  }
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
  if (!drag && pinnedSky !== null) readSky(pinnedSky);
  else if (!drag && !picked) readSky(orbitHint);
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
  if (audioCtx.state === "suspended") {
    await Promise.race([
      audioCtx.resume(),
      new Promise((resolve) => setTimeout(resolve, 400)),
    ]);
  }
  const bytes = Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
  const url = URL.createObjectURL(new Blob([bytes], { type: "audio/wav" }));
  player.src = url;
  setState("speaking");
  try {
    await player.play();
    await new Promise((resolve) => { player.onended = resolve; });
  } catch (err) {
    /* O texto já está na tela. Sem gesto de som o painel volta a ficar pronto. */
  } finally {
    URL.revokeObjectURL(url);
    if (document.body.dataset.state === "speaking") setState("idle");
  }
}
async function post(url, body) {
  const res = await fetch(url, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body || {}),
  });
  if (!res.ok) throw new Error("falha " + res.status);
  return res.json();
}
async function showTurn(data, sourceBtn) {
  if (Object.prototype.hasOwnProperty.call(data, "note_query")) {
    noteQuery = data.note_query || "";
    wake();
  }
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
    if (data.reply) {
      addLine("agent", data.reply);
      if (noteEl.hidden) readSkyFit(data.reply);
    }
    if (data.audio_b64) await playWav(data.audio_b64);
    else setState("idle");
    return;
  }
  if (data.status === "replied") sessEl.textContent = "acordado";
  if (data.reply) {
    addLine("agent", data.reply);
    if (noteEl.hidden) readSkyFit(data.reply);
    else pinnedSky = null;
  }
  if (data.output) addLine("meta", data.output);
  if (sourceBtn && data.reply) mark(sourceBtn, "success");
  await refreshBrain();
  if (data.audio_b64) await playWav(data.audio_b64);
  else setState("idle");
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
for (const btn of document.querySelectorAll(".fact")) {
  btn.addEventListener("click", () => {
    if (btn.dataset.brain) { closeNote(); pinnedSky = null; readSky(""); chooseBrain(btn.dataset.brain); return; }
    if (btn.dataset.voice) { closeNote(); askSky(systemText["sys-voz"]); voiceBtn.click(); return; }
    if (btn.dataset.draft) {
      closeNote();
      text.value = btn.dataset.draft;
      text.focus();
      askSky(draftAsk[btn.dataset.draft] || "");
      return;
    }
    if (btn.dataset.ask) { closeNote(); pinnedSky = null; readSky(""); sendText(btn.dataset.ask); }
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
const systemsEl = document.querySelector(".systems");
let shownChoice = null;
function revealChoice() {
  requestAnimationFrame(() => {
    const chosen = document.querySelector('.fact[data-brain][aria-pressed="true"]');
    const id = chosen ? chosen.dataset.brain : "";
    if (id !== shownChoice && chosen && systemsEl) {
      const row = chosen.getBoundingClientRect();
      const scroller = systemsEl.getBoundingClientRect();
      if (row.left < scroller.left - 1 || row.right > scroller.right + 1) {
        systemsEl.scrollLeft += row.left - scroller.left;
      }
    }
    shownChoice = id;
    markMore();
  });
}
function markMore() {
  if (!systemsEl) return;
  const more = systemsEl.scrollWidth - systemsEl.clientWidth - systemsEl.scrollLeft > 8;
  systemsEl.classList.toggle("has-more", more);
  const rect = systemsEl.getBoundingClientRect();
  let clip = rect.width;
  if (more) {
    let clipLeft = Infinity;
    for (const fact of systemsEl.querySelectorAll(".fact")) {
      const row = fact.getBoundingClientRect();
      if (row.left < rect.right - 1 && row.right > rect.right + 1 && row.left - rect.left >= 44) {
        clipLeft = Math.min(clipLeft, row.left);
      }
    }
    if (clipLeft < Infinity) clip = clipLeft - rect.left;
  }
  systemsEl.style.setProperty("--clip", clip + "px");
  const tel = systemsEl.closest(".telemetry");
  if (!tel) return;
  let moreX = 6;
  if (clip < rect.width - 1) {
    const telRect = tel.getBoundingClientRect();
    moreX = Math.max(6, Math.round(telRect.right - (rect.left + clip) - 14));
  }
  tel.style.setProperty("--more-x", moreX + "px");
}
systemsEl.addEventListener("scroll", markMore, { passive: true });
addEventListener("resize", () => { resize(); wake(); requestAnimationFrame(settleLog); markMore(); seatNote(); seatLog(); seatPermit(); seatLinks(); });
noteLinks.addEventListener("scroll", seatLinks, { passive: true });
resize();
seatLog();
markMore();
requestAnimationFrame(markMore);
if (document.fonts && document.fonts.ready) document.fonts.ready.then(markMore);
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
