# claude-voice-agent — assistente de voz de mão dupla (local-first)

Voz conversacional estilo JARVIS. Você fala, ela ouve, pensa e responde. Ativação
por **wake-word "Lilith"**. Tudo local exceto o cérebro (Claude).

**Pipeline:** mic → silero VAD → **faster-whisper** (STT, pt-BR) → wake-gate →
**Claude** (cérebro) → **kokoro** (TTS, voz `pf_dora`) → alto-falante.
Transporte/orquestração: **LiveKit Agents** (modo `console`, sem servidor).

## Rodar

```bash
cd tools/claude-agent-voice
uv run python -m claude_agent_voice.agent console
```

**Cérebro via subscription, sem API key:** o agente usa o CLI `claude -p`, que já
está autenticado na tua assinatura (mesma auth do Claude Code). Não precisa de
`ANTHROPIC_API_KEY` nem paga por token. Basta o `claude` estar no PATH e logado.

No console: fale **"Lilith, ..."** para ativá-la. Após o wake, a conversa segue
aberta por ~30s sem repetir o nome. `Ctrl+C` encerra.

Se o `claude` não estiver no PATH, ela ainda te ouve e fala a saudação (prova
voz+ouvido), mas não pensa.

## Configuração (env)

| Var | Default | O quê |
|---|---|---|
| `CLAUDE_VOICE_CLAUDE_CLI` | `claude` | binário do CLI (cérebro via subscription) |
| `CLAUDE_VOICE_LLM_MODEL` | (default do CLI) | modelo do cérebro (`--model`) |
| `CLAUDE_VOICE_VOICE` | `pf_dora` | voz kokoro |
| `CLAUDE_VOICE_WHISPER_MODEL` | `small` | modelo faster-whisper |
| `CLAUDE_VOICE_REQUIRE_WAKE` | `true` | exigir a wake-word |
| `CLAUDE_VOICE_WAKE_WINDOW_S` | `30` | janela de conversa pós-wake (s) |
| `CLAUDE_VOICE_KOKORO_MODEL` / `_VOICES` | `~/.cache/claude-voice/` | modelo/vozes kokoro |

## Pré-requisitos (já instalados nesta máquina)

- Modelo kokoro: `~/.cache/claude-voice/kokoro-v1.0.onnx` + `voices-v1.0.bin` (~350MB).
- espeak-ng: **não é necessário** — vem via `espeakng-loader`.
- `livekit-server.exe` em `vendor/` (útil para o modo `dev`/room; o `console` não precisa).

## Testes

```bash
uv run pytest -q      # 30 passam: wake-gate, persona, settings, TTS/STT (DSP puro + wiring)
```

O código separa **lógica pura testável** (`wake.py`, DSP em `tts_kokoro.py`/`stt_whisper.py`,
`persona.py`, `settings.py`) do **I/O de áudio** (só exercitado no `console`).

## Estado / roadmap

- [x] Fatia 0 — stack instalada (LiveKit + Whisper + kokoro + Claude) em py3.12.
- [x] Fatia 1 — TTS kokoro pt-BR plugado; Lilith fala (verificado em áudio).
- [x] Fatia 2 — STT faster-whisper plugado (ouvido); wiring testado.
- [x] Fatia 3 — cérebro Claude no loop (liga com a chave).
- [x] Fatia 4 — wake-word "Lilith" (keyword-spotting no transcript + janela).
- [ ] **Verificação ao vivo** no mic (você) do loop completo.
- [ ] Próximo: barge-in fino, ações ("caso eu peça"), wake-word dedicada (Porcupine/openWakeWord).
