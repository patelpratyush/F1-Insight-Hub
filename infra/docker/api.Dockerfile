FROM python:3.12-slim AS base
COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY packages ./packages
COPY apps/api ./apps/api
RUN uv sync --frozen --no-dev --package f1-api
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
# Behind the platform proxy (Fly edge): trust X-Forwarded-For so per-IP rate limits see real clients.
CMD ["uvicorn", "f1_api.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
