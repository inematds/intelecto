"""Stdlib unittest suite for the jarvis core. No network, no pip, no API keys."""
import asyncio
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from jarvis.config import Config
from jarvis.security.safety import SafetyChecker
from jarvis.security.secrets import SecretStore
from jarvis.memory.store import MemoryStore
from jarvis.providers import get_provider
from jarvis.channels.cli import CLIChannel
from jarvis.channels.telegram import split_message
from jarvis.agent.context import ContextBuilder
from jarvis.agent.loop import AgentLoop
from jarvis.tools.registry import ToolRegistry
from jarvis.tools.memory_tools import SaveMemoryTool, SearchMemoryTool, ForgetMemoryTool


def run(coro):
    return asyncio.run(coro)


class TestMemoryFTS5(unittest.TestCase):
    """(a) FTS5 save -> search returns the hit; forget removes it."""

    def test_save_search_forget(self):
        async def scenario():
            mem = MemoryStore(":memory:")
            await mem.initialize()
            mid = await mem.save("Meu nome é Nei e moro no Brasil", "fact")
            self.assertIsInstance(mid, int)

            hits = await mem.search("Nei")
            self.assertTrue(hits, "search should return the saved memory")
            self.assertIn("Nei", hits[0].content)
            self.assertGreater(hits[0].relevance, 0.0)

            # Recent reflects the insert.
            recent = await mem.recent()
            self.assertEqual(recent[0].id, mid)

            # Forget removes it from FTS too.
            self.assertTrue(await mem.forget(mid))
            self.assertEqual(await mem.search("Nei"), [])
            self.assertFalse(await mem.forget(mid))  # already gone
            await mem.close()

        run(scenario())


class TestAgentLoopToolRound(unittest.TestCase):
    """(b) Full agent-loop round: MockProvider asks for a tool, loop runs it,
    produces a final reply."""

    def test_full_tool_round(self):
        async def scenario():
            config = Config(data={"providers": {"default": "mock"},
                                  "memory": {"db_path": ":memory:"}})
            mem = MemoryStore(":memory:")
            await mem.initialize()
            tools = ToolRegistry()
            tools.register(SaveMemoryTool(mem))
            tools.register(SearchMemoryTool(mem))
            tools.register(ForgetMemoryTool(mem))
            provider = get_provider("mock")
            ctx = ContextBuilder(config, mem, tools)
            agent = AgentLoop(provider, ctx, mem, tools)
            channel = CLIChannel(sender_name="Nei")
            await channel.start(on_message=agent.process_message)

            reply = await channel.feed("lembre que meu nome é Nei")
            # The mock requested save_memory, the loop executed it -> fact in DB.
            hits = await mem.search("nome")
            self.assertTrue(hits)
            self.assertIn("Nei", hits[0].content)
            # Provider was called at least twice (tool request + final answer).
            self.assertGreaterEqual(provider.calls, 2)
            self.assertTrue(reply)  # produced a final text reply
            await mem.close()

        run(scenario())


class TestSafetyBlocklist(unittest.TestCase):
    """(c) Blocklist blocks dangerous command, allows safe one."""

    def test_block_and_allow(self):
        sc = SafetyChecker()
        safe, reason = sc.is_safe("rm -rf /")
        self.assertFalse(safe)
        self.assertIn("rm -rf /", reason)

        for bad in ("mkfs.ext4 /dev/sda1", "dd if=/dev/zero of=/dev/sda", "shutdown now"):
            ok, _ = sc.is_safe(bad)
            self.assertFalse(ok, f"{bad} should be blocked")

        ok, reason = sc.is_safe("echo hello && ls -la")
        self.assertTrue(ok)
        self.assertIsNone(reason)

    def test_audit_log(self):
        with tempfile.TemporaryDirectory() as d:
            log = os.path.join(d, "audit.log")
            sc = SafetyChecker(audit_log=log)
            sc.audit("rm -rf /", False)
            sc.audit("ls", True)
            with open(log) as f:
                content = f.read()
            self.assertIn("BLOCK", content)
            self.assertIn("ALLOW", content)


