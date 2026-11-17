import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import httpx
import jwt
from fastapi import Request

from f1_api.errors import ProblemError


@dataclass(frozen=True)
class Principal:
    user_id: str
    email: str | None


class JwtVerifier:
    def __init__(
        self,
        jwks_url: str,
        issuer: str,
        jwks_loader: Callable[[], dict[str, Any]] | None = None,
        ttl: float = 300.0,
        min_refresh: float = 30.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.jwks_url, self.issuer, self.ttl = jwks_url, issuer, ttl
        self.min_refresh = min_refresh
        self._clock = clock
        self._loader = jwks_loader or self._fetch
        self._cache: dict[str, Any] | None = None
        self._fetched_at = 0.0

    def _fetch(self) -> dict[str, Any]:
        resp = httpx.get(self.jwks_url, timeout=5.0)
        resp.raise_for_status()
        data: dict[str, Any] = resp.json()
        return data

    def _jwks(self, force: bool = False) -> dict[str, Any]:
        age = self._clock() - self._fetched_at
        # A forced refresh (unknown kid) is allowed at most once per `min_refresh`
        # seconds, so forged kids cannot turn every request into a JWKS fetch.
        if self._cache is None or age > self.ttl or (force and age >= self.min_refresh):
            self._cache = self._loader()
            self._fetched_at = self._clock()
        return self._cache

    def verify(self, token: str) -> Principal:
        unauthorized = ProblemError(401, "Unauthorized", "Invalid or expired token")
        try:
            header = jwt.get_unverified_header(token)
            kid = header.get("kid")
            for force in (False, True):
                keys = {k["kid"]: k for k in self._jwks(force)["keys"]}
                if kid in keys:
                    break
            else:
                raise unauthorized
            key = jwt.PyJWK(keys[kid]).key
            claims = jwt.decode(
                token,
                key,
                algorithms=["EdDSA", "RS256"],
                issuer=self.issuer,
                options={"require": ["exp", "iss", "sub"]},
            )
        except ProblemError:
            raise
        except Exception as exc:
            raise unauthorized from exc
        return Principal(user_id=str(claims["sub"]), email=claims.get("email"))


def current_principal(request: Request) -> Principal:
    header = request.headers.get("authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise ProblemError(401, "Unauthorized", "Missing bearer token")
    verifier: JwtVerifier = request.app.state.verifier
    return verifier.verify(token)
