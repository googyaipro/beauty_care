FROM python:3.11-slim

WORKDIR /app

# Ensure Python looks at /app for all module imports
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
RUN pip install --no-cache-dir uv

# Copy pyproject.toml and source code
COPY pyproject.toml .
COPY README.md .
COPY common/ common/
COPY locales/ locales/
COPY registry_server/ registry_server/
COPY mcp_servers/ mcp_servers/
COPY agents/ agents/
COPY gateways/ gateways/
COPY admin_cms/ admin_cms/

# Install dependencies in editable mode to ensure live module updates
RUN uv pip install --system --no-build-isolation -e .

EXPOSE 8000 8014 8015 8016 8019 8021 8022

CMD ["python3", "registry_server/server.py"]
