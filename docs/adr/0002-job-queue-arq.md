# ADR 0002: Arq for background jobs

Status: Accepted (2026-10-29)
Context: We need durable scheduled jobs with retries, async-native code, and Redis only.
Decision: Arq. Celery was rejected for sync-first design and operational weight.
Consequences: Cron is minute-granular; long jobs need explicit timeouts; no built-in dead-letter queue, so failed runs are recorded in `ingestion_runs` and alerted on.
