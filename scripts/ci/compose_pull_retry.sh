#!/usr/bin/env bash
set -euo pipefail

# Retry docker compose pull for CI registry rate limits (Docker Hub, ECR Public, Quay).
# Usage: scripts/ci/compose_pull_retry.sh [service ...]

max_attempts="${COMPOSE_PULL_RETRIES:-5}"
delay_seconds="${COMPOSE_PULL_RETRY_DELAY_SECONDS:-15}"

if [ "$#" -eq 0 ]; then
  echo "compose_pull_retry: at least one service name is required" >&2
  exit 1
fi

for ((attempt = 1; attempt <= max_attempts; attempt++)); do
  if docker compose pull "$@"; then
    echo "compose_pull_retry: pull succeeded on attempt ${attempt}"
    exit 0
  fi

  if [ "$attempt" -eq "$max_attempts" ]; then
    echo "compose_pull_retry: pull failed after ${max_attempts} attempts" >&2
    exit 1
  fi

  echo "compose_pull_retry: attempt ${attempt} failed; sleeping ${delay_seconds}s..."
  sleep "${delay_seconds}"
  delay_seconds=$((delay_seconds * 2))
done
