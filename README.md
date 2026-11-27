# F1 Insight Hub

Unofficial F1 analytics platform. Not affiliated with Formula 1.

## Quick start
    cp .env.example .env
    pnpm install && uv sync --all-packages
    make up
    set -a && . ./.env && set +a
    make migrate
    pnpm --filter @f1/web exec better-auth migrate --config src/lib/auth.ts -y
    uv run python apps/worker/scripts/seed_standings.py   # current season from Jolpica
    make api      # terminal 1
    make worker   # terminal 2
    make web      # terminal 3

Local S3-compatible storage is SeaweedFS (`s3` service, port 9000). Production uses Cloudflare R2.

Hosting: api, worker, Postgres and Redis on Railway (ADR 0004); web on Vercel.

See `docs/superpowers/specs` and `docs/superpowers/plans` for design and roadmap.
