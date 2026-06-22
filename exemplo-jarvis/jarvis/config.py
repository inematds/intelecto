"""Config loader (config.json) with deep-merge over defaults and ~ expansion.

Mirrors the schema in doc/intelecto.md Task 1.1. Stdlib-only (json + os).
"""
import json
import os
from copy import deepcopy

DEFAULTS = {
    "name": "INTELECTO",
    "version": "0.1.0",
    "providers": {
        "default": "mock",
        "openrouter": {"model": "anthropic/claude-sonnet-4-20250514"},
        "ollama": {"model": "llama3.2", "base_url": "http://localhost:11434"},
        "mock": {"model": "mock-1"},
    },
    "channels": {"telegram": {"enabled": True}},
    "memory": {"db_path": "~/.intelecto/memory.db", "max_context_memories": 10},
    "workspace": "~/.intelecto/workspace",
    "identity": {
        "soul": "workspace/SOUL.md",
        "agents": "workspace/AGENTS.md",
        "user": "workspace/USER.md",
    },
    "safety": {
        "blocked_commands": [
            "rm -rf /", "mkfs", "dd if=", "shutdown", "reboot", "> /dev/sd",
        ],
        "max_command_timeout": 60,
    },
}

# Keys whose values are paths and should be ~-expanded.
_PATH_KEYS = {"db_path", "workspace", "soul", "agents", "user"}


def _deep_merge(base: dict, override: dict) -> dict:
    out = deepcopy(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = deepcopy(v)
    return out


def _expand_paths(node):
    if isinstance(node, dict):
        return {k: (os.path.expanduser(v) if (k in _PATH_KEYS and isinstance(v, str))
                    else _expand_paths(v)) for k, v in node.items()}
    if isinstance(node, list):
        return [_expand_paths(x) for x in node]
    return node


class _Section:
    """Dotted attribute access over a dict (config.providers.default)."""

    def __init__(self, data: dict):
        self._data = data

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        try:
            val = self._data[name]
        except KeyError as e:
            raise AttributeError(name) from e
        return _Section(val) if isinstance(val, dict) else val

    def __getitem__(self, name):
        val = self._data[name]
        return _Section(val) if isinstance(val, dict) else val

    def get(self, name, default=None):
        if name in self._data:
            return getattr(self, name)
        return default

    def to_dict(self):
        return deepcopy(self._data)


class Config(_Section):
    """Loaded config. Sparse config.json is merged onto DEFAULTS, paths expanded.

    Required fields are validated; missing ones raise ValueError.
    """

    REQUIRED = ["name", "providers", "memory", "workspace", "safety"]

    def __init__(self, path: str | None = None, data: dict | None = None):
        if data is None:
            user = {}
            if path and os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    user = json.load(f)
            data = _deep_merge(DEFAULTS, user)
        else:
            data = _deep_merge(DEFAULTS, data)
        data = _expand_paths(data)
        for field in self.REQUIRED:
            if field not in data:
                raise ValueError(f"Config missing required field: {field}")
        super().__init__(data)

    def save(self, path: str) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2)
