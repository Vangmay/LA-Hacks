from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from formalization.config import formalization_settings

logger = logging.getLogger(__name__)


def _to_plain(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(k): _to_plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_to_plain(v) for v in value]
    annotations = getattr(value, "__annotations__", None)
    if isinstance(annotations, dict):
        return {name: _to_plain(getattr(value, name, None)) for name in annotations}
    if hasattr(value, "model_dump"):
        return value.model_dump()
    return str(value)


def normalize_axle_error(exc: Exception) -> dict[str, Any]:
    name = exc.__class__.__name__
    payload: dict[str, Any] = {
        "error_type": name,
        "message": str(exc),
    }
    for attr in ("status", "status_code", "response", "body"):
        if hasattr(exc, attr):
            payload[attr] = _to_plain(getattr(exc, attr))
    return payload


class AxleClientWrapper:
    def __init__(self) -> None:
        self._client: Any = None

    async def _get_client(self) -> Any:
        if self._client is None:
            try:
                from axle import AxleClient
            except ModuleNotFoundError as exc:
                raise RuntimeError(
                    "axiom-axle is not installed. Run `python -m pip install axiom-axle`."
                ) from exc

            kwargs = {
                "url": formalization_settings.axle_api_url,
                "max_concurrency": formalization_settings.axle_max_concurrency,
                "base_timeout_seconds": formalization_settings.axle_timeout_seconds,
            }
            if formalization_settings.axle_api_key:
                kwargs["api_key"] = formalization_settings.axle_api_key
            self._client = AxleClient(**kwargs)
            if hasattr(self._client, "__aenter__"):
                self._client = await self._client.__aenter__()
        return self._client

    async def call(self, method_name: str, **kwargs: Any) -> dict[str, Any]:
        client = await self._get_client()
        method: Callable[..., Awaitable[Any]] = getattr(client, method_name)
        logger.info("AXLE %s started", method_name)
        try:
            result = await method(**kwargs)
        except Exception as exc:  # noqa: BLE001
            logger.warning("AXLE %s failed: %s", method_name, exc)
            raise
        logger.info("AXLE %s complete", method_name)
        return _to_plain(result)

    async def close(self) -> None:
        client = self._client
        self._client = None
        if client is not None and hasattr(client, "__aexit__"):
            await client.__aexit__(None, None, None)


_wrapper = AxleClientWrapper()


def get_axle_client() -> AxleClientWrapper:
    return _wrapper
