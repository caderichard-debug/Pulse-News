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

## Cost and Throughput Knobs
- `max_tokens_per_request`
- stage batch sizes (`analysis_batch_size`, etc.)
- adaptive delay bounds (`pipeline_min_delay_seconds`, `pipeline_max_delay_seconds`)
- daily budget controls (`pipeline_daily_budget_usd`, `pipeline_warn_budget_percent`)

