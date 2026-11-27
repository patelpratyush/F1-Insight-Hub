FROM python:3.12-slim AS base
COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY packages ./packages
COPY apps/api ./apps/api
RUN uv sync --frozen --no-dev --package f1-api
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
# Client IP for rate limiting comes from TRUSTED_PROXY_HOPS, not uvicorn proxy headers
# (trusting all forwarded IPs would let clients spoof X-Forwarded-For).
CMD ["uvicorn", "f1_api.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--no-proxy-headers"]
