FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY packages ./packages
COPY apps/worker ./apps/worker
RUN uv sync --frozen --no-dev --package f1-worker
ENV PATH="/app/.venv/bin:$PATH"
CMD ["arq", "f1_worker.settings.WorkerSettings"]
