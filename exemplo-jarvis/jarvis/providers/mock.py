"""Offline MockProvider — no network, no API key.

Drives a realistic tool-calling loop:
  Round 1: if the user asks to remember/recall something, request a tool call
           (save_memory or search_memory).
  Round 2: after a tool result is present, return a final text answer.

It inspects the message list to decide which round it is in, so the same loop
code that talks to OpenRouter also works against this.
"""
import json
import re

from .base import BaseProvider, LLMResponse, Message


class MockProvider(BaseProvider):
    def __init__(self):
        self.calls = 0

    @staticmethod
    def _last_user_text(messages: list[Message]) -> str:
        for m in reversed(messages):
            if m.role == "user":
                return m.content or ""
        return ""

    @staticmethod
    def _tool_results(messages: list[Message]) -> list[Message]:
        return [m for m in messages if m.role == "tool"]

    async def chat(self, messages, tools=None, model=None, temperature=0.7):
        self.calls += 1
        user = self._last_user_text(messages).lower()
        tool_msgs = self._tool_results(messages)
        usage = {"prompt_tokens": 42, "completion_tokens": 17}

        # --- Phase 2: a tool already ran -> produce the final answer. ---
        if tool_msgs:
            last = tool_msgs[-1].content or ""
            m = re.search(r"meu nome (?:é|e|:)\s*([A-Za-zÀ-ÿ]+)", last, re.IGNORECASE)
            if not m:
                m = re.search(r"\bnome[:=]\s*([A-Za-zÀ-ÿ]+)", last, re.IGNORECASE)
            if m:
                nome = m.group(1)
                return LLMResponse(
                    content=f"Seu nome é {nome}.",
                    tool_calls=None,
                    usage=usage,
                )
            return LLMResponse(
                content=f"Pronto. Resultado da ferramenta: {last}",
                tool_calls=None,
                usage=usage,
            )

        # --- Phase 1: decide whether to call a tool. ---
        # Pattern: "lembre que meu nome é X e qual meu nome?"
        m = re.search(r"meu nome (?:é|e)\s+([A-Za-zÀ-ÿ]+)", user)
        if ("lembre" in user or "lembra" in user or "guarda" in user) and m:
            nome = m.group(1).capitalize()
            return LLMResponse(
                content=None,
                tool_calls=[{
                    "id": "call_1",
                    "name": "save_memory",
                    "arguments": {"content": f"Meu nome é {nome}", "category": "fact"},
                }],
                usage=usage,
            )
        if "qual" in user and "nome" in user:
            return LLMResponse(
                content=None,
                tool_calls=[{
                    "id": "call_1",
                    "name": "search_memory",
                    "arguments": {"query": "nome"},
                }],
                usage=usage,
            )

        # Default: plain canned reply, no tools.
        return LLMResponse(
            content="Olá! Sou seu assistente offline (mock).",
            tool_calls=None,
            usage=usage,
        )
