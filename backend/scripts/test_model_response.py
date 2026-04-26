"""Quick check that the configured model actually responds via the
OpenAI-compatible OpenRouter endpoint.

It uses the same settings/env the app loads, then makes one chat call
with and without JSON mode so you can tell whether the failure is the
model id, the key, the base url, or json-mode support.

Usage:
    python backend/scripts/test_model_response.py
    python backend/scripts/test_model_response.py --model google/gemini-3-flash
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

import dotenv
import httpx
from openai import APIConnectionError, APIStatusError, AsyncOpenAI

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
dotenv.load_dotenv(ROOT / ".env")

from config import settings  # noqa: E402


async def call_once(
    client: AsyncOpenAI,
    model: str,
    *,
    json_mode: bool,
) -> tuple[bool, str]:
    kwargs = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Reply with the literal string requested."},
            {
                "role": "user",
                "content": (
                    'Return JSON exactly: {"ok": true}'
                    if json_mode
                    else "Reply with: API key works"
                ),
            },
        ],
        "max_tokens": 64,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    try:
        resp = await client.chat.completions.create(**kwargs)
    except APIStatusError as exc:
        return False, f"HTTP {exc.status_code}: {exc.message}"
    except APIConnectionError as exc:
        return False, f"connection error: {exc}"
    except Exception as exc:  # noqa: BLE001
        return False, f"{type(exc).__name__}: {exc}"
    content = (resp.choices[0].message.content or "").strip()
    return True, content


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=settings.openai_model)
    parser.add_argument("--base-url", default=settings.openai_base_url)
    parser.add_argument(
        "--api-key-env",
        default="OPEN_ROUTER_KEY",
        help="env var to read the API key from (default OPEN_ROUTER_KEY)",
    )
    args = parser.parse_args()

    api_key = os.getenv(args.api_key_env) or getattr(
        settings, args.api_key_env.lower(), ""
    )

    print(f"base_url    : {args.base_url}")
    print(f"model       : {args.model}")
    print(f"api_key_env : {args.api_key_env}")
    print(f"key set     : {'yes' if api_key else 'NO  <-- this will 401'}")
    print("-" * 60)

    if not api_key:
        return 1

    client = AsyncOpenAI(
        api_key=api_key,
        base_url=args.base_url or None,
        http_client=httpx.AsyncClient(timeout=30.0, follow_redirects=True),
    )

    try:
        ok, msg = await call_once(client, args.model, json_mode=False)
        print(f"plain call  : {'OK' if ok else 'FAIL'}")
        print(f"  -> {msg}")

        ok_json, msg_json = await call_once(client, args.model, json_mode=True)
        print(f"json mode   : {'OK' if ok_json else 'FAIL'}")
        print(f"  -> {msg_json}")
    finally:
        await client.close()

    if not ok:
        print("\nplain call failed — likely wrong model id, base_url, or key.")
        return 2
    if not ok_json:
        print(
            "\nplain works but json mode fails — your model probably does not "
            "support response_format=json_object on this endpoint. Switch to a "
            "OpenRouter model (e.g. google/gemini-3-flash) or stop using json mode."
        )
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
