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

