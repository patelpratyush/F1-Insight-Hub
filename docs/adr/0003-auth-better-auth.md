# ADR 0003: Better Auth in Next.js with JWT verification in the api

Status: Accepted (2026-10-29)
Decision: Better Auth owns sessions and users (schema `auth`). Its `jwt` plugin issues short-lived tokens, and the api verifies them against the JWKS endpoint.
Consequences: The api never touches passwords. Key rotation is handled by JWKS caching (5 min) with a forced refresh on unknown `kid`.
