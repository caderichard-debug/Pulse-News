# Pulse Project Overview

Pulse is a backend/frontend system that ingests news articles, analyzes them with AI, and enriches them with framework mapping, statistics verification, clustering, and generated context.

## Backend Pipeline
- Scheduler: `backend/app/jobs/scheduler.py`
- Task chain: `backend/app/jobs/tasks.py`
- Pipeline stages:
  - RSS scrape
  - Content extraction
  - AI article analysis
  - Post-analysis fanout (frameworks, statistics, clustering, context)

## Primary Reliability Controls
- Job execution tracking in `JobExecutionHistory`
- Advisory-lock based duplicate run protection
- Shared retry/backoff utility: `backend/app/utils/resilience.py`
- Configurable retries/timeouts via `backend/app/config.py`

## Observability and Cost
- In-process pipeline metrics utility: `backend/app/utils/pipeline_metrics.py`
- Metrics endpoint: `GET /monitoring/pipeline`
- Cost tracking:
  - OpenAI token cost estimation in `backend/app/utils/openai_client.py`
  - Budget thresholds in settings (`pipeline_daily_budget_usd`, `pipeline_warn_budget_percent`)

