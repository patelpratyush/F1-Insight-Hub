# Phase 5: News, Social and Launch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an aggregated, deduplicated, driver-tagged news feed, server-side favorites, and reliable email and web-push notifications, then harden everything for public launch (load, security, accessibility, GDPR, backups, cutover).

**Architecture:** The worker polls RSS feeds, normalises and deduplicates articles, and tags them with drivers and teams using an alias dictionary. Notifications use a transactional outbox: domain events write `notification_outbox` rows in the same transaction as the change, and a delivery worker sends email (Resend) and web push (VAPID) with retries, idempotency and per-user preferences. The launch task group adds load tests, a security review, GDPR export and deletion, backup restore drills, and the production cutover.

**Tech Stack:** feedparser, simhash, bleach (sanitising), Resend, pywebpush, Web Push API and service worker, k6, OWASP ZAP baseline, Phase 0 to 4 stack.

**Spec:** `docs/superpowers/specs/2026-10-29-f1-insight-hub-rewrite-design.md`. Depends on: Phases 0 and 1. Notification triggers for fantasy depend on Phase 4 and for predictions on Phase 3; if those phases are not built yet, their triggers are skipped behind feature flags.

## Global Constraints

- Article content is never rendered as raw HTML. Store only title, source, published time, canonical URL, a plain-text excerpt of at most 280 chars, and an optional image URL. Always link out to the source. Respect each feed's terms: no full-text republishing.
- All outbound feed fetches use an allowlist of hosts, a 10 s timeout, a 2 MB size cap, and a `User-Agent` identifying the project.
- Notifications are opt-in per channel and per topic, with one-click unsubscribe (signed token) in every email. No marketing email.
- Web push requires explicit browser permission triggered by a user gesture.
- Deliveries are at-least-once with an idempotency key `(user_id, event_id, channel)`, so a retry never sends a duplicate.
- GDPR: export returns all personal data as JSON within 60 s, deletion anonymises within 30 days (immediate for sessions and push subscriptions).
- Launch gate: all CI gates green, load test and ZAP baseline pass thresholds, restore drill completed within the last 7 days.

## Review Focus

1. The same story from several outlets, or the same URL with tracking parameters: collapsed into one article with multiple sources. (Task 1)
2. A feed is down, returns HTML, malformed XML, gigantic payloads, or hostile content (script tags, javascript: URLs): ingestion survives and nothing unsafe reaches the UI. (Task 1, Task 2)
3. A user's push subscription has expired (HTTP 404 or 410): it is removed and deliveries continue to other channels. (Task 5)
4. An event triggers a notification twice (retry, duplicate event): the user receives it once. (Task 4, Task 5)
5. A user unsubscribes or changes preferences while a notification is queued: it is dropped at send time. (Task 4)
6. A user deletes their account with active fantasy leagues: personal data removed, league history remains with an anonymised label. (Task 8)
7. Time zones and quiet hours: notifications respect quiet hours in the user's time zone, except urgent lock reminders if the user opted in. (Task 4)

---

## File Structure

```
packages/db-py/alembic/versions/0008_news_social.py
packages/db-py/src/f1_db/models/{news.py,social.py,notifications.py}
packages/core-py/src/f1_core/news/{__init__,normalize,dedupe,tagging,aliases}.py
packages/core-py/src/f1_core/notifications/{__init__,events,preferences,render}.py
apps/worker/src/f1_worker/sources/rss.py
apps/worker/src/f1_worker/jobs/{news,notify_enqueue,notify_deliver}.py
apps/worker/src/f1_worker/delivery/{email_resend.py,webpush.py}
apps/api/src/f1_api/{schemas,services,routers}/{news,favorites,notifications,account}.py
apps/web/src/app/{news,favorites,settings/notifications,settings/account}/...
apps/web/public/{manifest.webmanifest,sw.js,icons/*}
apps/web/src/lib/push.ts
infra/k6/*.js
docs/{launch-checklist.md,security-review.md,runbooks/*}
```

---

### Task 1: News normalisation, deduplication and tagging (pure)

