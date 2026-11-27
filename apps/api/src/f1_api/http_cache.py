import hashlib
import json

from fastapi import Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

CACHE = "public, max-age=60, stale-while-revalidate=300"


def cached_json(request: Request, payload: object) -> Response:
    body = json.dumps(jsonable_encoder(payload), separators=(",", ":"), sort_keys=True)
    etag = 'W/"' + hashlib.sha256(body.encode()).hexdigest()[:24] + '"'
    headers = {"ETag": etag, "Cache-Control": CACHE}
    if request.headers.get("if-none-match") == etag:
        return Response(status_code=304, headers=headers)
    return JSONResponse(json.loads(body), headers=headers)
