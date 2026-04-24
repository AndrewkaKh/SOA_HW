from __future__ import annotations

import os
import time
from collections.abc import Callable

import httpx
import pytest
from clickhouse_driver import Client


def wait_for_http(url: str, timeout: int = 60) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            response = httpx.get(url, timeout=5.0)
            if response.status_code == 200:
                return
        except httpx.HTTPError:
            pass
        time.sleep(1)
    raise TimeoutError(f"HTTP service did not become ready: {url}")


def wait_for_clickhouse(client: Client, timeout: int = 60) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            result = client.execute("SELECT 1")
            if result and result[0][0] == 1:
                return
        except Exception:
            pass
        time.sleep(1)
    raise TimeoutError("ClickHouse did not become ready")


@pytest.fixture(scope="session")
def producer_base_url() -> str:
    return os.getenv("PRODUCER_BASE_URL", "http://producer:8000")


@pytest.fixture(scope="session")
def clickhouse_client() -> Client:
    return Client(
        host=os.getenv("CLICKHOUSE_HOST", "clickhouse"),
        port=int(os.getenv("CLICKHOUSE_PORT", "9000")),
        database=os.getenv("CLICKHOUSE_DATABASE", "default"),
    )


@pytest.fixture(scope="session", autouse=True)
def wait_for_dependencies(producer_base_url: str, clickhouse_client: Client) -> None:
    wait_for_http(f"{producer_base_url}/health")
    wait_for_clickhouse(clickhouse_client)
