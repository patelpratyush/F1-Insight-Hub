# Alert: ingestion lag

Trigger: `GET /v1/meta/freshness` reports `last_success_at` older than 2 hours for job `standings`
(checked every 5 minutes by the uptime monitor), or `last_status = failed` for 3 consecutive checks.

1. Open Sentry for `f1-worker` and find the latest `failed` ingestion error.
2. If upstream returns 429 or 5xx, wait: the circuit breaker retries after 60 s.
3. If the schema changed (parse error), fix `f1_worker.sources.jolpica` and redeploy the worker.
4. Users keep seeing the last good data with a "Data may be stale" label. No customer action needed.
