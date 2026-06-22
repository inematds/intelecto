"""Context builder — assembles the system prompt (doc/intelecto.md Task 3.3).

Concatenates SOUL.md + AGENTS.md + USER.md, appends recent/relevant memories and
the available tool list, returns Message objects for the provider.
"""
import os

from ..providers.base import Message


class ContextBuilder:
    def __init__(self, config, memory, tools=None):
        self.config = config
        self.memory = memory
        self.tools = tools
        # Resolve identity paths relative to the build root so file:// works.
        self.root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.identity_files = {
            "SOUL": os.path.join(self.root, "workspace", "SOUL.md"),
            "AGENTS": os.path.join(self.root, "workspace", "AGENTS.md"),
            "USER": os.path.join(self.root, "workspace", "USER.md"),
        }

    def _read(self, path: str) -> str:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except OSError:
            return ""

    async def build_system_prompt(self) -> str:
        parts = []
        for label, path in self.identity_files.items():
            text = self._read(path)
            if text:
                parts.append(f"# {label}\n{text}")
        # Recent facts/preferences.
        recent = await self.memory.recent(limit=self.config.memory.get("max_context_memories", 10))
        facts = [m.content for m in recent if m.category in ("fact", "preference")]
        if facts:
            parts.append("# Known facts\n" + "\n".join(f"- {f}" for f in facts))
        # Tool list.
        if self.tools:
            tlist = "\n".join(f"- {t.name}: {t.description}" for t in self.tools.all())
            if tlist:
                parts.append("# Available tools\n" + tlist)
        return "\n\n".join(parts)

    async def build(self, history: list[Message], query: str) -> list[Message]:
        system = await self.build_system_prompt()
        msgs = [Message(role="system", content=system)]
        # Relevant memories for this query.
        hits = await self.memory.search(query, limit=5)
        if hits:
            mem = "Relevant memories:\n" + "\n".join(f"- {h.content}" for h in hits)
            msgs.append(Message(role="system", content=mem))
        msgs.extend(history)
        msgs.append(Message(role="user", content=query))
        return msgs
