"""Memory tools the LLM can call (doc/intelecto.md Task 4.5: save/search/forget)."""
from .base import BaseTool, ToolResult


class SaveMemoryTool(BaseTool):
    name = "save_memory"
    description = "Store a fact or preference for later recall."
    parameters = {
        "type": "object",
        "properties": {
            "content": {"type": "string"},
            "category": {"type": "string", "default": "fact"},
        },
        "required": ["content"],
    }

    def __init__(self, memory):
        self.memory = memory

    async def execute(self, **kwargs) -> ToolResult:
        content = kwargs.get("content", "")
        category = kwargs.get("category", "fact")
        if not content:
            return ToolResult(success=False, output="", error="empty content")
        mid = await self.memory.save(content, category)
        return ToolResult(success=True, output=f"saved memory #{mid}: {content}")


class SearchMemoryTool(BaseTool):
    name = "search_memory"
    description = "Search stored memories by keyword."
    parameters = {
        "type": "object",
        "properties": {"query": {"type": "string"}},
        "required": ["query"],
    }

    def __init__(self, memory):
        self.memory = memory

    async def execute(self, **kwargs) -> ToolResult:
        query = kwargs.get("query", "")
        hits = await self.memory.search(query, limit=5)
        if not hits:
            return ToolResult(success=True, output="(no memories found)")
        return ToolResult(success=True, output="; ".join(h.content for h in hits))


class ForgetMemoryTool(BaseTool):
    name = "forget_memory"
    description = "Delete a memory by id."
    parameters = {
        "type": "object",
        "properties": {"id": {"type": "integer"}},
        "required": ["id"],
    }

    def __init__(self, memory):
        self.memory = memory

    async def execute(self, **kwargs) -> ToolResult:
        ok = await self.memory.forget(int(kwargs.get("id")))
        return ToolResult(success=ok, output="forgotten" if ok else "not found")
