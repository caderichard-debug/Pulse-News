import logging
import threading
from collections import defaultdict
from time import perf_counter
from typing import Dict


logger = logging.getLogger(__name__)
_lock = threading.Lock()
_counters = defaultdict(int)
_gauges = {}
_costs = defaultdict(float)
_latency_totals = defaultdict(float)


def incr(metric: str, value: int = 1) -> None:
    with _lock:
        _counters[metric] += value


def observe_latency(metric: str, seconds: float) -> None:
    with _lock:
        _latency_totals[metric] += seconds
        _counters[f"{metric}_count"] += 1


def set_gauge(metric: str, value: float) -> None:
    with _lock:
        _gauges[metric] = value


def add_cost(stage: str, usd: float) -> None:
    with _lock:
        _costs[stage] += usd
        _costs["pipeline_total"] += usd


def snapshot() -> Dict[str, Dict]:
    with _lock:
        return {
            "counters": dict(_counters),
            "gauges": dict(_gauges),
            "costs_usd": dict(_costs),
            "latency_totals": dict(_latency_totals),
        }


class TimedStage:
    def __init__(self, metric: str):
        self.metric = metric
        self.started = 0.0

    def __enter__(self):
        self.started = perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb):
        duration = perf_counter() - self.started
        observe_latency(self.metric, duration)
        logger.info("stage_timing metric=%s duration_seconds=%.3f", self.metric, duration)
