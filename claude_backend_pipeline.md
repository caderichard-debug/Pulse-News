# Claude Backend Pipeline Notes

## Baseline Bottlenecks Identified
- Fixed sleeps and conservative batch sizes in analysis and post-analysis loops.
- Several serial DB loops with repeated `NOT IN` scans.
- AI and external API paths lacked unified retry/backoff handling.
- Incomplete per-stage metric visibility for queue depth, latency, and cost.

## Implemented Improvements
- Added shared resilience helpers (`retry_call`, error classification).
- Added pipeline metrics utility for counters, gauges, stage latency, and cost.
- Added monitoring endpoint `/monitoring/pipeline`.
- Added output normalization/guardrails in analysis stage.
- Replaced expensive count implementation in `get_unanalyzed_article_count`.
- Added config-based tuning knobs for retries, timeouts, and per-stage batch sizes.
- Added model fallback logic when cost utilization approaches budget threshold.

## Operational Runbook
1. Check `GET /monitoring/pipeline` for latency, error, and spend signals.
2. If error rate rises, reduce stage batch sizes and increase min delay in settings.
3. If spend exceeds warning threshold, verify fallback model activation counter.
4. Use admin/manual job triggers for isolated stage replay if backlog accumulates.
5. Validate `JobExecutionHistory.result_data` for failure reason codes.
6. **`process_unprocessed` job** runs pending **extraction** first (so articles are not stuck behind `get_unanalyzed_article_count` only counting `COMPLETED`), then analysis, then always checks analyzed-but-missing-framework backlog.
7. **`POST /admin/jobs/analyze-recent?limit=5`** runs `analyze_recent_articles_job` to analyze the newest unanalyzed rows (including `PENDING` with `content_text`) without draining the full queue.
8. **Newsletter job** returns `skipped_reason` and `noop` when Resend is not configured or there are no eligible subscribers (still `success: true` for the HTTP job wrapper).
9. **Auth login hardening**: `verify_password` now treats invalid/legacy non-bcrypt hashes as a normal auth failure (`False`) instead of raising `ValueError: Invalid salt` and returning 500.
10. **Supabase schema isolation**: With `SUPABASE_DB_SCHEMA` / `SUPABASE_DB_ROLE` set, `backend/app/database.py` pins SQLModel metadata, normalizes `?schema=` for psycopg2, asserts `search_path` on every new connection, and `/health` runs a DB ping. Admin catalog checks live in `backend/sql/verify_isolation.sql`; runtime smoke: `backend/scripts/verify_isolation.py`.

## Mobile consumer notes
- Expo mobile app now calls backend endpoints directly (bearer JWT) for feed/detail/analytics/favorites/preferences/challenge flows.
- For mobile testing, keep deployed API reachable via HTTPS and provide the URL through `EXPO_PUBLIC_API_BASE_URL`.
- `GET /articles/{id}` accepts anonymous callers (optional JWT) so guests can open articles from the public feed; favorite state is omitted or false without a user.

