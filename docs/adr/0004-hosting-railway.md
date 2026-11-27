# ADR 0004: Host api, worker, Postgres and Redis on Railway

Status: Accepted (2026-11-27)
Context: The plan defaulted to Fly.io plus Neon and Upstash. For a single-developer demo stage we want the fewest accounts and moving parts.
Decision: One Railway project holds the `api` and `worker` services (built from `infra/docker/*.Dockerfile`), Postgres and Redis, on private networking. Railway deploys from GitHub on push; the api runs `alembic upgrade head` as its pre-deploy command and must pass the `/readyz` healthcheck. The web app stays on Vercel. CI (`.github/workflows/ci.yml`) remains the merge gate.
Consequences: No Fly configs or deploy workflow in the repo; service settings live in the Railway dashboard. Terraform still describes Neon/Upstash/R2/Vercel and should be reduced to R2 and Vercel when object storage is needed. Revisit Fly if global low-latency live timing or scale requires it.
