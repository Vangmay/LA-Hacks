from __future__ import annotations

import anyio
from sse_starlette.sse import AppStatus, EventSourceResponse


class LoopSafeEventSourceResponse(EventSourceResponse):
    """EventSourceResponse variant that does not reuse an anyio.Event across loops.

    The upstream response stores a shutdown event on a process-global AppStatus.
    Starlette's TestClient creates separate event loops for separate stream
    contexts, which can bind that global event to the first loop and fail later
    streams. Runtime stream completion and disconnect handling are still managed
    by EventSourceResponse's other tasks.
    """

    @staticmethod
    async def _listen_for_exit_signal() -> None:
        while not AppStatus.should_exit:
            await anyio.sleep(3600)
