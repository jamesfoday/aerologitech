FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

# App code
COPY . /app

# Ensure the start script is executable (important!)
RUN chmod +x /app/run.sh

# Document a default port (Render sets PORT at runtime)
EXPOSE 10000

# Healthcheck (optional)
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD curl -fsS "http://localhost:${PORT:-10000}/" || exit 1

# Start the app; use shell so env vars expand
CMD ["/bin/bash", "-lc", "/app/run.sh"]
