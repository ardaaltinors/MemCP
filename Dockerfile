# =============================================================================
# Multi-stage Dockerfile for Memory MCP Server
# Optimized for production with minimal image size and security best practices
# =============================================================================

# =============================================================================
# Stage 1: Base UV installer
# =============================================================================
FROM python:3.11-slim as uv-installer

# Install UV package manager
RUN pip install --no-cache-dir uv

# =============================================================================
# Stage 2: Dependencies builder
# =============================================================================
FROM uv-installer as dependencies

# Set working directory
WORKDIR /app

# Copy UV configuration files
COPY pyproject.toml uv.lock ./

# Install dependencies in isolated environment
# Using --no-dev to exclude development dependencies
RUN uv sync --frozen --no-dev --no-cache

# =============================================================================
# Stage 3: Application builder
# =============================================================================
FROM dependencies as builder

# Copy source code
COPY . .

# Remove unnecessary files for production
RUN rm -rf \
    .git \
    .gitignore \
    .cursor \
    docs \
    src/tests \
    docker-compose*.yml \
    README.md \
    .env.example

# Create optimized Python bytecode but keep source files for now
RUN python -m compileall src/ && \
    find . -name "__pycache__" -exec rm -rf {} + || true

# =============================================================================
# Stage 4: Production runtime
# =============================================================================
FROM python:3.11-slim as production

# Install system dependencies and security updates
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
        netcat-openbsd && \
    apt-get upgrade -y && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid 1000 --shell /bin/bash --create-home appuser

# Set working directory
WORKDIR /app

# Copy UV from builder stage
COPY --from=uv-installer /usr/local/bin/uv /usr/local/bin/uv
COPY --from=uv-installer /usr/local/lib/python3.11/site-packages/uv* /usr/local/lib/python3.11/site-packages/

# Copy virtual environment from dependencies stage
COPY --from=dependencies /app/.venv /app/.venv

# Copy application code from builder stage
COPY --from=builder --chown=appuser:appuser /app .

# Copy and set up entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Ensure virtual environment is in PATH
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"

# Security and optimization environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create necessary directories and set permissions
RUN mkdir -p /app/logs && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose application port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Set entrypoint and default command
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["python", "main.py"]

# =============================================================================
# Build metadata
# =============================================================================
LABEL maintainer="Altinors"
LABEL version="0.0.1"
LABEL description="Memory MCP Server"
LABEL org.opencontainers.image.source="https://github.com/ardaaltinors/MemCP" 