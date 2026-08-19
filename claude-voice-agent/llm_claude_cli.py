"""Cérebro (LLM) via **subscription** (sem API key).

Em vez do plugin anthropic (que exige ANTHROPIC_API_KEY), este LLM chama o CLI
``claude -p`` — que já está autenticado na assinatura do Kleber (mesma auth do
Claude Code). Sem token, sem custo por token.

Trade-off: cada turno spawna o CLI (~alguns segundos de overhead) e a resposta
vem inteira (não streamada) — ok pro MVP, já que o TTS sintetiza a fala completa.

``render_prompt`` (pura, testável) transforma o histórico da conversa no texto
que vai pro ``claude -p``; o system prompt (persona) segue por ``--append-system-prompt``.
"""

from __future__ import annotations

import asyncio

from livekit.agents import (
    DEFAULT_API_CONNECT_OPTIONS,
    NOT_GIVEN,
    APIConnectionError,
    APIConnectOptions,
    NotGivenOr,
    llm,
    utils,
)

from .speech import strip_for_speech


def render_prompt(
    turns: list[tuple[str, str]], assistant_label: str = "Lilith"
) -> tuple[str, str]:
    """(role, texto)[] -> (prompt_conversa, system). Puro e determinístico.

    ``system`` junta as mensagens de sistema; o resto vira um roteiro
    ``Usuário:/<persona>:`` terminando em ``<persona>:`` (deixa o modelo
    continuar). ``assistant_label`` é o nome da persona ativa (ex.: "Gambit"),
    senão o modelo se confunde de quem está falando.
    """
    system_parts: list[str] = []
    lines: list[str] = []
    for role, text in turns:
        text = (text or "").strip()
        if not text:
            continue
        if role == "system":
            system_parts.append(text)
        elif role == "assistant":
            lines.append(f"{assistant_label}: {text}")
        else:  # user (default)
            lines.append(f"Usuário: {text}")
    prompt = "\n".join([*lines, f"{assistant_label}:"])
    return prompt, "\n\n".join(system_parts)


def _extract_turns(chat_ctx) -> list[tuple[str, str]]:
    items = getattr(chat_ctx, "items", None)
    if items is None:
        items = getattr(chat_ctx, "messages", [])
    turns: list[tuple[str, str]] = []
    for it in items:
        role = getattr(it, "role", "user")
        text = getattr(it, "text_content", "") or ""
        turns.append((role, text))
    return turns


class ClaudeCliLLM(llm.LLM):
    def __init__(
        self,
        *,
        fallback_system: str = "",
        model: str | None = None,
        cli: str = "claude",
        label: str = "Lilith",
    ) -> None:
        super().__init__()
        self._fallback_system = fallback_system
        self._model = model
        self._cli = cli
        self._label = label

    def chat(
        self,
        *,
        chat_ctx: llm.ChatContext,
        tools=None,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
        parallel_tool_calls: NotGivenOr[bool] = NOT_GIVEN,
        tool_choice: NotGivenOr[object] = NOT_GIVEN,
        extra_kwargs: NotGivenOr[dict] = NOT_GIVEN,
    ) -> ClaudeCliStream:
        return ClaudeCliStream(
            self, chat_ctx=chat_ctx, tools=tools or [], conn_options=conn_options
        )


class ClaudeCliStream(llm.LLMStream):
    async def _run(self) -> None:
        brain: ClaudeCliLLM = self._llm  # type: ignore[assignment]
        prompt, system = render_prompt(
            _extract_turns(self._chat_ctx), assistant_label=brain._label
        )
        system = system or brain._fallback_system

        args = [brain._cli, "-p", prompt, "--output-format", "text"]
        if system:
            args += ["--append-system-prompt", system]
        if brain._model:
            args += ["--model", brain._model]

        try:
            proc = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            out, err = await proc.communicate()
        except (OSError, ValueError) as e:
            raise APIConnectionError(f"claude CLI falhou: {e}") from e

        text = out.decode("utf-8", "replace").strip()
        if proc.returncode != 0 and not text:
            msg = err.decode("utf-8", "replace").strip() or "sem saída"
            raise APIConnectionError(f"claude -p retornou {proc.returncode}: {msg}")

        self._event_ch.send_nowait(
            llm.ChatChunk(
                id=utils.shortuuid(),
                delta=llm.ChoiceDelta(role="assistant", content=strip_for_speech(text)),
            )
        )
