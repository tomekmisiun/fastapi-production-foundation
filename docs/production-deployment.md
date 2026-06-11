# Production Deployment Guide

This template is a reusable FastAPI backend foundation. It is not tied to one
business domain or one hosting provider. Adapt the deployment target to the
project, but keep the operational contract below.

## Supported Deployment Shape

The production runtime should provide these independently managed services:

- API process running the FastAPI application.
- Worker process running `python -m app.worker`.
- PostgreSQL database.
- Redis instance.
- S3-compatible object storage.
- SMTP or replaceable email delivery provider.
- Metrics, logs, and alerting stack.

The local Docker Compose files are development-oriented. Production can use
Kubernetes, a PaaS, container services, or Docker on a VM, but the deployment
must preserve the same process and dependency boundaries.

## Environments

Use separate environments for local development, staging, and production.

- `development`: local developer workflow with Docker Compose or uv.
- `test`: automated tests and CI.
- `staging`: production-like validation before release.
- `production`: real traffic and real customer data.

Required expectations:

- Staging and production use separate databases, Redis instances, buckets, and
  email credentials.
- Staging should run the same image version that will be promoted to
  production.
- Production must set `ENVIRONMENT=production`.
- Production secrets must not come from committed files.
- Production deploys must not mount the source tree into the runtime container.

## Secrets

Use a real secret manager or deployment-platform secret store for production.
Examples include cloud secret managers, Kubernetes Secrets backed by sealed or
external secrets, or a PaaS secret store.

Production secrets include:

- `SECRET_KEY`
- database URL and credentials
- Redis credentials if required by the provider
- SMTP credentials
- S3 access keys
- Grafana and observability credentials

Rules:

- Never commit `.env` files with real values.
- Rotate secrets through the deployment platform, not through code changes.
- Keep a documented emergency rotation procedure for `SECRET_KEY`, database
  credentials, S3 credentials, and email credentials.
- Treat `SECRET_KEY` rotation as a breaking session/token event unless a
  key-ring strategy is added in the future.

## Deployment Flow

Use this flow for normal releases:

1. Merge feature branches into `main` with a non-fast-forward merge commit.
2. Ensure CI passes on `main`.
3. Build a deployable image from the merge commit SHA.
4. Tag the image with the commit SHA and, if useful, a release tag.
5. Deploy the image to staging.
6. Run staging migrations with `alembic upgrade head`.
7. Run smoke checks in staging:
   - `GET /health/live`
   - `GET /health/ready`
   - `GET /metrics`
   - login or another authenticated smoke path
   - worker startup and queue connectivity
8. Promote the same image to production.
9. Run production migrations according to the migration strategy.
10. Shift traffic to the new API process.
11. Verify production health, metrics, logs, and worker status.
12. Keep the previous image available until the release is accepted.

## Migration Strategy

Alembic migrations are required for every database schema change.

Default migration order:

1. Backup or confirm a recent restorable backup exists.
2. Deploy code that is compatible with both the old and new schema when
   possible.
3. Run `alembic upgrade head`.
4. Verify readiness and application smoke checks.
5. Remove old compatibility code in a later release when needed.

For risky changes, prefer expand/contract migrations:

- First release: add nullable columns, new tables, or backward-compatible
  indexes.
- Backfill data separately when needed.
- Second release: switch reads/writes to the new shape.
- Later release: drop old columns or constraints.

Do not make destructive migrations without an explicit rollback and restore
plan.

## Rollback Strategy

Application rollback:

- Keep the previous production image tag available.
- Roll back to the previous image when the new release fails before or after
  traffic shift.
- Verify `GET /health/ready`, logs, metrics, and core auth flow after rollback.

Database rollback:

- Prefer forward-fix migrations over down migrations for production incidents.
- Use database restore only when data corruption or destructive schema changes
  require it.
- Test restore procedures outside production before relying on them.

Rollback checklist:

- Identify whether the incident is app-only, schema-related, data-related, or
  dependency-related.
- Stop or pause affected workers if they may worsen data state.
- Roll back app image or deploy a forward fix.
- Confirm database compatibility.
- Verify health checks and key user flows.
- Document the incident and follow-up actions.

## Backup And Restore

Production PostgreSQL must have automated backups. The exact mechanism depends
on the hosting provider, but the project using this template should document:

- backup frequency
- retention period
- encryption at rest
- restore target
- recovery point objective
- recovery time objective
- restore rehearsal cadence

Minimum expectation:

- daily backups for non-critical projects
- more frequent backups for SaaS projects with customer data
- a restore rehearsal before first production launch
- periodic restore rehearsals after launch

Object storage should also have a retention and deletion policy. If uploaded
files are business-critical, verify that bucket versioning or equivalent
recovery exists.

## Health And Smoke Checks

Use these endpoints in deployment automation:

- `GET /health/live` for process liveness.
- `GET /health/ready` before receiving traffic.
- `GET /health/db` when debugging database connectivity.
- `GET /health/redis` when debugging Redis connectivity.
- `GET /metrics` for Prometheus scraping.

Readiness must pass before a new API instance receives traffic.

Recommended post-deploy smoke checks:

- register/login or a project-specific auth flow
- authenticated `GET /auth/me`
- worker can connect to Redis
- API can connect to object storage if file uploads are enabled
- logs and metrics are visible

## Operational Ownership

Before using this template for a real project, define:

- deployment platform
- production domain and TLS termination
- secret manager
- backup provider and restore process
- alert destinations
- incident owner
- rollback owner
- database migration owner
- expected service-level indicators

## Current Template Limits

This guide defines the production operating model, but the repository still
does not include provider-specific infrastructure as code, production CI/CD
deployment jobs, alert rules, error tracking, tracing, or automated
backup/restore verification.
