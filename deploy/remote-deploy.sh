#!/usr/bin/env bash
# Runs ON the EC2 box, piped in over SSH by .github/workflows/deploy.yml.
# It never touches .env or backend/.env: those are created once on the server
# and are git-ignored, so they survive every deploy.
set -euo pipefail

APP_DIR="${APP_DIR:-$HOME/Finince-POC}"
BRANCH="${BRANCH:-dev}"

cd "$APP_DIR"

echo "==> Updating $APP_DIR to origin/$BRANCH"
git fetch origin "$BRANCH"
# --ff-only on purpose: if the server has diverged, fail loudly instead of
# silently discarding whatever is there.
git merge --ff-only "origin/$BRANCH"
echo "    now at $(git rev-parse --short HEAD) - $(git log -1 --pretty=%s)"

for env_file in .env backend/.env; do
  if [ ! -f "$env_file" ]; then
    echo "ERROR: $env_file is missing. Create it on this server first" >&2
    echo "       (see engineering_doc/local-setup.md)." >&2
    exit 1
  fi
done

echo "==> Building and starting containers"
docker compose up -d --build

echo "==> Waiting for the app to answer"
for attempt in $(seq 1 30); do
  if curl -fsS -m 5 http://localhost/health >/dev/null 2>&1; then
    echo "    healthy after ${attempt} attempt(s)"
    docker compose ps
    echo "==> Removing images left behind by this build"
    docker image prune -f >/dev/null
    exit 0
  fi
  sleep 2
done

echo "ERROR: /health did not answer within 60s. Recent backend logs:" >&2
docker compose logs --tail 40 backend >&2
exit 1
