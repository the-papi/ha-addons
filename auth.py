"""One-shot OAuth consent flow. Run once, get refresh_token saved to tokens.json."""
import asyncio
import json
import secrets
import urllib.parse
import webbrowser
from pathlib import Path

from aiohttp import ClientSession, web

CLIENT_SECRET_FILE = Path("client_secret.json")
TOKEN_FILE = Path("tokens.json")
REDIRECT_URI = "http://localhost:8765/callback"
SCOPES = [
    "https://www.googleapis.com/auth/googlehealth.health_metrics_and_measurements",
]


def load_client_config() -> tuple[str, str]:
    cfg = json.loads(CLIENT_SECRET_FILE.read_text())
    block = cfg.get("web") or cfg.get("installed")
    if not block:
        raise SystemExit("client_secret.json missing 'web' or 'installed' block")
    return block["client_id"], block["client_secret"]


async def main() -> None:
    client_id, client_secret = load_client_config()
    state_token = secrets.token_urlsafe(16)
    result: dict[str, object] = {}

    async def callback(request: web.Request) -> web.Response:
        if request.query.get("state") != state_token:
            return web.Response(text="State mismatch", status=400)
        if err := request.query.get("error"):
            result["done"] = True
            return web.Response(text=f"OAuth error: {err}", status=400)
        code = request.query.get("code")
        if not code:
            return web.Response(text="No code in callback", status=400)

        async with ClientSession() as session:
            async with session.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": REDIRECT_URI,
                    "grant_type": "authorization_code",
                },
            ) as resp:
                tokens = await resp.json()

        if "refresh_token" not in tokens:
            result["done"] = True
            return web.Response(
                text=(
                    f"No refresh_token in response: {tokens}\n\n"
                    "Revoke at https://myaccount.google.com/permissions and retry."
                ),
                status=400,
            )

        TOKEN_FILE.write_text(json.dumps({"refresh_token": tokens["refresh_token"]}))
        TOKEN_FILE.chmod(0o600)
        result["done"] = True
        return web.Response(
            text=f"Got refresh_token. Saved to {TOKEN_FILE}. You can close this tab."
        )

    app = web.Application()
    app.router.add_get("/callback", callback)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "localhost", 8765)
    await site.start()

    auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "state": state_token,
    })
    print(f"Opening browser to:\n{auth_url}\n")
    webbrowser.open(auth_url)

    while not result.get("done"):
        await asyncio.sleep(0.2)
    await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
