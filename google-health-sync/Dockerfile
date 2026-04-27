ARG BUILD_FROM
FROM $BUILD_FROM

RUN apk add --no-cache python3 py3-pip \
    && pip install --break-system-packages --no-cache-dir aiohttp

COPY google_health_sync.py /google_health_sync.py
COPY run.sh /run.sh
RUN chmod a+x /run.sh

CMD ["/run.sh"]
