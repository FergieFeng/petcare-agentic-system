# PetCare Triage & Smart Booking Agent -- Start Script (Windows PowerShell)
# Authors: Syed Ali Turab & Fergie Feng | Team: Broadview | Date: March 1, 2026
#
# Usage: powershell -ExecutionPolicy Bypass -File start.ps1
# Requires: Git, Docker Desktop

$ErrorActionPreference = "Stop"

$IMAGE_NAME = "petcare-agent"
$CONTAINER_NAME = "petcare-agent"
$PORT = 5002

Write-Host ""
Write-Host "================================================"
Write-Host "  PetCare Triage & Smart Booking Agent"
Write-Host "================================================"
Write-Host ""

# --- Step 1: Check for .env file ---
if (-not (Test-Path ".env")) {
    Write-Host "No .env file found. Let's set up your API keys."
    Write-Host ""
    Copy-Item ".env.example" ".env"

    $openai_key = Read-Host "Enter your OPENAI_API_KEY (or press Enter to skip)"
    if ($openai_key) {
        (Get-Content .env) -replace '^OPENAI_API_KEY=.*', "OPENAI_API_KEY=$openai_key" | Set-Content .env
    }

    $anthropic_key = Read-Host "Enter your ANTHROPIC_API_KEY (or press Enter to skip)"
    if ($anthropic_key) {
        (Get-Content .env) -replace '^ANTHROPIC_API_KEY=.*', "ANTHROPIC_API_KEY=$anthropic_key" | Set-Content .env
    }

    Write-Host ""
    Write-Host "API keys saved to .env (local only, never committed)."
    Write-Host ""
}

# --- Step 2: Pull latest code ---
Write-Host "Pulling latest code..."
try {
    git pull origin PetCare 2>$null
} catch {
    Write-Host "  (not a git repo or no remote - skipping pull)"
}
Write-Host ""

# --- Step 3: Stop existing container if running ---
$existing = docker ps -q -f "name=$CONTAINER_NAME" 2>$null
if ($existing) {
    Write-Host "Stopping existing container..."
    docker stop $CONTAINER_NAME 2>$null
    docker rm $CONTAINER_NAME 2>$null
}

# --- Step 4: Build Docker image ---
Write-Host "Building Docker image..."
docker build -t $IMAGE_NAME .
Write-Host ""

# --- Step 5: Run container ---
Write-Host "Starting container on port $PORT..."
docker run -d `
    --name $CONTAINER_NAME `
    -p "${PORT}:${PORT}" `
    --env-file .env `
    $IMAGE_NAME

Write-Host ""
Write-Host "================================================"
Write-Host "  PetCare Agent is running!"
Write-Host "  Open: http://localhost:$PORT"
Write-Host "================================================"
Write-Host ""
