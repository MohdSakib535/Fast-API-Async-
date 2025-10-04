"""Asynchronous HTTP load-testing helpers for internal diagnostics.

The utilities here are designed to be lightweight so they can be executed from
inside FastAPI endpoints (for ad-hoc verification) or launched manually via
``python -m app.Database.load_test``. They rely exclusively on ``httpx`` and
standard library primitives, avoiding external tooling.
"""

from __future__ import annotations

import asyncio
import statistics
import time
from collections import Counter
from typing import Any, Dict, Iterable, Optional

import httpx
from pydantic import BaseModel, Field


class LoadTestConfig(BaseModel):
    """Configuration accepted by the load-test runner."""

    url: str = Field(..., description="Target endpoint to exercise during the test")
    method: str = Field("GET", description="HTTP method to use (GET, POST, etc.)")
    total_requests: int = Field(50, ge=1, description="Total number of requests to perform")
    concurrency: int = Field(10, ge=1, description="How many requests to run concurrently")
    timeout: float = Field(10.0, gt=0, description="Per-request timeout in seconds")
    headers: Dict[str, str] = Field(default_factory=dict, description="Optional headers to include")
    json_payload: Optional[Dict[str, Any]] = Field(
        default=None,
        description="JSON body to send with each request (for POST/PUT/PATCH)",
    )
    query_params: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Query parameters to append to the request",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "url": "http://localhost:8000/book/all",
                "method": "GET",
                "total_requests": 50,
                "concurrency": 10,
                "timeout": 5.0,
            }
        }


class LoadTestResult(BaseModel):
    """Summary metrics returned after executing a load test."""

    requests_total: int
    concurrency: int
    successes: int
    failures: int
    status_codes: Dict[str, int]
    min_response_time: Optional[float]
    max_response_time: Optional[float]
    average_response_time: Optional[float]
    p95_response_time: Optional[float]
    errors: list[str]


async def _perform_request(
    client: httpx.AsyncClient,
    config: LoadTestConfig,
) -> tuple[Optional[float], Optional[int], Optional[str]]:
    start = time.perf_counter()
    try:
        response = await client.request(
            config.method.upper(),
            config.url,
            json=config.json_payload,
            params=config.query_params,
            headers=config.headers or None,
        )
        elapsed = time.perf_counter() - start
        return elapsed, response.status_code, None
    except httpx.HTTPError as exc:
        elapsed = time.perf_counter() - start
        return elapsed, None, str(exc)


def _percentile(values: Iterable[float], percentile: float) -> Optional[float]:
    data = sorted(values)
    if not data:
        return None
    k = (len(data) - 1) * percentile
    f = int(k)
    c = min(f + 1, len(data) - 1)
    if f == c:
        return data[f]
    d0 = data[f] * (c - k)
    d1 = data[c] * (k - f)
    return d0 + d1


async def run_load_test(config: LoadTestConfig) -> LoadTestResult:
    """Execute an asynchronous load-test based on ``config`` and return metrics."""

    semaphore = asyncio.Semaphore(config.concurrency)
    timings: list[float] = []
    status_counter: Counter[int] = Counter()
    errors: list[str] = []

    async with httpx.AsyncClient(timeout=config.timeout) as client:
        async def worker() -> None:
            async with semaphore:
                elapsed, status_code, error = await _perform_request(client, config)
                if elapsed is not None:
                    timings.append(elapsed)
                if status_code is not None:
                    status_counter[status_code] += 1
                if error is not None:
                    errors.append(error)

        await asyncio.gather(*(worker() for _ in range(config.total_requests)))

    successes = sum(status_counter.values())
    failures = config.total_requests - successes

    min_time = min(timings) if timings else None
    max_time = max(timings) if timings else None
    avg_time = statistics.mean(timings) if timings else None
    p95_time = _percentile(timings, 0.95)

    result = LoadTestResult(
        requests_total=config.total_requests,
        concurrency=config.concurrency,
        successes=successes,
        failures=failures,
        status_codes={str(code): count for code, count in status_counter.items()},
        min_response_time=min_time,
        max_response_time=max_time,
        average_response_time=avg_time,
        p95_response_time=p95_time,
        errors=errors,
    )

    return result


def run_load_test_sync(config: LoadTestConfig) -> LoadTestResult:
    """Convenience wrapper to execute the load test from synchronous contexts."""

    return asyncio.run(run_load_test(config))


if __name__ == "__main__":  # pragma: no cover - manual utility entrypoint
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Fire a simple HTTP load test.")
    parser.add_argument("url", help="Target URL to attack")
    parser.add_argument("--method", default="GET", help="HTTP method (default: GET)")
    parser.add_argument("--requests", type=int, default=50, help="Total number of requests")
    parser.add_argument("--concurrency", type=int, default=10, help="Concurrent workers")
    parser.add_argument("--timeout", type=float, default=10.0, help="Request timeout")
    args = parser.parse_args()

    config = LoadTestConfig(
        url=args.url,
        method=args.method,
        total_requests=args.requests,
        concurrency=args.concurrency,
        timeout=args.timeout,
    )

    summary = run_load_test_sync(config)
    print(json.dumps(summary.model_dump(), indent=2))
