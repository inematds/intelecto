"""End-to-end smoke test: boot the agent with MockProvider + CLIChannel,
send a message that both saves and recalls a name, print the reply.

Proves memory + tool-calling loop work together with no network/API key.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from jarvis.config import Config
from jarvis.providers import get_provider
from jarvis.memory.store import MemoryStore
from jarvis.channels.cli import CLIChannel
from jarvis.agent.context import ContextBuilder
from jarvis.agent.loop import AgentLoop
from jarvis.tools.registry import ToolRegistry
from jarvis.tools.memory_tools import SaveMemoryTool, SearchMemoryTool, ForgetMemoryTool


async def main():
    config = Config(data={"providers": {"default": "mock"},
                          "memory": {"db_path": ":memory:"}})

    provider = get_provider("mock")
    memory = MemoryStore(":memory:")
    await memory.initialize()

    tools = ToolRegistry()
    tools.register(SaveMemoryTool(memory))
    tools.register(SearchMemoryTool(memory))
    tools.register(ForgetMemoryTool(memory))

    context = ContextBuilder(config, memory, tools)
    agent = AgentLoop(provider, context, memory, tools)

    channel = CLIChannel(sender_name="Nei")
    await channel.start(on_message=agent.process_message)

    # Turn 1: save the name (mock asks for save_memory tool).
    r1 = await channel.feed("lembre que meu nome é Nei")
    print("USER : lembre que meu nome é Nei")
    print("JARVIS:", r1)

    # Turn 2: recall it (mock asks for search_memory tool, then answers).
    r2 = await channel.feed("qual meu nome?")
    print("USER : qual meu nome?")
    print("JARVIS:", r2)

    # Prove it actually came from the DB.
    hits = await memory.search("nome")
    print("DB   :", [h.content for h in hits])

    await memory.close()


if __name__ == "__main__":
    asyncio.run(main())
