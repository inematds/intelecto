"""Core agent loop (doc/intelecto.md Task 4.5).

channel -> context -> provider -> tools -> memory. Max N tool rounds, then force
a text response.
"""
import json

from ..channels.base import IncomingMessage
from ..providers.base import Message


class AgentLoop:
    def __init__(self, provider, context, memory, tools, max_rounds: int = 5):
        self.provider = provider
        self.context = context
        self.memory = memory
        self.tools = tools
        self.max_rounds = max_rounds
        self.history: dict[str, list[Message]] = {}  # per chat_id

    async def process_message(self, incoming: IncomingMessage) -> str:
        chat_id = incoming.chat_id
        history = self.history.setdefault(chat_id, [])
        messages = await self.context.build(history, incoming.text)

        tool_defs = self.tools.as_definitions() if self.tools else None
        final_text = ""

        for _round in range(self.max_rounds):
            resp = await self.provider.chat(messages, tools=tool_defs)

            if not resp.tool_calls:
                final_text = resp.content or ""
                break

            # Record the assistant turn that requested tools.
            messages.append(Message(
                role="assistant",
                content=resp.content or "",
                tool_calls=resp.tool_calls,
            ))

            for call in resp.tool_calls:
                name = call["name"]
                args = call.get("arguments", {}) or {}
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        args = {}
                tool = self.tools.get(name)
                if tool is None:
                    output = f"error: unknown tool {name}"
                else:
                    result = await tool.execute(**args)
                    output = result.output if result.success else (result.error or "tool error")
                messages.append(Message(
                    role="tool",
                    content=output,
                    tool_call_id=call.get("id"),
                ))
        else:
            # Ran out of rounds: force a final text call without tools.
            resp = await self.provider.chat(messages, tools=None)
            final_text = resp.content or "(no response)"

        # Update conversation history (skip trivial turns).
        history.append(Message(role="user", content=incoming.text))
        history.append(Message(role="assistant", content=final_text))
        self.history[chat_id] = history[-50:]
        return final_text
