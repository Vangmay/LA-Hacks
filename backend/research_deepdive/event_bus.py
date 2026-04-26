"""In-process replaying event bus for research deep-dive runs."""
from __future__ import annotations

import asyncio
from collections import deque
from typing import AsyncIterator

from .events import DeepDiveEvent


class DeepDiveEventBus:
    def __init__(self, history_limit: int = 5000) -> None:
        self.history_limit = history_limit
        self._channels: dict[str, list[asyncio.Queue[DeepDiveEvent]]] = {}
        self._history: dict[str, deque[DeepDiveEvent]] = {}

    def create_channel(self, run_id: str) -> None:
        self._channels.setdefault(run_id, [])
        self._history.setdefault(run_id, deque(maxlen=self.history_limit))

    def channel_exists(self, run_id: str) -> bool:
        return run_id in self._channels or run_id in self._history

    def history(self, run_id: str) -> list[DeepDiveEvent]:
        return list(self._history.get(run_id, ()))

    async def publish(self, event: DeepDiveEvent) -> None:
        self.create_channel(event.run_id)
        self._history[event.run_id].append(event)
        for queue in list(self._channels.get(event.run_id, [])):
            queue.put_nowait(event)

    async def subscribe(
        self,
        run_id: str,
        last_event_id: str | None = None,
    ) -> AsyncIterator[DeepDiveEvent]:
        self.create_channel(run_id)
        history = list(self._history.get(run_id, ()))
        replay_from = 0
        if last_event_id:
            for idx, event in enumerate(history):
                if event.event_id == last_event_id:
                    replay_from = idx + 1
                    break

        for event in history[replay_from:]:
            yield event

        queue: asyncio.Queue[DeepDiveEvent] = asyncio.Queue()
        self._channels[run_id].append(queue)
        try:
            while True:
                yield await queue.get()
        finally:
            subscribers = self._channels.get(run_id, [])
            if queue in subscribers:
                subscribers.remove(queue)

    def close_subscribers(self, run_id: str) -> None:
        self._channels.pop(run_id, None)


deepdive_event_bus = DeepDiveEventBus()
