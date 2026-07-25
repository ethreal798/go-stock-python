"""Factory for OpenAI-compatible or LangChain chat clients."""

from typing import Any

from .runtime_model_config_service import RuntimeModelConfig


class LLMFactory:
    """Create chat model clients from a runtime model config."""

    def create_chat_client(self, config: RuntimeModelConfig) -> Any:
        """Create a chat client.

        TODO: Return an OpenAI-compatible client first, then add LangChain
        ChatOpenAI support when chains are wired.
        """
        raise NotImplementedError
