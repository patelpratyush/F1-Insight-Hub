"""
Wraps successful JSON API responses with `success: true`.

Frontend fetch call sites universally check `data.success` before consuming
a response body -- a contract the routers never satisfied. Rather than
touch every route handler, inject the flag once here so router code stays
free of presentation concerns.
"""
import json

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class SuccessEnvelopeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        if not request.url.path.startswith("/api") or response.status_code >= 400:
            return response

        content_type = response.headers.get("content-type", "")
        if not content_type.startswith("application/json"):
            return response

        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        try:
            data = json.loads(body)
        except ValueError:
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )

        if isinstance(data, dict) and "success" not in data:
            data = {"success": True, **data}

        headers = {k: v for k, v in response.headers.items() if k.lower() != "content-length"}
        return JSONResponse(content=data, status_code=response.status_code, headers=headers)
