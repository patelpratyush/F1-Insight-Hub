# Runbook: live session (OpenF1 poller)

Live timing is unofficial, community data from OpenF1. The worker polls OpenF1 and writes
reduced timing state to Redis; the api serves it as a snapshot and an SSE stream.

**Plan limits.** Real-time OpenF1 data needs the paid Sponsor plan. We are on the free tier,
which serves only past sessions (data appears about 30 minutes after it happens), so during a
real session the tower may stay on "Waiting for live data". The poll interval is
`OPENF1_POLL_SECONDS` on the worker (default 15: the free tier allows 30 requests/min and one
poll hits 7 endpoints). Live with under 5 s lag needs Sponsor plus MQTT (not built yet).

## How it runs

- `tick_sessions` (arq cron, every minute) marks sessions live from the calendar, resolves the
  OpenF1 `session_key`, and enqueues `poll_live_session(key)` with arq job id `live:<key>`
  (one poller per session; timeout 4 h, `max_tries` 1).
- The poller loops while the session's DB status is `live`, polling every
  `OPENF1_POLL_SECONDS`. After the session, `flush_live_session` (job `flush:<session id>`)
  runs 45 min later and stores laps and stints in Postgres.

## Verify the poller during a session

1. **Worker logs** (Railway, `f1-worker` service, Deployments > View logs). Search for
   `openf1_`:
   - `openf1_endpoint_failed` (one endpoint failed; others still polled) is fine occasionally.
   - `openf1_unavailable` (all 7 failed) means OpenF1 is down; viewers get "waiting" status.
   - `openf1_sessions_failed` means the session key could not be resolved; no poller starts.
2. **Redis** (all keys expire 24 h after the last write):

   | Key | Type | What to check |
   | --- | --- | --- |
   | `live:<key>` | stream | `XLEN`, `XREVRANGE live:<key> + - COUNT 1`: one entry per poll with new events, id `<last seq>-0`, fields `seq`, `payload`, `state` |
   | `live:<key>:state` | string | latest TimingState JSON; `status` should be `live` |
   | `live:<key>:seq` | counter | last event seq; should grow every poll or two |
   | `live:<key>:seen` | set | event fingerprints (dedupe) |
   | `live:<key>:cursor` | hash | per-kind latest timestamp fetched |
   | `arq:job:live:<key>`, `arq:in-progress:live:<key>` | arq | the poller job is queued or running |
   | `live:conn:<ip>` | counter | open streams per viewer IP (max 3) |

3. **Api**: `curl https://<api>/v1/live/<key>/snapshot` returns the tower; `last_seq` should
   increase between calls a poll interval apart. `curl -N https://<api>/v1/live/<key>/stream`
   prints `event: tower` frames, and `: heartbeat` every 15 s when nothing changes.

## Restart the poller

The job id prevents duplicates, and arq keeps a finished or failed job's result for 1 hour,
which also blocks a new job with the same id. To restart:

1. Clear the old job: `redis-cli DEL arq:job:live:<key> arq:in-progress:live:<key>
   arq:result:live:<key> arq:retry:live:<key>`.
2. Within a minute `tick_sessions` re-enqueues it if the session is still `live` in the DB.
   If the worker process itself is stuck, restart the `f1-worker` service on Railway first.
3. The poller resumes from `live:<key>:state` and the `:cursor` hash, so there are no
   duplicates or seq gaps; viewers reconnect with `Last-Event-ID` and catch up.

## Replay data (dev only)

`apps/worker/scripts/replay_live.py` replays a recorded JSONL fixture through the real poller
code (`poll_once`), so the stream and state are exactly what production writes:

```bash
uv run python apps/worker/scripts/replay_live.py \
  apps/worker/tests/fixtures/live_replay_9999.jsonl --speed 5 \
  [--session-key 9999] [--redis-url redis://localhost:6379/0]   # or REDIS_URL
```

- Each line is a LiveEvent without `seq` (`{"ts", "kind", "driver_number", "data"}`), or a
  `{"pause_s": N}` directive: N wall-clock seconds of silence (not divided by `--speed`).
- It deletes `live:<key>*` first, so every run is a clean session. Then open `/live/<key>` in
  the web app. Never point it at production Redis.
- The bundled fixture has five drivers, a "+1 LAP" gap, a pit stop, an overtake (16 passes 4),
  a retirement (81), a 25 s pause (enough for the stale banner), then more laps. At
  `--speed 5` it takes about 28 s.

## What users see during an OpenF1 outage

- At session start with no data yet: the stream sends a `waiting` state and the page shows
  "Waiting for live data", never a blank tower.
- Mid-session, when every OpenF1 endpoint fails, the poller publishes `status: waiting`; the
  page shows "Waiting for live data".
- When the stream is silent for more than 15 s during a live session (OpenF1 slow, poller
  stopped), the page shows a stale banner with "Updated Xs ago". It clears on the next entry.
- No action needed for a short outage: the poller keeps polling and recovers by itself. If
  logs show the poller job ended, restart it (above).

## Capacity

Each api instance serves at most 500 streams, 3 per viewer IP. Check fan-out and lag locally
with `uv run python apps/api/tests/load/live_fanout.py` (300 clients, 60 s; fails if
publish-to-receive p95 is 1 s or more).
