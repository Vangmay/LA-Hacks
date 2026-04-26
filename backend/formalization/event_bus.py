from __future__ import annotations

import asyncio
from typing import AsyncIterator, Optional

from formalization.events import FormalizationEvent


class FormalizationEventBus:
    def __init__(self) -> None:
        self._channels: dict[str, list[asyncio.Queue]] = {}
        self._history: dict[str, list[FormalizationEvent]] = {}

    def create_channel(self, run_id: str) -> None:
        if run_id not in self._channels:
            self._channels[run_id] = []
            self._history[run_id] = []

    def channel_exists(self, run_id: str) -> bool:
        return run_id in self._channels

    async def publish(self, run_id: str, event: FormalizationEvent) -> None:
        if run_id not in self._channels:
            self.create_channel(run_id)
        self._history[run_id].append(event)
        for queue in list(self._channels[run_id]):
            await queue.put(event)

    async def subscribe(
        self,
        run_id: str,
        last_event_id: Optional[str] = None,
    ) -> AsyncIterator[FormalizationEvent]:
        if run_id not in self._channels:
            self.create_channel(run_id)

        queue: asyncio.Queue = asyncio.Queue()
        history = list(self._history.get(run_id, []))

        replay_from = 0
        if last_event_id:
            for index, event in enumerate(history):
                if event.event_id == last_event_id:
                    replay_from = index + 1
                    break

        for event in history[replay_from:]:
            yield event

        self._channels[run_id].append(queue)
        try:
            while True:
                yield await queue.get()
        finally:
            if queue in self._channels.get(run_id, []):
                self._channels[run_id].remove(queue)

    def close_channel(self, run_id: str) -> None:
        self._channels.pop(run_id, None)
        self._history.pop(run_id, None)


formalization_event_bus = FormalizationEventBus()
