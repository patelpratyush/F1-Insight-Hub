# Phase 1 parity checklist

Each legacy feature, its equivalent in the rewrite, and the test that proves it. Test paths are
relative to the repo root (`file::test name`). "done" means ingestion, api and web page are
covered by tests.

| Legacy feature | New equivalent | Status | Proving tests |
| --- | --- | --- | --- |
| Live weather | Open-Meteo hourly ingestion (Task 4), `weather` on `GET /v1/races/{season}/{round}` | done | `apps/worker/tests/test_weather_job.py::test_parses_hourly_points`, `::test_null_values_become_none`, `::test_ingest_weather_is_idempotent`, `apps/worker/tests/test_scheduling.py::test_races_needing_weather`, `apps/api/tests/test_races_api.py::test_race_without_sprint_has_empty_sprint_results` (asserts the weather points) |
| Championship standings | Driver standings (Phase 0), constructor standings (Task 3), `GET /v1/standings/...` | done | `apps/api/tests/test_standings.py::test_returns_latest_round_ordered_by_position`, `::test_fractional_points_preserved`, `apps/api/tests/test_teams_api.py::test_constructor_standings_latest_round`, `apps/worker/tests/test_standings_job.py::test_ingest_writes_rows_and_is_idempotent`, `apps/worker/tests/test_constructors_job.py::test_empty_standings_is_noop`, `apps/web/e2e/standings.spec.ts::sign up, return to standings, and see ingested data` |
| Race weekend forecast | Weather for race dates today to +7 days (Task 4) shown on the race page | done | `apps/worker/tests/test_scheduling.py::test_races_needing_weather`, `apps/api/tests/test_races_api.py::test_race_without_sprint_has_empty_sprint_results`, `apps/api/tests/test_races_api.py::test_race_with_cancelled_session_and_no_results` (empty forecast) |
| Session results | Results ingestion (Task 3), race detail api (Task 5), race page | done | `apps/web/src/components/race-results.test.tsx` (DNF, fractional points, team per round, empty state), `apps/web/e2e/browse.spec.ts::calendar links to a race page with results`, `apps/worker/tests/test_results_job.py::test_results_idempotent_and_dnf_has_null_position`, `::test_team_change_creates_new_stint`, `apps/api/tests/test_races_api.py::test_dnf_row_has_null_position_and_status`, `::test_results_attribute_team_per_round`, `::test_race_with_cancelled_session_and_no_results` |
| Race calendar | Calendar ingestion and `GET /v1/calendar` (Tasks 2 and 5) | done | `apps/web/e2e/browse.spec.ts::calendar links to a race page with results`, `apps/worker/tests/test_calendar_job.py::test_parses_sessions_per_weekend_format`, `apps/api/tests/test_calendar_api.py::test_calendar_lists_races_in_round_order`, `::test_sprint_weekend_has_sprint_session_and_cancelled_is_reported`, `::test_session_times_are_utc` |
| Driver profiles | `GET /v1/drivers/{id}` (Task 5), driver page (Task 10) | done | `apps/web/e2e/browse.spec.ts::command palette search navigates to the driver`, `::driver page accent colour equals the team colour`, `apps/api/tests/test_drivers_api.py::test_driver_profile_has_team_history_in_order`, `::test_recent_results_newest_first_with_team_per_round`, `::test_unknown_driver_is_404` |
| Team profiles | `GET /v1/teams/{id}` (Task 5), team page (Task 10) | done | `apps/web/src/components/team-theme.test.tsx`, `apps/api/tests/test_teams_api.py::test_team_profile_includes_color_and_drivers`, `::test_unknown_team_is_404`, `packages/core-py/tests/test_teams.py::test_known_team_color` |
| Dashboard | Home page (Task 10): next race card (countdown, \"Live now\"), link to standings | done | `apps/web/e2e/browse.spec.ts::home shows the next race card`, `apps/web/src/components/next-race-card.test.tsx` (countdown, live now, cancelled sessions, season complete) |
| Search | `GET /v1/search` | done (api) | `apps/api/tests/test_search_api.py::test_finds_driver_ignoring_case_and_accents`, `::test_finds_teams_and_races` |
| Live timing | OpenF1 poller to Redis (Task 8), SSE stream and snapshot (Task 8), Live Race Centre (Task 11) | done (free-tier data; real-time needs the OpenF1 Sponsor plan) | `apps/web/e2e/live.spec.ts::tower follows the replay, goes stale during a gap and recovers`, `::an unknown session shows the waiting state, never an empty tower`, `apps/web/src/hooks/use-live-session.test.ts`, `apps/web/src/components/live/live-tower.test.tsx`, `packages/core-py/tests/live/test_reducer.py::test_position_events_order_the_tower`, `::test_retired_driver_sorts_last_and_pit_flag_toggles`, `::test_gap_strings_are_kept_verbatim`, `apps/worker/tests/test_live_poll.py::test_poller_publishes_ordered_seq_and_state`, `::test_poller_publishes_waiting_status_on_upstream_error`, `apps/api/tests/test_live_sse.py::test_stream_replays_after_last_event_id`, `::test_no_data_emits_waiting_then_heartbeats`, `::test_per_ip_stream_limit_returns_429_and_releases`, `apps/worker/tests/test_replay_live.py::test_replay_final_state_reflects_overtake_pit_and_retirement`, load check `apps/api/tests/load/live_fanout.py` |

## Later phases (planned, not in Phase 1)

| Legacy feature | Status |
| --- | --- |
| Telemetry (car data, speed traces) | planned |
| Race predictions | planned |
| Strategy analysis | planned |
| Favorites (followed drivers and teams) | planned |
| Season comparison | planned |
| Pit stop analysis | planned (Phase 1 keeps pit-in state live and stints after the session) |
| Lap replay | planned (the dev replay tool `apps/worker/scripts/replay_live.py` is not a user feature) |