**Files:**
- Create: `packages/core-py/src/f1_core/news/{__init__,normalize,dedupe,tagging,aliases}.py`
- Test: `packages/core-py/tests/news/{test_normalize.py,test_dedupe.py,test_tagging.py}`

**Interfaces:**
- Produces:
  - `canonical_url(url: str) -> str` strips tracking params (`utm_*`, `fbclid`, `gclid`, `ref`), fragments, lowercases host, removes trailing slash, upgrades `http` to `https`; returns the input unchanged for invalid URLs rather than raising.
  - `clean_text(html_or_text: str, max_len: int = 280) -> str` strips tags and entities (via `bleach.clean(strip=True)` then whitespace collapse), cuts at a word boundary, appends an ellipsis.
  - `simhash64(title: str) -> int` and `is_near_duplicate(a: int, b: int, max_distance: int = 3) -> bool` over normalised title tokens (lowercased, stopwords removed).
  - `tag_article(title: str, excerpt: str, aliases: AliasIndex) -> Tags(drivers: list[str], teams: list[str])` word-boundary, accent-insensitive matching using aliases such as `{"max verstappen": "max_verstappen", "verstappen": "max_verstappen", "ver": None}` (3-letter codes only match when uppercase and standalone to avoid matching words like "ham" or "bot").
  - `AliasIndex.build(drivers, teams)` generating aliases from DB rows (full name, family name, code, team name and common short names).

- [ ] **Step 1: Write the failing tests**

```python
@pytest.mark.parametrize("raw,expected", [
    ("http://Example.com/a/?utm_source=x&id=2#top", "https://example.com/a?id=2"),
    ("https://example.com/a/", "https://example.com/a"),
    ("not a url", "not a url"),
    ("https://example.com/a?fbclid=abc", "https://example.com/a"),
])
def test_canonical_url(raw, expected): ...

def test_clean_text_strips_script_and_entities():
    assert clean_text("<p>Hi <script>alert(1)</script>&amp; bye</p>") == "Hi & bye"
def test_clean_text_truncates_at_word_boundary_with_ellipsis(): ...
def test_javascript_urls_are_not_preserved(): ...

def test_near_duplicate_titles_detected():
    a = simhash64("Verstappen wins dramatic Monaco Grand Prix")
    b = simhash64("Verstappen wins dramatic Monaco GP")
    assert is_near_duplicate(a, b)
def test_unrelated_titles_not_duplicates(): ...

def test_tags_driver_by_family_name_ignoring_accents(): ...   # "Perez" matches perez
def test_code_alias_only_matches_uppercase_standalone(): ...   # "HAM" matches, "ham sandwich" does not
def test_team_tagging_and_multiple_drivers(): ...
def test_no_matches_returns_empty_tags(): ...
```

- [ ] **Step 2: Implement and commit**

Simhash: tokenise to 3-word shingles, hash each with `hashlib.blake2b(digest_size=8)`, accumulate bit votes, build 64-bit signature, Hamming distance via `(a ^ b).bit_count()`.

Run: `uv run pytest packages/core-py/tests/news -v` (Expected: pass.)

```bash
git add -A && git commit -m "feat(core): news normalisation, near-duplicate detection and tagging"
```

---

### Task 2: RSS ingestion job

**Files:**
- Create: `packages/db-py/src/f1_db/models/news.py`, `packages/db-py/alembic/versions/0008_news_social.py` (news part), `apps/worker/src/f1_worker/sources/rss.py`, `apps/worker/src/f1_worker/jobs/news.py`, `apps/worker/tests/fixtures/{feed_ok.xml,feed_malformed.xml,feed_hostile.xml,feed_dupe_b.xml}`
- Test: `apps/worker/tests/test_news_job.py`

