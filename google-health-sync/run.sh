#!/usr/bin/with-contenv bashio

export GOOGLE_CLIENT_ID=$(bashio::config 'client_id')
export GOOGLE_CLIENT_SECRET=$(bashio::config 'client_secret')
export GOOGLE_REFRESH_TOKEN=$(bashio::config 'refresh_token')
export SHARED_SECRET=$(bashio::config 'shared_secret')
export LOG_LEVEL=$(bashio::config 'log_level')
export LISTEN_HOST=0.0.0.0
export LISTEN_PORT=8766
export PYTHONUNBUFFERED=1

bashio::log.info "Starting google-health-sync..."

if [ -z "$GOOGLE_CLIENT_ID" ]; then
    bashio::log.fatal "client_id is not set in add-on config"
    exit 1
fi
if [ -z "$GOOGLE_CLIENT_SECRET" ]; then
    bashio::log.fatal "client_secret is not set in add-on config"
    exit 1
fi
if [ -z "$GOOGLE_REFRESH_TOKEN" ]; then
    bashio::log.fatal "refresh_token is not set in add-on config (run auth.py locally to get one)"
    exit 1
fi
if [ -z "$SHARED_SECRET" ]; then
    bashio::log.fatal "shared_secret is not set in add-on config"
    exit 1
fi

exec python3 /google_health_sync.py
