#!/usr/bin/env bash
# Package the app into build/ with a small metadata file.
set -euo pipefail
rm -rf build
mkdir -p build
cp -R app build/
find build -name __pycache__ -type d -prune -exec rm -rf {} +
cat > build/build-info.txt <<INFO
Application: Session 16 Calculator
Commit: ${GITHUB_SHA:-local}
Built: $(date -u +%Y-%m-%dT%H:%M:%SZ)
INFO
echo "Build output:"
find build -type f | sort
