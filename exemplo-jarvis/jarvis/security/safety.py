"""Command safety: blocklist + path-traversal check + audit log (Task 1.3)."""
import datetime
import os

DEFAULT_BLOCKLIST = [
    "rm -rf /", "mkfs", "dd if=", "shutdown", "reboot", "> /dev/sd",
    ":(){:|:&};:",  # fork bomb
]


class SafetyChecker:
    def __init__(self, blocked_commands=None, workspace=None, audit_log=None):
        self.blocked = list(blocked_commands or DEFAULT_BLOCKLIST)
        self.workspace = os.path.expanduser(workspace) if workspace else None
        self.audit_log = os.path.expanduser(audit_log) if audit_log else None

    def is_safe(self, command: str) -> tuple[bool, str | None]:
        """Return (safe, reason_if_blocked). Substring match on the blocklist."""
        norm = " ".join(command.strip().split())
        low = norm.lower()
        for bad in self.blocked:
            if bad.lower() in low:
                return False, f"blocked command pattern: {bad!r}"
        # Path traversal beyond workspace.
        if "../" in norm and self.workspace:
            return False, "path traversal ('../') is not allowed"
        return True, None

    def audit(self, command: str, allowed: bool) -> None:
        if not self.audit_log:
            return
        os.makedirs(os.path.dirname(os.path.abspath(self.audit_log)), exist_ok=True)
        ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
        verdict = "ALLOW" if allowed else "BLOCK"
        with open(self.audit_log, "a", encoding="utf-8") as f:
            f.write(f"{ts}\t{verdict}\t{command}\n")
