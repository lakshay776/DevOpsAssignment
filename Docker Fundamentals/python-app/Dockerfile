# -slim drops the build toolchain and docs from the full python image.
FROM python:3.12-slim

WORKDIR /srv

# requirements.txt is copied on its own first: this layer is only rebuilt
# when the dependencies change, so editing app.py reuses the cached install.
COPY requirements.txt .
# --no-cache-dir keeps pip's download cache out of the image layer.
RUN pip install --no-cache-dir -r requirements.txt

# Source is copied after the install so it sits in the cheap top layer.
COPY app.py .

# Unbuffered stdout, otherwise Flask's log lines sit in a buffer and never
# reach `docker logs` until the process exits.
ENV PYTHONUNBUFFERED=1

EXPOSE 5000

# -slim has no non-root user of its own, so create one. 5000 is above 1024,
# so binding it does not need root.
RUN useradd --create-home --shell /bin/bash appuser
USER appuser

CMD ["python", "app.py"]
