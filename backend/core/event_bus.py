import asyncio
from typing import AsyncIterator, Optional, Dict, List

from models import DAGEvent


class EventBus:
    def __init__(self) -> None:
        self._channels: Dict[str, List[asyncio.Queue]] = {}
        self._history: Dict[str, List[DAGEvent]] = {}

    def create_channel(self, job_id: str) -> None:
        if job_id not in self._channels:
            self._channels[job_id] = []
            self._history[job_id] = []

    def channel_exists(self, job_id: str) -> bool:
        return job_id in self._channels

    async def publish(self, job_id: str, event: DAGEvent) -> None:
        if job_id not in self._channels:
            self.create_channel(job_id)
        self._history[job_id].append(event)
        for q in list(self._channels[job_id]):
            await q.put(event)

    async def subscribe(
        self,
        job_id: str,
        last_event_id: Optional[str] = None,
    ) -> AsyncIterator[DAGEvent]:
        if job_id not in self._channels:
            self.create_channel(job_id)

        queue: asyncio.Queue = asyncio.Queue()
        history = list(self._history.get(job_id, []))

        # Replay history (from after last_event_id if provided)
        replay_from = 0
        if last_event_id:
            for i, ev in enumerate(history):
                if ev.event_id == last_event_id:
                    replay_from = i + 1
                    break

        for ev in history[replay_from:]:
            yield ev

        self._channels[job_id].append(queue)
        try:
            while True:
                ev = await queue.get()
                yield ev
        finally:
            if queue in self._channels.get(job_id, []):
                self._channels[job_id].remove(queue)

    def close_channel(self, job_id: str) -> None:
        self._channels.pop(job_id, None)
        self._history.pop(job_id, None)


event_bus = EventBus()
