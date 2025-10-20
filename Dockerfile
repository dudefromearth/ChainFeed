FROM python:3.11-slim

WORKDIR /app
COPY . /app

RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install redis pytest ruff

ENV PYTHONPATH=/app

# Default entry can be overridden by docker compose `command:`
CMD ["python", "-m", "core.historical_feed_manager"]
