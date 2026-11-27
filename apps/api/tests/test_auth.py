import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from f1_api.auth.jwt import JwtVerifier, Principal, current_principal
from f1_api.errors import ProblemError, install_error_handlers
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient

ISSUER = "http://auth.test"


@pytest.fixture(scope="module")
def key() -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def _token(key: rsa.RSAPrivateKey, **over: object) -> str:
    claims = {"sub": "u1", "email": "a@b.c", "iss": ISSUER, "exp": int(time.time()) + 300, **over}
    return jwt.encode(claims, key, algorithm="RS256", headers={"kid": "k1"})


def _app(key: rsa.RSAPrivateKey) -> FastAPI:
    jwk = jwt.algorithms.RSAAlgorithm.to_jwk(key.public_key(), as_dict=True)
    jwk.update({"kid": "k1", "alg": "RS256", "use": "sig"})
    verifier = JwtVerifier("http://auth.test/jwks", ISSUER, jwks_loader=lambda: {"keys": [jwk]})
    app = FastAPI()
    app.state.verifier = verifier
    install_error_handlers(app)

    @app.get("/me")
    async def me(p: Principal = Depends(current_principal)) -> dict[str, str | None]:  # noqa: B008
        return {"user_id": p.user_id, "email": p.email}

    return app


async def _get(key: rsa.RSAPrivateKey, header: str | None) -> int:
    async with AsyncClient(transport=ASGITransport(app=_app(key)), base_url="http://t") as c:
        r = await c.get("/me", headers={"Authorization": header} if header else {})
        return r.status_code


async def test_valid_token_ok(key: rsa.RSAPrivateKey) -> None:
    assert await _get(key, f"Bearer {_token(key)}") == 200


async def test_missing_header_401(key: rsa.RSAPrivateKey) -> None:
    assert await _get(key, None) == 401


async def test_expired_401(key: rsa.RSAPrivateKey) -> None:
    assert await _get(key, f"Bearer {_token(key, exp=int(time.time()) - 10)}") == 401


async def test_wrong_issuer_401(key: rsa.RSAPrivateKey) -> None:
    assert await _get(key, f"Bearer {_token(key, iss='http://evil')}") == 401


async def test_garbage_token_401(key: rsa.RSAPrivateKey) -> None:
    assert await _get(key, "Bearer not-a-jwt") == 401


async def test_signed_with_other_key_401(key: rsa.RSAPrivateKey) -> None:
    other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    assert await _get(key, f"Bearer {_token(other)}") == 401


def test_unknown_kid_refetch_is_rate_limited(key: rsa.RSAPrivateKey) -> None:
    jwk = jwt.algorithms.RSAAlgorithm.to_jwk(key.public_key(), as_dict=True)
    jwk.update({"kid": "k1", "alg": "RS256", "use": "sig"})
    calls = 0
    now = [1000.0]

    def loader() -> dict[str, object]:
        nonlocal calls
        calls += 1
        return {"keys": [jwk]}

    verifier = JwtVerifier(
        "http://auth.test/jwks", ISSUER, jwks_loader=loader, clock=lambda: now[0]
    )
    forged = jwt.encode(
        {"sub": "u", "iss": ISSUER, "exp": int(time.time()) + 60},
        key,
        algorithm="RS256",
        headers={"kid": "unknown"},
    )
    for _ in range(50):
        with pytest.raises(ProblemError):
            verifier.verify(forged)
    assert calls == 1  # initial load only; forced refresh suppressed within interval

    now[0] += 31
    with pytest.raises(ProblemError):
        verifier.verify(forged)
    assert calls == 2  # one forced refresh allowed after the interval

    assert verifier.verify(_token(key)).user_id == "u1"  # known kid still verifies
