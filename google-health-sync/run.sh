#!/usr/bin/with-contenv bashio

export SHARED_SECRET=$(bashio::config 'shared_secret')
export LOG_LEVEL=$(bashio::config 'log_level')
export CLIENT_SECRET_FILE=/share/google-health-sync/client_secret.json
export TOKEN_FILE=/share/google-health-sync/tokens.json
export LISTEN_HOST=0.0.0.0
export LISTEN_PORT=8766
export PYTHONUNBUFFERED=1

bashio::log.info "Starting google-health-sync..."

if [ ! -f "$CLIENT_SECRET_FILE" ]; then
    bashio::log.fatal "Missing $CLIENT_SECRET_FILE"
    bashio::log.fatal "Copy your Google OAuth client_secret.json to /share/google-health-sync/"
    exit 1
fi
if [ ! -f "$TOKEN_FILE" ]; then
    bashio::log.fatal "Missing $TOKEN_FILE"
    bashio::log.fatal "Run auth.py locally and copy tokens.json to /share/google-health-sync/"
    exit 1
fi
if [ -z "$SHARED_SECRET" ] || [ "$SHARED_SECRET" = "CHANGE_ME" ]; then
    bashio::log.fatal "Set shared_secret in the add-on configuration"
    exit 1
fi

exec python3 /google_health_sync.py
