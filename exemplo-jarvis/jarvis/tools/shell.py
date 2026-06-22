"""Shell tool (safety-gated). Safe tool #2: run_command.

Runs only commands the SafetyChecker allows. Output truncated to 10KB. Uses
asyncio subprocess; timeout from config.
"""
import asyncio

from .base import BaseTool, ToolResult

MAX_OUT = 10 * 1024


class RunCommandTool(BaseTool):
    name = "run_command"
    description = "Run a shell command (blocked dangerous ones are refused)."
    parameters = {
        "type": "object",
        "properties": {"command": {"type": "string"}},
        "required": ["command"],
    }

    def __init__(self, safety, timeout: int = 60):
        self.safety = safety
        self.timeout = timeout

    async def execute(self, **kwargs) -> ToolResult:
        command = kwargs.get("command", "")
        safe, reason = self.safety.is_safe(command)
        self.safety.audit(command, safe)
        if not safe:
            return ToolResult(success=False, output="", error=f"refused: {reason}")
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            out, _ = await asyncio.wait_for(proc.communicate(), timeout=self.timeout)
        except asyncio.TimeoutError:
            return ToolResult(success=False, output="", error="command timed out")
        text = out.decode("utf-8", "replace")[:MAX_OUT]
        return ToolResult(success=proc.returncode == 0, output=text,
                          error=None if proc.returncode == 0 else f"exit {proc.returncode}")
