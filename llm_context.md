# LLM Context

## Model Usage
- Default model: `settings.ai_model`
- Fallback model when budget warning threshold is exceeded: `settings.fallback_ai_model`
- OpenAI wrapper: `backend/app/utils/openai_client.py`

## LLM-Driven Features
- Article analysis (`ai_analyzer`)
- Framework discovery and mapping
- Statistic extraction and verification support
- Source tracing multi-turn reasoning

## Mobile usage notes
- Expo mobile UI now consumes backend route outputs directly through generated TypeScript client functions in `mobile/app/lib/api-client-react/src/generated/api.ts`.
- Advanced LLM-backed article endpoints consumed by mobile include:
  - `GET /articles/{id}/opposing-viewpoints`
  - `POST /articles/{id}/analyze-viewpoints`
  - `GET /articles/{id}/coverage`
  - `POST /articles/{id}/analyze-coverage`

## Web UX alignment notes
- Web feed signal readability now mirrors mobile interaction intent without changing API contracts:
  - `SentimentDot` includes directional icon + text label for non-color encoding.
  - `LeanPill` and `FrameworkCue` provide at-a-glance feed context while full framework analysis remains on detail/analytics routes.
- `_app.feed` filter controls expose better semantics (`aria-pressed`, input labels) and stronger keyboard focus treatment.
- Shared UI primitives now drive filter interactions:
  - `FilterChip` for selected/unselected chip state hierarchy.
  - `FilterSelect` wrapper around Radix select for consistent feed control affordance.
- Type safety hardening:
  - Required route `search` payloads are now passed for `/feed`, `/preferences`, and `/admin` navigation paths.
  - URL analyze normalization now coerces `analysis.political_lean` to numeric values before assigning `Article.political_lean`.

## Output Guardrails
- Article analysis payload normalization in `backend/app/services/ai_analyzer.py`
  - sentiment bounded to `[-10, 10]`
  - topic fallback to `general`
  - political lean fallback to `center`
  - empty summary replacement

## Failure Handling
- LLM requests wrapped with retry/backoff
- Request timeouts configurable via `ai_request_timeout_seconds`
- Retry limits configurable via `ai_max_retries`

## Deployment Context
- Current production target is Railway services with Supabase Postgres.
- Database URLs should use schema-scoped Supabase connection strings (for example, `...?schema=proj_pulse`) aligned with `docs/guides/SUPABASE_SCHEMA_ISOLATION_PORTABLE_GUIDE.md`.

## Cost and Throughput Knobs
- `max_tokens_per_request`
- stage batch sizes (`analysis_batch_size`, etc.)
- adaptive delay bounds (`pipeline_min_delay_seconds`, `pipeline_max_delay_seconds`)
- daily budget controls (`pipeline_daily_budget_usd`, `pipeline_warn_budget_percent`)

## Admin recovery
- `POST /admin/jobs/analyze-recent?limit=N` — background job `analyze_recent_articles_job` uses `get_recent_unanalyzed_article_ids` + optional `target_article_ids` on `analyze_articles_batch`.
- `process_unprocessed_articles_job` chains extraction when `get_pending_extraction_count` > 0, then unanalyzed analysis, then framework-gap processing.

