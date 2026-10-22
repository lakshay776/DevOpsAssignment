FROM python:3.13-slim

# Patch OS packages in the base image; Trivy flags these otherwise.
RUN apt-get update \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/*

# PYTHONUNBUFFERED, or log lines sit in a buffer and never reach
# `docker logs` / `kubectl logs`.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Dependencies install in one layer, directly.
#
# An earlier version of this file built wheels in a separate stage and copied
# them in. That left the wheels in their own layer, and `rm -rf /wheels`
# only whited them out in a later one - so superseded versions stayed in the
# image's layer history and Trivy kept reporting CVEs that `pip list` said
# were already fixed. Installing in place avoids the stale layer entirely.
#
# setuptools ships with the base image at a version Trivy flags and is not
# in requirements.txt, so it is upgraded in the same layer.
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip "setuptools>=78.1.1" \
    && pip install --no-cache-dir -r requirements.txt \
    # pip is removed once dependencies are in. It is not needed to run the
    # app, and its bundled copies of urllib3, msgpack and setuptools (listed
    # in pip/_vendor/vendor.txt) are what Trivy reports as vulnerable - the
    # versions the app actually imports are already patched. Dropping pip
    # clears those findings and removes a package manager from the runtime.
    && pip uninstall -y pip \
    && rm -rf /usr/local/lib/python3.13/site-packages/pip \
              /usr/local/lib/python3.13/site-packages/pip-*

COPY alembic.ini pytest.ini ./
COPY alembic ./alembic
COPY app ./app

# Run unprivileged. The port is 8000, so no root is needed to bind it.
RUN useradd --create-home --uid 10001 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Exec form, so uvicorn is PID 1 and receives SIGTERM directly on
# `docker stop` and on pod termination.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
