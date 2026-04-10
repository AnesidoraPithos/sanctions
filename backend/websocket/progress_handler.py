"""
WebSocket Progress Handler

In-memory progress tracking for long-running searches.
Clients connect to /ws/progress/{search_id} to receive live step updates.
"""

import asyncio
import logging
from typing import Dict, Optional
from dataclasses import dataclass, field
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json

logger = logging.getLogger(__name__)

router = APIRouter()


@dataclass
class ProgressEvent:
    search_id: str
    step: str
    percent: int
    done: bool = False
    error: Optional[str] = None


# In-memory store: search_id -> latest ProgressEvent
progress_store: Dict[str, ProgressEvent] = {}


def update_progress(search_id: str, step: str, percent: int, done: bool = False, error: Optional[str] = None) -> None:
    """Update progress for a running search. Called from search route handlers."""
    progress_store[search_id] = ProgressEvent(
        search_id=search_id,
        step=step,
        percent=percent,
        done=done,
        error=error,
    )
    logger.debug(f"[progress] {search_id}: {percent}% — {step}")


def complete_progress(search_id: str) -> None:
    """Mark a search as complete."""
    update_progress(search_id, step="Complete", percent=100, done=True)


def fail_progress(search_id: str, error: str) -> None:
    """Mark a search as failed."""
    update_progress(search_id, step="Failed", percent=0, done=True, error=error)


def clear_progress(search_id: str) -> None:
    """Remove progress entry (cleanup after client disconnects)."""
    progress_store.pop(search_id, None)


@router.websocket("/ws/progress/{search_id}")
async def websocket_progress(websocket: WebSocket, search_id: str):
    """
    Stream search progress events to a connected WebSocket client.

    Polls the in-memory store every 500 ms and sends updates until the
    search is done or the client disconnects. Times out after 20 minutes.
    """
    await websocket.accept()
    logger.info(f"[ws] Client connected for search {search_id}")

    try:
        timeout_seconds = 1200  # 20 minutes max
        elapsed = 0
        poll_interval = 0.5

        # Send initial placeholder so client knows connection is live
        await websocket.send_text(json.dumps({
            "search_id": search_id,
            "step": "Initialising…",
            "percent": 0,
            "done": False,
        }))

        while elapsed < timeout_seconds:
            event = progress_store.get(search_id)
            if event:
                payload = {
                    "search_id": event.search_id,
                    "step": event.step,
                    "percent": event.percent,
                    "done": event.done,
                }
                if event.error:
                    payload["error"] = event.error

                await websocket.send_text(json.dumps(payload))

                if event.done:
                    break

            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

        if elapsed >= timeout_seconds:
            await websocket.send_text(json.dumps({
                "search_id": search_id,
                "step": "Timeout",
                "percent": 0,
                "done": True,
                "error": "Search timed out",
            }))

    except WebSocketDisconnect:
        logger.info(f"[ws] Client disconnected for search {search_id}")
    except Exception as e:
        logger.error(f"[ws] Error for search {search_id}: {e}", exc_info=True)
        try:
            await websocket.send_text(json.dumps({
                "search_id": search_id,
                "step": "Error",
                "percent": 0,
                "done": True,
                "error": str(e),
            }))
        except Exception:
            pass
    finally:
        clear_progress(search_id)
        try:
            await websocket.close()
        except Exception:
            pass
