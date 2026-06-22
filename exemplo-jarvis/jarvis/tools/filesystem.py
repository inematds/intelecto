"""Filesystem tools (workspace-restricted). Safe tool #1: read_file."""
import os

from .base import BaseTool, ToolResult

MAX_READ = 100 * 1024  # 100KB cap per the plan


class ReadFileTool(BaseTool):
    name = "read_file"
    description = "Read a UTF-8 text file from inside the workspace (max 100KB)."
    parameters = {
        "type": "object",
        "properties": {"path": {"type": "string", "description": "Path inside workspace"}},
        "required": ["path"],
    }

    def __init__(self, workspace: str):
        self.workspace = os.path.abspath(os.path.expanduser(workspace))

    def _resolve(self, path: str) -> str:
        full = os.path.abspath(os.path.join(self.workspace, path))
        if not (full == self.workspace or full.startswith(self.workspace + os.sep)):
            raise ValueError("path escapes workspace")
        return full

    async def execute(self, **kwargs) -> ToolResult:
        path = kwargs.get("path", "")
        try:
            full = self._resolve(path)
        except ValueError as e:
            return ToolResult(success=False, output="", error=str(e))
        if not os.path.isfile(full):
            return ToolResult(success=False, output="", error="file not found")
        with open(full, "r", encoding="utf-8") as f:
            data = f.read(MAX_READ)
        return ToolResult(success=True, output=data)
