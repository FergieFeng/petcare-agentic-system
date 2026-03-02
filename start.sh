#!/usr/bin/env bash
# PetCare Triage & Smart Booking Agent -- Start Script (macOS / Linux)
# Authors: Syed Ali Turab & Fergie Feng | Team: Broadview | Date: March 1, 2026
#
# Usage: ./start.sh
# Requires: Git, Docker Desktop

set -e

IMAGE_NAME="petcare-agent"
CONTAINER_NAME="petcare-agent"
PORT=5002

echo ""
echo "================================================"
echo "  PetCare Triage & Smart Booking Agent"
echo "================================================"
echo ""

# --- Step 1: Check for .env file ---
if [ ! -f .env ]; then
    echo "No .env file found. Let's set up your API keys."
    echo ""
    cp .env.example .env

    read -p "Enter your OPENAI_API_KEY (or press Enter to skip): " openai_key
    if [ -n "$openai_key" ]; then
        sed -i.bak "s/^OPENAI_API_KEY=.*/OPENAI_API_KEY=$openai_key/" .env
    fi

    read -p "Enter your ANTHROPIC_API_KEY (or press Enter to skip): " anthropic_key
    if [ -n "$anthropic_key" ]; then
        sed -i.bak "s/^ANTHROPIC_API_KEY=.*/ANTHROPIC_API_KEY=$anthropic_key/" .env
    fi

    rm -f .env.bak
    echo ""
    echo "API keys saved to .env (local only, never committed)."
    echo ""
fi

# --- Step 2: Pull latest code ---
echo "Pulling latest code..."
git pull origin PetCare 2>/dev/null || echo "  (not a git repo or no remote — skipping pull)"
echo ""

# --- Step 3: Stop existing container if running ---
if docker ps -q -f name=$CONTAINER_NAME 2>/dev/null | grep -q .; then
    echo "Stopping existing container..."
    docker stop $CONTAINER_NAME 2>/dev/null || true
    docker rm $CONTAINER_NAME 2>/dev/null || true
fi

# --- Step 4: Build Docker image ---
echo "Building Docker image..."
docker build -t $IMAGE_NAME .
echo ""

# --- Step 5: Run container ---
echo "Starting container on port $PORT..."
docker run -d \
    --name $CONTAINER_NAME \
    -p $PORT:$PORT \
    --env-file .env \
    $IMAGE_NAME

echo ""
echo "================================================"
echo "  PetCare Agent is running!"
echo "  Open: http://localhost:$PORT"
echo "================================================"
echo ""
