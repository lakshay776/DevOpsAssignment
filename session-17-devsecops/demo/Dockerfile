# Alpine instead of Debian slim: the slim image carried 44 HIGH OS-package
# CVEs with no fixed version available, which failed the Trivy gate.
FROM python:3.12-alpine

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Pick up patched OS packages.
RUN apk upgrade --no-cache

COPY requirements.txt .

# pip is only needed at build time. Removing it afterwards also removes its
# vendored copies of urllib3/msgpack/setuptools, which Trivy flags.
RUN pip install --no-cache-dir -r requirements.txt \
    && pip uninstall -y pip

COPY app ./app

# Run as an unprivileged user instead of root.
RUN adduser -D -H -u 10001 appuser
USER 10001

EXPOSE 5001

# python runs as PID 1 and ignores SIGTERM, so `docker stop` / pod shutdown
# waited the full grace period (30s). Python does handle SIGINT.
STOPSIGNAL SIGINT

CMD ["python", "app/app.py"]