**Interfaces:**
- Tables: `news_sources(id, key unique, name, feed_url, host, active, last_fetched_at, last_status)`, `articles(id, canonical_url unique, title, excerpt, image_url, published_at, simhash BIGINT, first_source_id, created_at)`, `article_sources(article_id, source_id, url, published_at)` PK `(article_id, source_id)`, `article_tags(article_id, kind: "driver"|"team", ref)` PK all three, index on `articles(published_at desc)`.
- `RssClient.fetch(source) -> list[RawItem]` enforces host allowlist (host must equal `source.host`), 10 s timeout, 2 MB cap (streamed with early abort), content-type check, `feedparser` parse, ignoring items without link or title. Never raises on malformed XML; returns what it can and `[]` otherwise.
- `ingest_news(session_factory, client, aliases) -> int`: for each active source (circuit breaker per source), canonicalise, `clean_text`, compare simhash against articles from the last 48 h; near duplicates attach an `article_sources` row instead of creating an article; images accepted only if `https` and host not in a denylist; stores tags.

- [ ] **Step 1: Write the failing tests**

```python
async def test_ingest_ok_feed_creates_articles_with_tags(...): ...
async def test_same_url_with_utm_params_is_one_article(...): ...
async def test_near_duplicate_from_second_source_attaches_source_not_article(...): ...
async def test_malformed_feed_is_survived_and_status_recorded(...): ...
async def test_hostile_content_is_sanitised(...): ...   # script tags, javascript: link, onerror images
async def test_oversized_feed_is_aborted(...): ...
async def test_redirect_to_other_host_is_rejected(...): ...
async def test_rerun_is_idempotent(...): ...
async def test_one_failing_source_does_not_block_others(...): ...
```

- [ ] **Step 2: Implement and commit**

Schedule: every 10 minutes (`cron(news_task, minute=set(range(0, 60, 10)), unique=True)`).

```bash
git add -A && git commit -m "feat(worker): safe rss ingestion with dedupe and tagging"
```

---

### Task 3: News and favorites API

**Files:**
- Create: `packages/db-py/src/f1_db/models/social.py`, migration part for `favorites(user_id, kind: "driver"|"team"|"race", ref, created_at)` PK `(user_id, kind, ref)`; `apps/api/src/f1_api/{schemas,services,routers}/{news,favorites}.py`
- Test: `apps/api/tests/test_news_api.py`, `apps/api/tests/test_favorites_api.py`

**Interfaces:**
- Produces:
  - `GET /v1/news?driver=&team=&before=<cursor>&limit=<=50` (public, cursor pagination by `(published_at, id)`) returns `{items: [{id, title, excerpt, image_url, published_at, sources: [{name, url}], tags: {drivers, teams}}], next_cursor}`; cached 60 s.
  - `GET /v1/favorites`, `PUT /v1/favorites/{kind}/{ref}`, `DELETE /v1/favorites/{kind}/{ref}` (auth; at most 100 favorites per user; `kind` and `ref` validated against existing rows with a `404` problem for unknown refs; idempotent).
  - `POST /v1/favorites/import` body `{items: [{kind, ref}]}` for one-time import of legacy local favorites (max 100, unknown refs skipped and reported).

