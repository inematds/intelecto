"""Tool registry (doc/intelecto.md Task 4.3)."""
from ..providers.base import ToolDefinition
from .base import BaseTool


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def all(self) -> list[BaseTool]:
        return list(self._tools.values())

    def as_definitions(self) -> list[ToolDefinition]:
        return [
            ToolDefinition(name=t.name, description=t.description, parameters=t.parameters)
            for t in self._tools.values()
        ]
