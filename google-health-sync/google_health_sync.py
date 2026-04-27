"""HA → Google Health API weight bridge. Listens on HTTP, writes weight to Fitbit account."""
import asyncio
import json
import logging
import os
import time
import uuid
from pathlib import Path

from aiohttp import ClientSession, ClientTimeout, web
from datetime import datetime, timezone

# --- Config from environment ---
LISTEN_HOST = os.environ.get("LISTEN_HOST", "127.0.0.1")
LISTEN_PORT = int(os.environ.get("LISTEN_PORT", "8766"))

HEALTH_API = "https://health.googleapis.com/v4/users/me/dataTypes/weight/dataPoints"
TOKEN_URL = "https://oauth2.googleapis.com/token"

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "info").upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("google-health-sync")


class TokenManager:
    """Caches access tokens, refreshes lazily."""

    def __init__(self) -> None:
        self._access_token: str | None = None
        self._expires_at: float = 0.0
        self._lock = asyncio.Lock()
        self._client_id = os.environ["GOOGLE_CLIENT_ID"]
        self._client_secret = os.environ["GOOGLE_CLIENT_SECRET"]
        self._refresh_token = os.environ["GOOGLE_REFRESH_TOKEN"]

    async def get(self, session: ClientSession) -> str:
        async with self._lock:
            if self._access_token and time.time() < self._expires_at - 60:
                return self._access_token

            async with session.post(
                TOKEN_URL,
                data={
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "refresh_token": self._refresh_token,
                    "grant_type": "refresh_token",
                },
                timeout=ClientTimeout(total=10),
            ) as resp:
                body = await resp.json()
                if resp.status != 200:
                    raise RuntimeError(f"Token refresh failed ({resp.status}): {body}")

            self._access_token = body["access_token"]
            self._expires_at = time.time() + body.get("expires_in", 3600)
            log.info(
                "Refreshed access token, valid for %ds",
                body.get("expires_in", 3600),
            )
            return self._access_token


async def write_weight(
    session: ClientSession, tokens: TokenManager, weight_kg: float, iso_time: str
) -> None:
    """POST a weight data point. iso_time is RFC3339 with offset (e.g. 2026-04-27T18:30:00+02:00)."""
    access = await tokens.get(session)

    dt = datetime.fromisoformat(iso_time)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    # Send local-time RFC3339 (with offset embedded) as physicalTime.
    # Also send utcOffset separately as the docs require.
    physical_time_local = dt.strftime("%Y-%m-%dT%H:%M:%S%z")
    # %z gives +0200; convert to +02:00 for RFC3339 compliance
    physical_time_local = physical_time_local[:-2] + ":" + physical_time_local[-2:]
    offset_seconds = int(dt.utcoffset().total_seconds())

    payload = {
        "dataSource": {
            "recordingMethod": "ACTIVELY_MEASURED",
            "device": {
                "formFactor": "SCALE",
                "manufacturer": "Xiaomi",
                "displayName": "Mi Body Composition Scale 2",
            },
        },
        "weight": {
            "weightGrams": round(weight_kg * 1000),
            "sampleTime": {
                "physicalTime": physical_time_local,
                "utcOffset": f"{offset_seconds}s",
            },
        },
    }
    log.debug("Payload: %s", json.dumps(payload))
    async with session.post(
        GOOGLE_HEALTH_API,
        headers={
            "Authorization": f"Bearer {access}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        json=payload,
        timeout=ClientTimeout(total=15),
    ) as resp:
        body = await resp.json()
        if resp.status >= 300:
            raise RuntimeError(f"Health API write failed ({resp.status}): {body}")
        log.info(
            "Wrote weight=%s kg, physicalTime=%s, offset=%ds",
            weight_kg, physical_time_local, offset_seconds,
        )


async def handle_weight(request: web.Request) -> web.Response:
    if request.headers.get("X-Shared-Secret") != os.environ["SHARED_SECRET"]:
        return web.Response(status=401, text="bad secret")
    try:
        data = await request.json()
        weight = float(data["weight_kg"])
        iso_time = str(data["time"])
    except (KeyError, ValueError, TypeError, json.JSONDecodeError) as e:
        return web.Response(status=400, text=f"bad request: {e}")

    if not (20 <= weight <= 300):
        return web.Response(status=400, text="weight out of sane range")

    try:
        tokens: TokenManager = request.app["tokens"]
        async with ClientSession() as session:
            await write_weight(session, tokens, weight, iso_time)
    except Exception as e:
        log.exception("write failed")
        return web.Response(status=502, text=str(e))

    return web.json_response({"ok": True})


async def handle_health(_: web.Request) -> web.Response:
    return web.Response(text="ok")


def build_app() -> web.Application:
    app = web.Application()
    app["tokens"] = TokenManager()
    app.router.add_post("/weight", handle_weight)
    app.router.add_get("/healthz", handle_health)
    return app


def main() -> None:
    log.info("Listening on %s:%s", LISTEN_HOST, LISTEN_PORT)
    web.run_app(build_app(), host=LISTEN_HOST, port=LISTEN_PORT, print=None)


if __name__ == "__main__":
    main()
