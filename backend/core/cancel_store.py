"""
Cancel Store

In-memory set of search IDs that have been cancelled by the user.
Search route handlers check this cooperatively between major steps.
"""

_cancelled: set[str] = set()


def mark_cancelled(search_id: str) -> None:
    """Mark a search as cancelled."""
    _cancelled.add(search_id)


def is_cancelled(search_id: str) -> bool:
    """Return True if the search has been cancelled."""
    return search_id in _cancelled


def clear_cancelled(search_id: str) -> None:
    """Remove a search from the cancelled set (called after the search stops)."""
    _cancelled.discard(search_id)
