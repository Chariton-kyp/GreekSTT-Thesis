"""WebSocket support for real-time progress updates."""

from .manager import TranscriptionProgressManager
from .events import register_websocket_events

__all__ = ['TranscriptionProgressManager', 'register_websocket_events']