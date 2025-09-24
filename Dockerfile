FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

# System deps (add build-essential if you compile things)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Copy & install
COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

# Copy project
COPY . /app

# Default port on Render
ENV PORT=8000

# Healthcheck (optional)
HEALTHCHECK --interval=30s --timeout=3s CMD curl -fsS http://localhost:${PORT}/ || exit 1

CMD ["./run.sh"]
