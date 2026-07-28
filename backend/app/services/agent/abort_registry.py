"""In-process abort state for active agent streams."""

from dataclasses import dataclass


@dataclass
class AbortState:
    """Abort state for one active conversation stream."""

    user_id: int
    conversation_id: str
    aborted: bool = False


class AbortRegistry:
    """Track active chat streams that can be interrupted within one process."""

    def __init__(self) -> None:
        self._states: dict[str, AbortState] = {}

    def register(self, *, user_id: int, conversation_id: str) -> None:
        """Register a stream as active and clear stale abort flags."""
        self._states[conversation_id] = AbortState(user_id=user_id, conversation_id=conversation_id)

    def request_abort(self, *, user_id: int, conversation_id: str) -> bool:
        """Mark an active stream as aborted if it belongs to the user."""
        state = self._states.get(conversation_id)
        if state is None or state.user_id != user_id:
            return False
        state.aborted = True
        return True

    def is_aborted(self, *, user_id: int, conversation_id: str) -> bool:
        """Return whether the active stream has been aborted."""
        state = self._states.get(conversation_id)
        return bool(state and state.user_id == user_id and state.aborted)

    def clear(self, *, user_id: int, conversation_id: str) -> None:
        """Clear active state if it still belongs to the user."""
        state = self._states.get(conversation_id)
        if state and state.user_id == user_id:
            self._states.pop(conversation_id, None)


abort_registry = AbortRegistry()
