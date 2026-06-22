from .base import BaseProvider, Message, ToolDefinition, LLMResponse  # noqa: F401


def get_provider(name: str | None = None, config=None):
    """Factory. doc/intelecto.md Task 2.4 shape; mock added for offline use."""
    name = name or (config.providers.default if config else "mock")
    if name == "mock":
        from .mock import MockProvider
        return MockProvider()
    if name == "openrouter":
        from .openrouter import OpenRouterProvider
        return OpenRouterProvider(config)
    if name == "ollama":
        from .ollama import OllamaProvider
        return OllamaProvider(config)
    raise ValueError(f"Unknown provider: {name}")
