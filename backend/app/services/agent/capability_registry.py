"""Capability definitions for chat routing."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CapabilityDefinition:
    """Static execution defaults for one chat capability."""

    code: str
    execution_engine: str
    rag_enabled: bool = False
    tool_enabled: bool = False
    chain: str = "general"
    capabilities: list[str] = field(default_factory=list)
    tool_allowlist: list[str] = field(default_factory=list)
    default_options: dict[str, Any] = field(default_factory=dict)


class CapabilityRegistry:
    """Resolve frontend capability into backend execution defaults."""

    _definitions: dict[str, CapabilityDefinition] = {
        "general": CapabilityDefinition(
            code="general",
            execution_engine="llm",
            chain="general",
            capabilities=["general"],
        ),
        "news_rag": CapabilityDefinition(
            code="news_rag",
            execution_engine="workflow",
            rag_enabled=True,
            chain="news_rag",
            capabilities=["news_rag"],
        ),
    }

    def resolve(self, capability: str | None) -> CapabilityDefinition:
        """Return a capability definition, falling back to general chat."""
        return self._definitions.get(capability or "general", self._definitions["general"])
