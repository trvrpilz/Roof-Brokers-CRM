FROM python:3.12-slim AS unpack

WORKDIR /unpack
COPY .staging/runtime /unpack/chunks
RUN cat /unpack/chunks/part-* | base64 -d > /tmp/roof-brokers-runtime.zip \
    && echo "a574c2ac67cf6e9dd00713b06d4f6942d0519f7be44b9cb1f029dc20ea14bd3d  /tmp/roof-brokers-runtime.zip" | sha256sum -c - \
    && mkdir -p /runtime \
    && python -m zipfile -e /tmp/roof-brokers-runtime.zip /runtime

FROM python:3.12-slim

WORKDIR /srv/backend
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY --from=unpack /runtime/backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir psycopg2-binary==2.9.11

COPY --from=unpack /runtime/backend/app ./app
COPY --from=unpack /runtime/backend/alembic.ini ./alembic.ini
COPY --from=unpack /runtime/backend/alembic ./alembic
COPY --from=unpack /runtime/backend/scripts ./scripts
COPY --from=unpack /runtime/backend/run.sh ./run.sh
COPY --from=unpack /runtime/web /srv/web

RUN useradd -r -u 10001 roofbrokers \
    && mkdir -p /data/media /data/backups \
    && chmod +x ./run.sh \
    && chown -R roofbrokers:roofbrokers /data /srv

USER roofbrokers
EXPOSE 8000
CMD ["./run.sh"]
