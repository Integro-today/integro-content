# Dockerfile for Railway deployment with Agno Therapeutic Workflow
# Multi-stage build: generate requirements.txt from pyproject.toml, then build app

# Stage 1: Generate requirements.txt from pyproject.toml
FROM python:3.11-slim AS requirements-builder

WORKDIR /build

# Install uv for dependency resolution
RUN pip install --no-cache-dir uv

# Copy only dependency files
COPY pyproject.toml .

# Generate requirements.txt with voice extras
RUN uv pip compile pyproject.toml --extra voice -o requirements.txt

# Stage 2: Build the application
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
# Kept all original dependencies except wget (not needed without Qdrant download)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential \
    curl \
    sqlite3 \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Skip Qdrant binary installation - using external Qdrant on Railway
# This saves ~100MB and reduces build time significantly

# Copy auto-generated requirements from builder stage
COPY --from=requirements-builder /build/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Install the package in development mode
RUN pip install -e .

# Create volume directories and set permissions
RUN mkdir -p /app/data/qdrant/storage /app/data/qdrant/snapshots \
             /app/data/backups /app/data/logs \
    && chmod -R 755 /app/data

# Set Railway environment detection
ENV RAILWAY_ENVIRONMENT=production

# Set default volume path if not provided by Railway
ENV RAILWAY_VOLUME_MOUNT_PATH=${RAILWAY_VOLUME_MOUNT_PATH:-/app/data}

# Set therapeutic workflow environment variables
ENV DEFAULT_LLM_PROVIDER=groq
ENV PYTHONUNBUFFERED=1
ENV DISABLE_QDRANT_IF_UNAVAILABLE=true

# Expose port for API
EXPOSE 8888

# Enhanced health check for Railway volume deployment
# Increased start-period to allow for Qdrant initialization
HEALTHCHECK --interval=30s --timeout=15s --start-period=90s --retries=5 \
  CMD curl -f http://localhost:${PORT:-8888}/health || exit 1

# Copy scripts (only .sh and .py files exist)
COPY scripts/*.sh /app/scripts/
COPY scripts/*.py /app/scripts/
# Note: No YAML files in scripts directory - removed to prevent build errors
RUN chmod +x /app/scripts/*.sh

# Default command runs uvicorn with reload/workers tuned by docker-compose
CMD ["sh", "-c", "uvicorn integro.web_server:app --host 0.0.0.0 --port ${PORT:-8888} --workers 2"]