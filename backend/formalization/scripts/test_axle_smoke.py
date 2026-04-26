from __future__ import annotations

import asyncio

from formalization.axle_client import get_axle_client
from formalization.config import formalization_settings


async def main() -> None:
    if not formalization_settings.axle_api_key:
        raise SystemExit("AXLE_API_KEY is required for live AXLE smoke test")

    client = get_axle_client()
    try:
        result = await client.call(
            "check",
            content="import Mathlib\n\nexample : 1 + 1 = 2 := by\n  norm_num\n",
            environment=formalization_settings.formalization_lean_environment,
            mathlib_options=True,
            timeout_seconds=formalization_settings.axle_timeout_seconds,
        )
    finally:
        await client.close()
    assert result["okay"] is True, result
    print("axle smoke ok")


if __name__ == "__main__":
    asyncio.run(main())
