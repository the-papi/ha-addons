# HA Google Health Sync

Home Assistant add-on repository.

This add-on bridges weight readings from a HA sensor (e.g. a Bluetooth body
composition scale exposed via the `xiaomi_ble` integration) to your Fitbit
account, by posting them to the Google Health API.

## Installation

1. In Home Assistant: **Settings → Add-ons → Add-on Store**.
2. Top-right ⋮ menu → **Repositories**.
3. Add: `https://github.com/the-papi/ha-google-health-sync`
4. Find **Google Health Sync** in the store and install it.

See [`google-health-sync/README.md`](./google-health-sync/README.md) for full
setup instructions (Google Cloud OAuth setup, minting a refresh token,
configuring HA).

## One-time auth setup

Before the add-on can run, you need a Google OAuth refresh token. The
`auth.py` script in this repo handles it. See the add-on README.

## License

MIT
