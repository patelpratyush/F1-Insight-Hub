import json
import logging

import pytest
import sentry_sdk
import structlog
from f1_api.config import Settings
from f1_api.logging_setup import configure_logging
from f1_api.middleware.request_id import RequestIdMiddleware
from f1_api.telemetry import setup_telemetry
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient


def test_json_logs_include_request_id(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging("production")
    structlog.contextvars.bind_contextvars(request_id="abc")
    structlog.get_logger().info("hello", job="standings")
    line = capsys.readouterr().out.strip().splitlines()[-1]
    data = json.loads(line)
    assert data["event"] == "hello"
    assert data["request_id"] == "abc"
    assert data["job"] == "standings"
    structlog.contextvars.clear_contextvars()
    logging.getLogger().handlers.clear()


async def test_middleware_binds_and_clears_request_id() -> None:
    app = FastAPI()
    app.add_middleware(RequestIdMiddleware)
    seen: dict[str, object] = {}

    @app.get("/x")
    async def x() -> dict[str, str]:
        seen.update(structlog.contextvars.get_contextvars())
        return {}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        await c.get("/x", headers={"X-Request-ID": "rid-9"})
    assert seen["request_id"] == "rid-9"
    assert "request_id" not in structlog.contextvars.get_contextvars()


def test_telemetry_is_noop_without_config() -> None:
    app = FastAPI()
    setup_telemetry(app, Settings(sentry_dsn=""))
    assert not sentry_sdk.get_client().is_active()


def test_uvicorn_access_logs_are_json_with_request_id(capsys: pytest.CaptureFixture[str]) -> None:
    access = logging.getLogger("uvicorn.access")
    access.handlers = [logging.StreamHandler()]  # what uvicorn's default log config installs
    access.propagate = False
    configure_logging("production")
    structlog.contextvars.bind_contextvars(request_id="rid-7")
    access.info('%s - "%s %s HTTP/%s" %d', "1.2.3.4", "GET", "/healthz", "1.1", 200)
    structlog.contextvars.clear_contextvars()
    data = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert data["logger"] == "uvicorn.access"
    assert data["level"] == "info"
    assert data["request_id"] == "rid-7"
    assert "GET /healthz" in data["event"]
    logging.getLogger().handlers.clear()
