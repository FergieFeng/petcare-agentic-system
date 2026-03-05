# PetCare Triage & Smart Booking Agent -- Dockerfile
#
# Authors: Syed Ali Turab, Fergie Feng & Diana Liu | Team: Broadview
# Date:   March 1, 2026
#
# Single-container deployment for the PetCare Agent.
# Bundles: Python backend + Flask API + 7 sub-agents + frontend + data files.
#
# Build:  docker build -t petcare-agent .
# Run:    docker run -p 5002:5002 --env-file .env petcare-agent
#
# The container:
#   - Uses python:3.11-slim as base (~150MB)
#   - Installs Python dependencies from requirements.txt
#   - Copies all application code (backend, frontend, data, docs)
#   - Runs the Flask server via Gunicorn (production WSGI server)
#   - Exposes port 5002
#   - Expects API keys via --env-file .env (never baked into the image)

# ---------------------------------------------------------------------------
# Stage 1: Base image with Python
# ---------------------------------------------------------------------------
FROM python:3.11-slim

LABEL maintainer="Syed Ali Turab, Fergie Feng & Diana Liu"
LABEL description="PetCare Triage & Smart Booking Agent"
LABEL version="2.0.0"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p backend/logs

EXPOSE ${PORT:-5002}

ENV APP_ENV=production
ENV PORT=5002
ENV PYTHONUNBUFFERED=1

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen(f'http://localhost:{__import__(\"os\").getenv(\"PORT\",\"5002\")}/api/health')" || exit 1

CMD sh -c "gunicorn --bind 0.0.0.0:${PORT:-5002} --workers 2 --timeout 120 backend.api_server:app"
