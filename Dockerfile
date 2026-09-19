FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt pyproject.toml ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code and configurations
COPY src/ ./src/
COPY cedar/ ./cedar/
COPY config/ ./config/
COPY scripts/ ./scripts/

# Install the project in editable mode
RUN pip install --no-cache-dir -e .

# Create database directory
RUN mkdir -p /app/.var

# Copy entrypoint script
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

ENV PORT=8000
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/health/live || exit 1

ENTRYPOINT ["/app/docker-entrypoint.sh"]
