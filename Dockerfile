# PetCare Triage & Smart Booking Agent -- Dockerfile
#
# Authors: Syed Ali Turab & Fergie Feng | Team: Broadview
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

LABEL maintainer="Syed Ali Turab & Fergie Feng"
LABEL description="PetCare Triage & Smart Booking Agent"
LABEL version="1.0.0"

# ---------------------------------------------------------------------------
# Stage 2: Install Python dependencies
# ---------------------------------------------------------------------------
WORKDIR /app

# Copy requirements first (Docker layer caching: only reinstall if deps change)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---------------------------------------------------------------------------
# Stage 3: Copy application code
# ---------------------------------------------------------------------------
COPY . .

# Create logs directory (needed by the Flask logger)
RUN mkdir -p backend/logs

# ---------------------------------------------------------------------------
# Stage 4: Configure runtime
# ---------------------------------------------------------------------------

# Expose the Flask server port
EXPOSE 5002

# Production environment (disables Flask debug mode)
ENV APP_ENV=production
ENV PORT=5002
ENV PYTHONUNBUFFERED=1

# Health check: verify the server is responding
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5002/api/health')" || exit 1

# ---------------------------------------------------------------------------
# Stage 5: Start the server
# ---------------------------------------------------------------------------

# Production: use Gunicorn (multi-worker WSGI server)
# Falls back to Flask dev server if gunicorn is not installed
CMD ["python", "-c", \
     "import subprocess, sys; \
      try: \
          subprocess.run(['gunicorn', '--bind', '0.0.0.0:5002', '--workers', '2', '--timeout', '120', 'backend.api_server:app'], check=True); \
      except FileNotFoundError: \
          subprocess.run([sys.executable, 'backend/api_server.py'], check=True)"]
