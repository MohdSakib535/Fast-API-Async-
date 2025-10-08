from __future__ import annotations

from typing import Any

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.Database.async_verification_routers import verification_router
from app.Database import async_verification_routers as avr_module
from app.Database.load_test import LoadTestResult


@pytest.fixture
def test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(verification_router)
    return app


@pytest_asyncio.fixture
async def async_client(test_app: FastAPI):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


class _DummySessionContext:
    def __init__(self, value: Any):
        self._value = value

    async def __aenter__(self) -> Any:
        return self._value

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False


@pytest.mark.asyncio
async def test_test_async_database(async_client, monkeypatch):
    dummy_db = object()

    monkeypatch.setattr(
        avr_module,
        "AsyncSessionLocal",
        lambda: _DummySessionContext(dummy_db),
    )

    async def fake_get_books_views(db, limit=1, **kwargs):
        assert db is dummy_db
        assert limit == 1
        return [object()]

    monkeypatch.setattr(avr_module, "get_books_views", fake_get_books_views)

    sleep_calls: list[float] = []

    async def fake_sleep(delay: float):
        sleep_calls.append(delay)

    monkeypatch.setattr(avr_module.asyncio, "sleep", fake_sleep)

    response = await async_client.get("/verification/test-async-db")
    data = response.json()

    assert response.status_code == 200
    assert data["results"] == [1, 1, 1]
    assert data["actual_async"] is True
    assert sleep_calls == [1, 1, 1]


@pytest.mark.asyncio
async def test_test_concurrent_handling(async_client, monkeypatch):
    async def fake_sleep(delay: float):
        assert delay == 2

    monkeypatch.setattr(avr_module.asyncio, "sleep", fake_sleep)

    response = await async_client.get("/verification/test-concurrent")
    data = response.json()

    assert response.status_code == 200
    assert data["message"] == "Request processed"
    assert "thread_id" in data and "process_id" in data
    assert data["processing_time"].startswith("0.")


@pytest.mark.asyncio
async def test_test_async_operations(async_client, monkeypatch):
    sleep_calls: list[float] = []

    async def fake_sleep(delay: float):
        sleep_calls.append(delay)

    monkeypatch.setattr(avr_module.asyncio, "sleep", fake_sleep)

    response = await async_client.get("/verification/test-async-operations")
    data = response.json()

    assert response.status_code == 200
    assert len(data["results"]) == 4
    assert data["is_truly_async"] is True
    assert sorted(sleep_calls) == [0.3, 0.5, 0.8, 1.0]


@pytest.mark.asyncio
async def test_test_sync_vs_async(async_client, monkeypatch):
    call_count = 0

    async def fake_sleep(delay: float):
        nonlocal call_count
        call_count += 1
        assert delay == 0.1

    monkeypatch.setattr(avr_module.asyncio, "sleep", fake_sleep)

    response = await async_client.get("/verification/test-sync-vs-async")
    data = response.json()

    assert response.status_code == 200
    assert data["async_results"] == 10
    assert data["is_truly_async"] is True
    assert call_count == 10


@pytest.mark.asyncio
async def test_trigger_load_test(async_client, monkeypatch):
    async def fake_run_load_test(config):
        return LoadTestResult(
            requests_total=config.total_requests,
            concurrency=config.concurrency,
            successes=5,
            failures=0,
            status_codes={"200": 5},
            min_response_time=0.01,
            max_response_time=0.05,
            average_response_time=0.02,
            p95_response_time=0.04,
            errors=[],
        )

    monkeypatch.setattr(avr_module, "run_load_test", fake_run_load_test)

    payload = {
        "url": "http://example.com",
        "method": "GET",
        "total_requests": 5,
        "concurrency": 2,
        "timeout": 5.0,
    }

    response = await async_client.post("/verification/load-test", json=payload)
    data = response.json()

    assert response.status_code == 200
    assert data["requests_total"] == 5
    assert data["successes"] == 5
    assert data["failures"] == 0
