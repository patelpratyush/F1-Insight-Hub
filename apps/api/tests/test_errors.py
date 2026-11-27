from httpx import AsyncClient


async def test_unknown_route_returns_problem_json_with_request_id(client: AsyncClient) -> None:
    resp = await client.get("/v1/nope", headers={"X-Request-ID": "req-123"})
    assert resp.status_code == 404
    assert resp.headers["content-type"].startswith("application/problem+json")
    assert resp.headers["x-request-id"] == "req-123"
    body = resp.json()
    assert body["status"] == 404
    assert body["request_id"] == "req-123"


async def test_request_id_generated_when_absent(client: AsyncClient) -> None:
    resp = await client.get("/healthz")
    assert len(resp.headers["x-request-id"]) >= 16
