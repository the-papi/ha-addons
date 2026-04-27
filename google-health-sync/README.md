# Google Health Sync

Bridges weight readings from a Home Assistant sensor to your Fitbit account
via the Google Health API. Designed for cases where you ingest a smart scale
locally (e.g. via the `xiaomi_ble` integration) but want the data to also
land in the Fitbit ecosystem.

## How it works
Scale (BLE) → HA sensor
↓ HA automation on state change
↓ rest_command POSTs to add-on
this add-on (Python aiohttp service)
↓ Google OAuth 2.0 refresh
↓ POST to https://health.googleapis.com/v4/users/me/dataTypes/weight/dataPoints
Fitbit account

## One-time setup

### 1. Google Cloud OAuth

1. Go to https://console.cloud.google.com/ and create a project.
2. Enable the **Google Health API**.
3. Configure the OAuth consent screen:
   - **User type:** External, leave in *Testing* (no verification needed for
     personal use under 100 users).
   - **Test users:** add the Google account linked to your Fitbit account.
   - **Scopes:** add
     `.../auth/googlehealth.health_metrics_and_measurements`.
4. Create an OAuth Client ID:
   - **Application type:** Web application
   - **Authorized redirect URIs:** `http://localhost:8765/callback`
5. Download the `client_secret.json` file.

### 2. Mint a refresh token

On your local machine (any OS with Python 3.12+):

\`\`\`bash
git clone https://github.com/YOURUSER/ha-google-health-sync
cd ha-google-health-sync
uv sync                                      # or: pip install aiohttp
cp ~/Downloads/client_secret_*.json client_secret.json
uv run python auth.py
\`\`\`

A browser opens, you approve, `tokens.json` lands in the directory.

### 3. Place files on Home Assistant

Copy these files to `/share/google-health-sync/` on your HA host (via the
Samba add-on, SCP, or the File editor add-on):

- `client_secret.json`
- `tokens.json`

### 4. Configure & start the add-on

- Open the add-on **Configuration** tab.
- Set `shared_secret` to a random value (e.g. `openssl rand -hex 32`).
- Save.
- **Info** tab → toggle **Watchdog** and **Start on boot** → **Start**.
- **Log** tab → confirm `Listening on 0.0.0.0:8766`.

### 5. Wire up Home Assistant

Add to `configuration.yaml`:

\`\`\`yaml
rest_command:
  google_health_sync_push:
    url: "http://HOSTNAME:8766/weight"
    method: POST
    headers:
      X-Shared-Secret: !secret google_health_sync_secret
      Content-Type: "application/json"
    payload: >
      {"weight_kg": {{ weight }}, "time": "{{ time }}"}

automation:
  - alias: "Sync weight to Fitbit"
    trigger:
      - platform: state
        entity_id: sensor.YOUR_SCALE_WEIGHT
        not_to: ["unavailable", "unknown"]
    condition:
      - condition: template
        value_template: "{{ states('sensor.YOUR_SCALE_WEIGHT') | float(0) > 20 }}"
    action:
      - service: rest_command.google_health_sync_push
        data:
          weight: "{{ states('sensor.YOUR_SCALE_WEIGHT') | float }}"
          time: "{{ utcnow().strftime('%Y-%m-%dT%H:%M:%SZ') }}"
\`\`\`

`secrets.yaml`:

\`\`\`yaml
google_health_sync_secret: "match-the-add-on-config-value"
\`\`\`

`HOSTNAME` is shown on the add-on **Info** tab as **Hostname** (e.g.
`local_google_health_sync`). If unsure, `homeassistant.local:8766` works
because the port is mapped.

## Caveats

- **Refresh tokens in Testing mode expire after 7 days.** Either click
  *Publish app* in the OAuth consent screen (your scopes are below the
  verification threshold for personal use), or re-run `auth.py` weekly.
- **Google Health API is in migration** until end of May 2026. Field
  names may shift. If a write fails with "unknown field", check the
  current schema at
  https://developers.google.com/health/reference/rest/v4/users.dataTypes.dataPoints
  and update the payload.

## Troubleshooting

- Add-on won't start → check the **Log** tab; usually missing files in
  `/share/google-health-sync/` or unset `shared_secret`.
- HA returns 502 from `rest_command` → check the add-on log; usually
  expired refresh token (re-mint) or schema drift.
- Hit `http://homeassistant.local:8766/healthz` — should return `ok`.

