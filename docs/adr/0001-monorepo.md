# ADR 0001: Monorepo with pnpm/Turborepo and a uv workspace

Status: Accepted (2026-10-29)

## Context
Web (TypeScript) and data services (Python) must share one typed contract and ship together.

## Decision
One repository. Turborepo orchestrates TypeScript packages. A uv workspace orchestrates Python packages. The OpenAPI spec exported by the api is the single source of the TS client.

## Consequences
CI must cache both toolchains. Contributors need Node 22 and uv installed.
