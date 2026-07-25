"""Backward-compatible import for the new agent service package."""

from app.services.agent import AgentService

__all__ = ["AgentService"]