class TestConfigRoundTrip(unittest.TestCase):
    """(d) Config round-trips (save -> load), sparse merge + ~ expansion."""

    def test_roundtrip_and_merge(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "config.json")
            cfg = Config(data={"name": "JARVIS",
                               "providers": {"default": "ollama"}})
            cfg.save(path)
            loaded = Config(path=path)
            self.assertEqual(loaded.name, "JARVIS")
            self.assertEqual(loaded.providers.default, "ollama")  # override kept
            # Default carried through the merge.
            self.assertEqual(loaded.providers.ollama.base_url, "http://localhost:11434")
            self.assertEqual(loaded.safety.max_command_timeout, 60)
            # ~ expanded.
            self.assertFalse(loaded.memory.db_path.startswith("~"))

    def test_required_validation(self):
        # A normally-built config has all required fields (merged from DEFAULTS).
        cfg = Config(data={})
        for field in Config.REQUIRED:
            self.assertIn(field, cfg.to_dict())
        # If validation is bypassed by feeding pre-merged data missing a required
        # field, construction raises.
        with self.assertRaises(ValueError):
            from jarvis import config as cfgmod
            orig = cfgmod.DEFAULTS
            try:
                cfgmod.DEFAULTS = {"providers": {}, "memory": {}, "workspace": "/", "safety": {}}
                Config(data={})  # 'name' now absent from defaults -> ValueError
            finally:
                cfgmod.DEFAULTS = orig


class TestSecretStore(unittest.TestCase):
    """Bonus: secrets encrypt at rest, round-trip, list/delete."""

    def test_secret_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, ".secrets")
            store = SecretStore(path, machine_id="test-machine")
            store.save_secret("TELEGRAM_BOT_TOKEN", "123:ABC")
            self.assertEqual(store.get_secret("TELEGRAM_BOT_TOKEN"), "123:ABC")
            self.assertEqual(store.list_secrets(), ["TELEGRAM_BOT_TOKEN"])
            # On-disk value is not plaintext.
            with open(path) as f:
                raw = f.read()
            self.assertNotIn("123:ABC", raw)
            # Wrong machine id can't decrypt.
            other = SecretStore(path, machine_id="different-machine")
            with self.assertRaises(ValueError):
                other.get_secret("TELEGRAM_BOT_TOKEN")
            store.delete_secret("TELEGRAM_BOT_TOKEN")
            self.assertEqual(store.list_secrets(), [])


class TestIdentityContext(unittest.TestCase):
    """(e) Identity context string contains SOUL/USER content."""

    def test_context_contains_identity(self):
        async def scenario():
            config = Config(data={"memory": {"db_path": ":memory:"}})
            mem = MemoryStore(":memory:")
            await mem.initialize()
            tools = ToolRegistry()
            tools.register(SaveMemoryTool(mem))
            ctx = ContextBuilder(config, mem, tools)
            prompt = await ctx.build_system_prompt()
            self.assertIn("JARVIS", prompt)         # from SOUL.md
            self.assertIn("Nei", prompt)            # from SOUL/USER.md
            self.assertIn("save_memory", prompt)    # tool list
            # build() returns Message list with system first, user last.
            msgs = await ctx.build([], "oi")
            self.assertEqual(msgs[0].role, "system")
            self.assertEqual(msgs[-1].role, "user")
            self.assertEqual(msgs[-1].content, "oi")
            await mem.close()

        run(scenario())


class TestTelegramSplit(unittest.TestCase):
    """Bonus: Telegram 4096-char splitting (structural channel helper)."""

    def test_split(self):
        short = "hello"
        self.assertEqual(split_message(short), ["hello"])
        big = ("para " * 1000).strip()  # > 4096 chars
        chunks = split_message(big)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(c) <= 4096 for c in chunks))


if __name__ == "__main__":
    unittest.main(verbosity=2)
