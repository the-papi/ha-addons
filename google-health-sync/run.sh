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

for v in GOOGLE_CLIENT_ID GOOGLE_CLIENT_SECRET GOOGLE_REFRESH_TOKEN SHARED_SECRET; do
    if [ -z "${!v}" ]; then
        bashio::log.fatal "$v is not set in add-on config"
        exit 1
    fi
done

exec python3 /google_health_sync.py

