#!/usr/bin/env bash
# Local version of the pipeline's security gates (module 08).
# Each stage must pass before the next one runs; the first failure stops
# everything, so an image is only "allowed to push" when all gates pass.
#
# Usage: ./security-gate.sh <path-to-demo-app> <image-tag>
# Tools run from Docker images, so only Docker is needed on the host.
set -uo pipefail

APP_DIR=$(cd "${1:?app dir}" && pwd)
IMAGE=${2:?image tag}
PY=python:3.12-slim

stage() { printf '\n== %s\n' "$1"; }
stop()  { printf '\nGATE FAILED at: %s -> STOP (nothing is pushed or deployed)\n' "$1"; exit 1; }

stage "1. Unit tests (pytest)"
docker run --rm -v "$APP_DIR":/src -w /src $PY sh -c \
  "pip install -q --root-user-action=ignore --disable-pip-version-check -r requirements-dev.txt \
   && python -m pytest -q -p no:cacheprovider" | tail -1 || stop "unit tests"

stage "2. SAST (bandit, block on MEDIUM and above)"
docker run --rm -v "$APP_DIR":/src -w /src $PY sh -c \
  "pip install -q --root-user-action=ignore --disable-pip-version-check bandit \
   && bandit -r app -q --severity-level medium -f custom \
      --msg-template '{relpath}:{line} {test_id} [{severity}] {msg}'" || stop "SAST"
echo "no MEDIUM/HIGH findings"

stage "3. SCA (pip-audit on runtime + dev requirements)"
docker run --rm -v "$APP_DIR":/src -w /src $PY sh -c \
  "pip install -q --root-user-action=ignore --disable-pip-version-check pip-audit \
   && pip-audit -r requirements-dev.txt" || stop "SCA"

stage "4. Docker build"
docker build -q -t "$IMAGE" "$APP_DIR" || stop "docker build"

stage "5. Image scan (Trivy, block on HIGH/CRITICAL)"
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  -v "${TRIVY_CACHE:-$HOME/.cache/trivy}":/root/.cache/trivy aquasec/trivy \
  image -q --severity HIGH,CRITICAL --exit-code 1 "$IMAGE" | grep -E '^Total' \
  ; [ "${PIPESTATUS[0]}" -eq 0 ] || stop "image scan"
echo "no HIGH/CRITICAL vulnerabilities"

printf '\nALL GATES PASSED -> %s may be pushed and deployed\n' "$IMAGE"
