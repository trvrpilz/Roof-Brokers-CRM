FROM python:3.12-slim AS unpack

WORKDIR /unpack
COPY .staging/runtime /unpack/chunks
COPY .staging/auth31 /unpack/auth31
COPY .staging/hardening32 /unpack/hardening32
COPY .staging/pilotfix32 /unpack/pilotfix32
COPY .staging/fieldux33/apply.py /unpack/fieldux33_apply.py
COPY .staging/authreset33/apply.py /unpack/authreset33_apply.py
COPY .staging/authreset33/hash_patch.py /unpack/authreset33_hash_patch.py
COPY .staging/repux331 /unpack/repux331
COPY .staging/pipeline34/apply.py /unpack/pipeline34_apply.py
COPY .staging/authzprobe/apply.py /unpack/authzprobe_apply.py
RUN cat /unpack/chunks/part-* | base64 -d > /tmp/roof-brokers-runtime.zip \
    && echo "a574c2ac67cf6e9dd00713b06d4f6942d0519f7be44b9cb1f029dc20ea14bd3d  /tmp/roof-brokers-runtime.zip" | sha256sum -c - \
    && cat /unpack/auth31/part-* | base64 -d > /tmp/roof-brokers-auth31.zip \
    && echo "56c80f162f355460b679ef2f3c1c015c56f57b0f79ab20ea4c3f19519b1baec3  /tmp/roof-brokers-auth31.zip" | sha256sum -c - \
    && cat /unpack/hardening32/part-* | base64 -d > /tmp/roof-brokers-hardening32.zip \
    && echo "66f8e627c68f358b196ec3692ac27029d298d2f96bdc04b6a55a30b3a73f61b5  /tmp/roof-brokers-hardening32.zip" | sha256sum -c - \
    && cat /unpack/pilotfix32/part-00 /unpack/pilotfix32/part-01 /unpack/pilotfix32/part-02 /unpack/pilotfix32/part-03a /unpack/pilotfix32/part-03b /unpack/pilotfix32/part-03c /unpack/pilotfix32/part-03d /unpack/pilotfix32/part-04 /unpack/pilotfix32/part-05 /unpack/pilotfix32/part-06 | base64 -d > /tmp/roof-brokers-pilotfix32.zip \
    && echo "c8de7a6fb5bf78da77387217dabdcb2e9d12edea9d6382c8d8422b7d7ff5fffc  /tmp/roof-brokers-pilotfix32.zip" | sha256sum -c - \
    && echo "afdc4a78f3a86f04dcc97f88b2472b37966012b61e2a939f1632cd286192eb6b  /unpack/fieldux33_apply.py" | sha256sum -c - \
    && python -c "import hashlib,pathlib; p=pathlib.Path('/unpack/authreset33_apply.py').read_bytes(); assert hashlib.sha1(f'blob {len(p)}\\0'.encode()+p).hexdigest() == '6618622065d95c39d07c21ee1edd34da6ed33db9'" \
    && echo "0a1cadd241d716645e87e18624fdd9f162521c4e290e6fcea81e84bdc3895835  /unpack/authreset33_hash_patch.py" | sha256sum -c - \
    && cat /unpack/repux331/part-00 /unpack/repux331/part-01 /unpack/repux331/part-02 /unpack/repux331/part-03a /unpack/repux331/part-03b /unpack/repux331/part-04a /unpack/repux331/part-04b /unpack/repux331/part-05a /unpack/repux331/part-05b /unpack/repux331/part-06a /unpack/repux331/part-06b | base64 -d > /tmp/roof-brokers-repux331.zip \
    && echo "139be9d6efc1058f93ca958bf6b235a6b5b15baa1b31699bc841d7d122caf843  /tmp/roof-brokers-repux331.zip" | sha256sum -c - \
    && mkdir -p /runtime \
    && python -m zipfile -e /tmp/roof-brokers-runtime.zip /runtime \
    && python -m zipfile -e /tmp/roof-brokers-auth31.zip /runtime \
    && python -m zipfile -e /tmp/roof-brokers-hardening32.zip /runtime \
    && python -m zipfile -e /tmp/roof-brokers-pilotfix32.zip /runtime \
    && python /unpack/fieldux33_apply.py \
    && python /unpack/authreset33_apply.py \
    && python /unpack/authreset33_hash_patch.py \
    && python -m zipfile -e /tmp/roof-brokers-repux331.zip /runtime \
    && python /unpack/pipeline34_apply.py \
    && python /unpack/authzprobe_apply.py \
    && python -m compileall -q /runtime/backend/app /runtime/backend/scripts

FROM python:3.12-slim

WORKDIR /srv/backend
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/srv/backend

COPY --from=unpack /runtime/backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir psycopg2-binary==2.9.11

COPY --from=unpack /runtime/backend/app ./app
COPY --from=unpack /runtime/backend/alembic.ini ./alembic.ini
COPY --from=unpack /runtime/backend/alembic ./alembic
COPY railway/migrations/20261020_0003_webhook_retries.py ./alembic/versions/20261020_0003_webhook_retries.py
COPY railway/migrations/20261020_0004_offline_visit_idempotency.py ./alembic/versions/20261020_0004_offline_visit_idempotency.py
COPY railway/migrations/20261020_0005_webhook_scope_and_limits.py ./alembic/versions/20261020_0005_webhook_scope_and_limits.py
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