- [ ] **Step 1: Write the failing tests** (cursor pagination has no duplicates or gaps across pages; filter by driver; invalid cursor is 422; favorites idempotent put and delete; limit of 100; unknown ref 404; import skips unknown and reports counts; users cannot see each other's favorites; news response never contains HTML tags)

- [ ] **Step 2: Implement, regenerate contract, commit**

Run: `uv run pytest apps/api -v && pnpm contract`

```bash
git add -A && git commit -m "feat(api): news feed and favorites endpoints"
```

---

### Task 4: Notification events, preferences and outbox (pure plus schema)

**Files:**
- Create: `packages/core-py/src/f1_core/notifications/{__init__,events,preferences,render}.py`, `packages/db-py/src/f1_db/models/notifications.py`, migration part for `notification_prefs(user_id PK, email_enabled, push_enabled, topics JSONB, timezone, quiet_start, quiet_end, urgent_override)`, `push_subscriptions(id, user_id, endpoint unique, p256dh, auth, created_at, last_success_at)`, `notification_outbox(id, user_id, event_id, channel, payload_json, status: "pending"|"sent"|"failed"|"dropped", attempts, next_attempt_at, created_at, sent_at)` unique `(user_id, event_id, channel)`, `unsubscribe_tokens` not stored (stateless signed tokens)
- Test: `packages/core-py/tests/notifications/*.py`, `packages/db-py/tests/test_schema_phase5.py`

**Interfaces:**
- Produces:
  - Event types: `session_starting`, `race_results`, `favorite_driver_news`, `fantasy_lock_reminder`, `fantasy_scored`, `prediction_published`. `NotificationEvent(id: str (deterministic, e.g. "session_starting:2025:3:Q"), type, audience: Audience, data: dict)`.
  - `should_send(prefs, event, channel, now_utc) -> Decision(send: bool, reason: str | None)` honouring channel enabled, topic enabled, quiet hours in `prefs.timezone` (wrap-around windows like 22:00 to 07:00), and `urgent_override` for `fantasy_lock_reminder` only.
  - `render(event, channel, locale="en") -> RenderedMessage(subject, body_text, body_html, url)`; HTML is built from escaped parts only.
  - `sign_unsubscribe(user_id, topic, secret) -> str` and `verify_unsubscribe(token, secret) -> (user_id, topic) | None` (HMAC-SHA256, constant-time compare, 90-day expiry).

- [ ] **Step 1: Write the failing tests**

```python
def test_quiet_hours_wraparound_blocks_at_23_local_and_allows_at_08_local(): ...
def test_quiet_hours_use_user_timezone_not_utc(): ...
def test_urgent_override_only_for_lock_reminder(): ...
def test_disabled_channel_or_topic_is_not_sent(): ...
def test_event_id_is_deterministic(): ...
def test_render_escapes_html_in_titles(): ...
def test_unsubscribe_token_roundtrip_and_tamper_rejected_and_expired_rejected(): ...
async def test_outbox_unique_per_user_event_channel(engine): ...
```

- [ ] **Step 2: Implement and commit**

```bash
git add -A && git commit -m "feat: notification events, preferences, rendering and outbox schema"
```

---

### Task 5: Notification enqueue and delivery

**Files:**
- Create: `apps/worker/src/f1_worker/jobs/{notify_enqueue,notify_deliver}.py`, `apps/worker/src/f1_worker/delivery/{email_resend.py,webpush.py}`
- Modify: `apps/worker/src/f1_worker/settings.py`, `apps/worker/pyproject.toml` (add `pywebpush`, `resend`)
- Test: `apps/worker/tests/test_notify_enqueue.py`, `apps/worker/tests/test_notify_deliver.py`

**Interfaces:**
- Produces:
  - `enqueue_event(session_factory, event: NotificationEvent) -> int` resolves the audience (all users with the topic enabled, or favorites match), evaluates `should_send` per channel at enqueue time (quiet hours defer by setting `next_attempt_at` to the end of the window, not drop), and inserts outbox rows with `ON CONFLICT DO NOTHING`.
  - `deliver_pending(session_factory, email: EmailSender, push: PushSender, now) -> DeliveryStats` claims up to 100 due rows with `FOR UPDATE SKIP LOCKED`, re-checks preferences at send time (drops if unsubscribed since), sends, marks `sent`, or on failure increments attempts with exponential backoff (1, 5, 30, 120 minutes, max 5 attempts, then `failed`). Push 404 or 410 deletes the subscription. Email provider 4xx (not 429) marks `failed` without retry.
  - Triggers (`tick_notifications` cron, every minute): session starting in 15 minutes (favorite or all), race results available, fantasy lock in 60 minutes (if Phase 4 is enabled), favorite-driver news (from `articles` tagged to a favorite driver in the last 10 minutes).

- [ ] **Step 1: Write the failing tests**

```python
async def test_enqueue_same_event_twice_creates_one_row_per_user_channel(...): ...
async def test_quiet_hours_defer_instead_of_drop(...): ...
async def test_deliver_marks_sent_and_is_not_resent(...): ...
async def test_user_unsubscribes_after_enqueue_is_dropped_at_send(...): ...
async def test_push_410_deletes_subscription_and_other_channel_still_sends(...): ...
async def test_transient_failure_backs_off_and_eventually_fails_after_5_attempts(...): ...
async def test_two_workers_never_send_same_row(...): ...  # SKIP LOCKED, asyncio.gather
async def test_email_contains_unsubscribe_link_and_list_unsubscribe_header(...): ...
```

Use fake `EmailSender` and `PushSender` classes recording calls. Real senders: `ResendEmailSender` (adds `List-Unsubscribe` and `List-Unsubscribe-Post: List-Unsubscribe=One-Click` headers) and `WebPushSender` (VAPID keys from env).

- [ ] **Step 2: Implement and commit**

```bash
git add -A && git commit -m "feat(worker): outbox enqueue and idempotent notification delivery"
```

---

### Task 6: Notification and subscription API

**Files:**
- Create: `apps/api/src/f1_api/{schemas,services,routers}/notifications.py`
- Test: `apps/api/tests/test_notifications_api.py`

**Interfaces:**
- Produces (auth unless noted):
  - `GET/PUT /v1/notifications/prefs` (validates timezone against IANA names via `zoneinfo`, quiet hours `HH:MM`).
  - `POST /v1/notifications/push/subscribe` body `{endpoint (https URL), keys: {p256dh, auth}}` (max 5 subscriptions per user; idempotent on endpoint); `DELETE /v1/notifications/push/subscribe` body `{endpoint}`.
  - `GET /v1/notifications/vapid-key` (public) returns the public VAPID key.
  - `POST /v1/notifications/unsubscribe` (public, one-click) body `token=...` verifies the signed token and disables that topic for that user; always returns `200` with a generic message (no information leak), including for invalid tokens.

- [ ] **Step 1: Write the failing tests** (invalid timezone 422; endpoint must be https; sixth subscription 409; unsubscribe token disables only the named topic; tampered token returns 200 and changes nothing; prefs are per-user; defaults when no prefs row exist are all off)

- [ ] **Step 2: Implement and commit**

```bash
git add -A && git commit -m "feat(api): notification preferences, push subscriptions and one-click unsubscribe"
```

---

### Task 7: Web: news, favorites, notification settings and PWA

**Files:**
- Create: `apps/web/src/app/{news/page.tsx,favorites/page.tsx,settings/notifications/page.tsx}`, `apps/web/src/components/{news-card,favorite-button,notification-settings}.tsx`, `apps/web/src/lib/{push.ts,legacy-favorites.ts}`, `apps/web/public/{manifest.webmanifest,sw.js}`, `apps/web/public/icons/*`
- Test: `apps/web/src/lib/{push,legacy-favorites}.test.ts`, `apps/web/src/components/{news-card,favorite-button,notification-settings}.test.tsx`, `apps/web/e2e/{news,notifications}.spec.ts`

**Interfaces:**
- Produces:
  - `<NewsCard>` shows title (as text), source names, relative time, tag chips linking to driver and team pages, and always links out with `rel="noopener noreferrer"`; no HTML injection (test with a hostile title string).
  - `<FavoriteButton kind ref />` toggles via API with optimistic UI and rollback; unauthenticated users are sent to sign-in with `next`.
  - `lib/push.ts`: `subscribeToPush(vapidKey)` registers `/sw.js`, requests permission only from a user gesture, handles denied or unsupported browsers by returning a typed result (`"granted" | "denied" | "unsupported"`); `urlBase64ToUint8Array` helper tested.
  - `lib/legacy-favorites.ts`: `readLegacyFavorites(storage)` reads the old localStorage keys safely (invalid JSON returns `[]`), and the favorites page offers one-time "Import saved favorites" using `POST /v1/favorites/import`, then clears the old keys on success.
  - `sw.js` shows notifications from push payloads (title, body, url), validates `url` is same-origin before opening, and handles `notificationclick`.
  - `manifest.webmanifest` with name, icons (192, 512, maskable), `display: standalone`, `theme_color #0B0B0D`.

- [ ] **Step 1: Write the failing tests** (hostile title rendered as text; push permission denied path; unsupported browser path; legacy import with corrupt JSON; optimistic rollback on API failure; quiet-hours inputs validate; `sw.js` rejects cross-origin click URLs via a small testable `isSameOrigin` module imported by the worker)

- [ ] **Step 2: Implement, E2E and commit**

E2E: sign in, favorite a driver, see news filtered to that driver from seeded articles, enable email notifications, set quiet hours, reload and verify persistence; Playwright grants the `notifications` permission to test the subscribe flow against a fake push endpoint.

```bash
git add -A && git commit -m "feat(web): news, favorites, notification settings and PWA"
```

---

### Task 8: GDPR export and account deletion

**Files:**
- Create: `apps/api/src/f1_api/{schemas,services,routers}/account.py`, `apps/worker/src/f1_worker/jobs/account_purge.py`, `apps/web/src/app/settings/account/page.tsx`
- Test: `apps/api/tests/test_account_api.py`, `apps/worker/tests/test_account_purge.py`

**Interfaces:**
- Produces:
  - `GET /v1/account/export` returns JSON `{profile, favorites, notification_prefs, push_subscriptions (endpoints only), fantasy_teams, league_memberships, fantasy_scores}` for the caller only, generated under 60 s (streaming response), with `Content-Disposition: attachment`.
  - `DELETE /v1/account` (requires re-auth within 10 minutes via a `fresh` claim, otherwise `403 REAUTH_REQUIRED`) immediately revokes sessions and push subscriptions, deletes favorites and notification data, marks the user `pending_deletion`, and enqueues `account_purge`.
  - `account_purge(user_id)`: anonymises fantasy rows (`team name -> "Former player"`, `user_id -> NULL`), removes league memberships where the user was not the owner, transfers or deletes owned leagues (deleted if no other members, otherwise ownership goes to the earliest member), deletes the Better Auth user row, and records an `admin_audit` entry without personal data. Idempotent.

- [ ] **Step 1: Write the failing tests** (export contains only the caller's data and no other users' emails; deletion without fresh auth is 403; after purge fantasy history still counts in leaderboards under the anonymised label; owner deletion with members transfers ownership; purge twice is a no-op; push subscriptions removed immediately)

- [ ] **Step 2: Implement and commit**

```bash
git add -A && git commit -m "feat: gdpr export and account deletion with anonymised history"
```

---

### Task 9: Load, security and accessibility hardening

**Files:**
- Create: `infra/k6/{read_heavy.js,live_sse.js,write_mix.js}`, `.github/workflows/nightly.yml`, `docs/security-review.md`, `apps/web/e2e/a11y.spec.ts`
- Modify: `apps/api/src/f1_api/main.py` (security headers for api responses)

- [ ] **Step 1: Load tests**

`read_heavy.js` (k6): ramp to 300 virtual users for 5 minutes across calendar, standings, race detail and news; thresholds `http_req_duration{p(95)}<200` for cached reads, error rate under 0.5%. `live_sse.js`: 500 concurrent SSE clients for 5 minutes, thresholds on event lag under 5 s and zero dropped connections other than per-IP limit rejections. `write_mix.js`: 50 users saving fantasy teams and toggling favorites, p95 under 400 ms. Run against staging: `k6 run infra/k6/read_heavy.js`. Expected: thresholds pass; if not, profile with traces and fix before launch.

- [ ] **Step 2: Security review and scans**

Add `nightly.yml` running OWASP ZAP baseline against staging, `pip-audit` and `pnpm audit --prod`, Trivy on the container images, and the upstream-schema canary from the spec (calls Jolpica and OpenF1 once and validates against the parsers). Work through the checklist in `docs/security-review.md` and record the result and fix for each item: authN and authZ on every write route (automated test enumerating all routes in the OpenAPI spec and asserting that every non-GET route requires auth except the one-click unsubscribe), IDOR checks (users cannot access other users' teams, leagues, favorites), CSRF on cookie-authenticated Next routes, rate limits, SSRF review of RSS fetching, headers and CSP, secrets inventory, dependency pins.

Add the automated test `apps/api/tests/test_route_auth_inventory.py`:

```python
PUBLIC_WRITE_ALLOWLIST = {("POST", "/v1/notifications/unsubscribe")}

def test_every_write_route_requires_auth_except_allowlist():
    app = create_app(Settings())
    for route in app.routes:
        for method in getattr(route, "methods", set()) & {"POST", "PUT", "PATCH", "DELETE"}:
            if (method, route.path) in PUBLIC_WRITE_ALLOWLIST:
                continue
            deps = {d.call for d in route.dependant.dependencies}
            assert current_principal in deps or any(_requires_principal(d) for d in route.dependant.dependencies), (method, route.path)
```

- [ ] **Step 3: Accessibility audit**

`a11y.spec.ts` runs `@axe-core/playwright` on the 15 key pages (home, standings, calendar, race, driver, team, live, telemetry compare, predictions, strategy, fantasy team, leagues, news, favorites, settings) in both dark and light themes and asserts zero serious or critical violations; add keyboard-only journey tests for command palette, team builder and strategy builder; verify reduced-motion mode disables all non-essential animation.

- [ ] **Step 4: Run and commit**

Run: `uv run pytest && pnpm test && pnpm --filter @f1/web e2e && k6 run infra/k6/read_heavy.js`
Expected: green and thresholds met.

```bash
git add -A && git commit -m "test: load, security inventory, nightly scans and accessibility audit"
```

---

### Task 10: Launch: backups, observability review, cutover

**Files:**
- Create: `docs/launch-checklist.md`, `docs/runbooks/{restore-drill.md,incident-response.md,rollback.md}`, `infra/terraform/monitoring.tf`, `apps/web/src/app/(legal)/{privacy,terms,about}/page.tsx`
- Modify: `README.md`

- [ ] **Step 1: Backups and restore drill**

Enable Neon point-in-time recovery and daily logical dumps to R2 (`pg_dump` job in the worker, 30-day retention). Perform a restore drill into a scratch Neon branch, run the api test suite against it, and record the date and duration in `docs/runbooks/restore-drill.md`. The launch gate requires a drill within the previous 7 days.

- [ ] **Step 2: Monitoring and alerting**

Create dashboards and alerts in `monitoring.tf`: ingestion lag (freshness over 2 h), api 5xx rate over 1% for 5 minutes, p95 latency over SLO for 10 minutes, SSE lag over 5 s during live sessions, outbox pending older than 15 minutes, worker queue depth, and error budget burn. Page the owner on 5xx and ingestion alerts, notify on the rest. Verify each alert fires by injecting a failure in staging (stop the worker; return 500 from a test route) and record the evidence.

- [ ] **Step 3: Legal and disclosures**

Privacy policy (data collected, processors: Neon, Vercel, Fly, Upstash, Cloudflare, Resend, Sentry, Google if Gemini is enabled; rights and contact), terms, and an about page with the non-affiliation disclaimer and data source credits (Jolpica, OpenF1, FastF1, Open-Meteo). Footer links on every page. Cookie notice is not needed for strictly necessary cookies only; confirm no analytics cookies are set.

- [ ] **Step 4: Cutover**

1. Freeze `legacy` branch (protected, read-only). Tag it `legacy-final`.
2. Final staging soak: 48 hours with synthetic checks every minute; zero Sev1 alerts.
3. Production deploy via approved workflow, run smoke E2E against production, verify `/readyz`, freshness, and one live replay.
4. Point the domain to Vercel; keep the old host as a redirect for 90 days.
5. Rollback plan in `docs/runbooks/rollback.md`: Fly releases rollback command, Vercel instant rollback, database migrations are forward-only so any rollback target must be compatible with the current schema (the migration policy requires an expand-then-contract pattern).
6. Announce, then monitor the first week with a daily review of error budget and cost.

- [ ] **Step 5: Final verification and commit**

Run the full gate: all CI jobs green on `main`, load tests pass, ZAP baseline clean (no high findings), axe clean, restore drill current. Tick every line in `docs/launch-checklist.md`.

```bash
git add -A && git commit -m "chore(launch): backups, alerting, legal pages and cutover runbooks"
```

Open the PR `phase-5-news-social-launch`. Exit criterion: notifications deliver within one minute of the trigger event, and the launch checklist is fully ticked.
