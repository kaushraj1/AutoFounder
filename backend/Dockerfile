# syntax=docker/dockerfile:1
# Multi-stage build for the AutoFounder AI backend.
# Stage 1 installs dependencies with uv; stage 2 is a slim runtime image.

FROM python:3.12-slim AS builder

# uv: fast, deterministic Python dependency manager (reads pyproject.toml + uv.lock)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Install deps first (cached layer) using only the lockfiles, then the source.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev


FROM python:3.12-slim AS runtime

# Install Terraform CLI — DevOps agent invokes `terraform init -backend=false`
# + `terraform validate -json` against staged copies of infra/terraform/modules/*
# (Path A, no AWS credentials required).
ARG TERRAFORM_VERSION=1.9.8
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl unzip \
    && curl -fsSL "https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip" -o /tmp/tf.zip \
    && unzip /tmp/tf.zip -d /usr/local/bin \
    && rm /tmp/tf.zip \
    && apt-get purge -y unzip curl \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/* \
    && terraform version

# Run as a non-root user (least privilege).
RUN useradd --create-home --uid 10001 appuser
WORKDIR /app

# TF_PLUGIN_CACHE_DIR lets repeated `terraform init` calls inside one task reuse
# the AWS provider download (~90s saved per module after the first init).
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_ENV=production \
    TF_PLUGIN_CACHE_DIR=/home/appuser/.terraform.d/plugin-cache

COPY --from=builder --chown=appuser:appuser /app /app

# Bake the DevOps agent's terraform module templates into the image so the
# tool can stage them at runtime (backend/app/agents/devops/terraform_templates/
# is already inside ./app, this is just a sanity guard).
RUN mkdir -p /home/appuser/.terraform.d/plugin-cache \
    && chown -R appuser:appuser /home/appuser/.terraform.d

USER appuser
EXPOSE 8000

# Health check hits the liveness endpoint.
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0) if urllib.request.urlopen('http://localhost:8000/health').status==200 else sys.exit(1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
