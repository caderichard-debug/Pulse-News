# Backend Pipeline Baseline Audit

## Scope
Audit of backend article analysis pipeline before/while applying reliability, quality, performance, observability, and cost improvements.

## Pipeline Stages
- Scrape: RSS ingestion to `Article` (`PENDING`)
- Extract: full content extraction (`COMPLETED`/`FAILED`)
- Analyze: LLM analysis and topic mapping
- Post-process: framework mapping, statistics verification, clustering, context generation

## Primary Baseline Risks
- External API/network failure handling was inconsistent across services.
- Fixed sleep and static batching limited throughput under low-error periods.
- Query patterns included expensive in-memory counting.
- Metrics existed in logs/history but lacked an aggregated stage-oriented endpoint.
- Cost controls did not have explicit budget-aware model fallback behavior.

## New Baseline Metrics to Track
- Stage success/failure counters
- Stage latency totals and invocation counts
- Pipeline backlog gauges
- Retry attempts and exhaustion signals
- Total and per-stage estimated cost

## Acceptance Targets
- Analysis success rate >= 99%
- p95 end-to-end latency reduced vs pre-change baseline
- Backlog age p95 < 6h
- Cost per analyzed article reduced without quality regressions

