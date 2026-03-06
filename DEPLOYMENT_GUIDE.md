# PetCare Triage & Smart Booking Agent -- Deployment Guide

**Authors:** Syed Ali Turab, Fergie Feng & Diana Liu | **Team:** Broadview
**Date:** March 6, 2026

Step-by-step instructions for deploying the PetCare Agent locally, with Docker, and to the cloud.

**Cloud deployment:** **Render** is the recommended option for this POC (free tier, GitHub auto-deploy, HTTPS). Railway is documented as an alternative. Webhook/n8n is **optional** for POC — the app runs fully without it.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Option A: Local Python (Development)](#2-option-a-local-python-development)
3. [Option B: Docker (Recommended)](#3-option-b-docker-recommended)
4. [Option C: Deploy to Render (Cloud -- Free)](#4-option-c-deploy-to-render-cloud----free)
5. [Option D: Deploy to Railway (Cloud -- Alternative)](#5-option-d-deploy-to-railway-cloud----alternative)
6. [Post-Deployment Verification](#6-post-deployment-verification)
7. [Troubleshooting](#7-troubleshooting)

---

## 1. Prerequisites

Before deploying, make sure you have:

| Requirement | Needed For | How to Get It |
|------------|-----------|---------------|
| Git | All options | [git-scm.com](https://git-scm.com/) |
| Python 3.10+ | Option A (local) | [python.org](https://www.python.org/downloads/) |
| Docker Desktop | Option B (Docker) | [docker.com](https://www.docker.com/products/docker-desktop/) |
| GitHub account | Options C/D (cloud) | [github.com](https://github.com/) |
| OpenAI API key | LLM + Voice (Tier 2) + Photo | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) |
| Google Maps API key | Nearby vet finder | [console.cloud.google.com](https://console.cloud.google.com/apis/credentials) |
| Render account | Option C | [render.com](https://render.com/) |
| Railway account | Option D | [railway.app](https://railway.app/) |

### Google Maps API Setup (for Nearby Vet Finder)

To enable the "Find Nearby Vets" feature, you need a Google Maps API key with the Places API (New) enabled:

1. **Get an API Key:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
   - Create a new project (or use existing)
   - Click **Create Credentials** → **API Key**
   - Copy the key (starts with `AIza...`)

2. **Enable Places API (New):**
   - Go to [API Library](https://console.cloud.google.com/apis/library/places.googleapis.com)
   - Search for "Places API (New)" 
   - Click **Enable**
   - **Important:** The old Places API will not work — you must enable "Places API (New)"

3. **Restrict the Key (recommended):**
   - In Credentials, click your API key
   - Under **Application restrictions**, select **HTTP referrers**
   - Add your domain (e.g., `https://your-app.onrender.com/*`)
   - Under **API restrictions**, select **Places API (New)** only

4. **Add to Environment:**
   ```bash
   GOOGLE_MAPS_API_KEY=your-key-here
   ```

**Note:** Google provides $200/month free credit, which covers ~10,000 Places API calls — more than enough for POC testing.

### Get the Code

```bash
git clone https://github.com/FergieFeng/petcare-agentic-system.git
cd petcare-agentic-system
git checkout main
```

---

## 2. Option A: Local Python (Development)

Best for: **development, debugging, and fast iteration**.

### Step 1: Create a Virtual Environment

```bash
python -m venv .venv
```

Activate it:

```bash
# macOS / Linux
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1

# Windows CMD
.venv\Scripts\activate.bat
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables

```bash
cp .env.example .env
```

Open `.env` in your editor and fill in your API keys:

```
OPENAI_API_KEY=sk-your-key-here
```

### Step 4: Start the Server

```bash
cd backend
python api_server.py
```

You should see:

```
2026-03-01 ... [INFO] petcare_api: Starting PetCare API server on port 5002
2026-03-01 ... [INFO] petcare_api: Voice enabled: True
 * Running on http://0.0.0.0:5002
```

### Step 5: Open the App

Open [http://localhost:5002](http://localhost:5002) in your browser.

### Step 6: Test It

1. You should see the chat interface with a welcome message
2. Type "My dog has been vomiting" and press Enter
3. You should get a triage response with urgency tier and guidance
4. Click the mic button to test voice input (Chrome/Edge)

### Stopping the Server

Press `Ctrl+C` in the terminal.

---

## 3. Option B: Docker (Recommended)

Best for: **consistent environment, sharing with teammates, production-like testing**.

### Step 1: Configure Environment Variables

```bash
cp .env.example .env
# Edit .env and add your API keys
```

### Step 2: One-Click Start

**macOS / Linux:**

```bash
./start.sh
```

**Windows:**

```powershell
powershell -ExecutionPolicy Bypass -File start.ps1
```

The script will:
1. Prompt for API keys if `.env` doesn't exist
2. Build the Docker image (~2-3 minutes first time)
3. Start the container on port 5002
4. Print the URL to open

### Step 2 (Alternative): Manual Docker Build

```bash
# Build the image
docker build -t petcare-agent .

# Run the container
docker run -d \
  --name petcare-agent \
  -p 5002:5002 \
  --env-file .env \
  petcare-agent
```

### Step 3: Open the App

Open [http://localhost:5002](http://localhost:5002) in your browser.

### Useful Docker Commands

```bash
# View running containers
docker ps

# View container logs
docker logs petcare-agent

# Follow logs in real-time
docker logs -f petcare-agent

# Stop the container
docker stop petcare-agent

# Remove the container (to rebuild)
docker rm petcare-agent

# Rebuild after code changes
docker build -t petcare-agent . && docker run -d --name petcare-agent -p 5002:5002 --env-file .env petcare-agent
```

### What's Inside the Container

```
petcare-agent:latest
│
├── /app/                          (WORKDIR)
│   ├── backend/
│   │   ├── api_server.py          ← Flask server (entry point)
│   │   ├── orchestrator.py        ← Agent coordinator
│   │   ├── agents/                ← 7 sub-agent Python classes
│   │   ├── data/                  ← Clinic rules, red flags, mock schedule
│   │   └── logs/                  ← Runtime logs (ephemeral)
│   ├── frontend/
│   │   ├── index.html             ← Chat UI
│   │   ├── js/app.js              ← Client-side logic + voice
│   │   └── styles/main.css        ← Styles
│   ├── requirements.txt
│   └── .env                       ← Mounted via --env-file (not in image)
│
├── Python 3.11 + pip packages
└── Exposed: port 5002
```

---

## 4. Option C: Deploy to Render (Cloud -- Free)

Best for: **live demo, sharing a URL with the team, MMAI 891 presentation**.

### Step 1: Push Code to GitHub

Make sure your latest code is pushed:

```bash
git add .
git commit -m "prepare for deployment"
git push -u origin main
```

### Step 2: Create a Render Account

Go to [render.com](https://render.com/) and sign up (free).

### Step 3: Create a New Web Service

1. Click **New** → **Web Service**
2. Connect your GitHub account
3. Select the `petcare-agentic-system` repository
4. Configure:

| Setting | Value |
|---------|-------|
| **Name** | `petcare-agent` |
| **Branch** | `main` |
| **Region** | Oregon (or closest) |
| **Runtime** | Docker |
| **Instance Type** | Free |

### Step 4: Set Environment Variables

In the Render dashboard, go to **Environment** and add:

| Key | Value |
|-----|-------|
| `OPENAI_API_KEY` | `sk-your-key-here` |
| `APP_ENV` | `production` |
| `PORT` | `5002` |

### Step 5: Deploy

Click **Deploy**. Render will:

1. Pull your code from GitHub
2. Build the Docker image
3. Start the container
4. Assign a public URL (e.g., `https://petcare-agent.onrender.com`)

First deploy takes ~5 minutes. Subsequent deploys (on push) take ~2 minutes.

### Step 6: Access the App

Your app is now live at the URL shown in the Render dashboard.

> **Note:** Free tier instances spin down after 15 minutes of inactivity. First request after idle takes ~30-60 seconds (cold start). After that, it's instant.

### Auto-Deploy on Push

Render automatically redeploys when you push to the `main` branch:

```bash
# Make changes, commit, push
git add .
git commit -m "update triage logic"
git push
# Render auto-deploys in ~2 minutes
```

---

## 5. Option D: Deploy to Railway (Cloud -- Alternative)

Best for: **faster cold starts, slightly better free tier**.

### Step 1: Create a Railway Account

Go to [railway.app](https://railway.app/) and sign up.

### Step 2: Create a New Project

1. Click **New Project** → **Deploy from GitHub repo**
2. Select `petcare-agentic-system`, branch `main`
3. Railway auto-detects the Dockerfile

### Step 3: Set Environment Variables

In the Railway dashboard, go to **Variables** and add:

| Key | Value |
|-----|-------|
| `OPENAI_API_KEY` | `sk-your-key-here` |
| `APP_ENV` | `production` |
| `PORT` | `5002` |

### Step 4: Deploy

Railway builds and deploys automatically. It assigns a public URL.

### Step 5: Generate a Domain

Go to **Settings** → **Networking** → **Generate Domain** to get a public URL.

---

## 6. Post-Deployment Verification

After deploying (any option), verify everything works:

### Health Check

```bash
curl https://your-app-url.onrender.com/api/health
```

Expected response:

```json
{
  "status": "ok",
  "timestamp": "2026-03-01T12:00:00.000000",
  "version": "1.0.0",
  "voice_enabled": true
}
```

### Functional Test

1. Open the app URL in your browser
2. You should see the chat UI with a welcome message
3. Type "My cat can't urinate" → should trigger emergency escalation
4. Type "My dog has a mild rash" → should route to routine triage
5. Click the mic button to test voice input

### Checklist

- [ ] App loads in browser without errors
- [ ] `/api/health` returns `{"status": "ok"}`
- [ ] Chat messages send and receive responses
- [ ] Voice button appears (Chrome/Edge)
- [ ] No API key errors in logs

---

## 7. Troubleshooting

### "Module not found" errors

```bash
# Make sure you're in the right directory
cd petcare-agentic-system

# Reinstall dependencies
pip install -r requirements.txt
```

### Docker build fails

```bash
# Clean Docker cache and rebuild
docker system prune -f
docker build --no-cache -t petcare-agent .
```

### Port 5002 already in use

```bash
# Find what's using the port
lsof -i :5002  # macOS/Linux
netstat -ano | findstr :5002  # Windows

# Kill the process, or use a different port
PORT=5003 python backend/api_server.py
```

### Voice not working

- **Chrome/Edge:** Voice should work out of the box
- **Safari:** Partial support; may need to enable in settings
- **Firefox:** Limited; Web Speech API requires flag
- **All browsers:** Must be on HTTPS or localhost (mic requires secure context)

### Render deploy fails

1. Check the build logs in the Render dashboard
2. Ensure `Dockerfile` is in the repo root
3. Ensure the `main` branch is pushed to GitHub
4. Check environment variables are set correctly

### API key errors

```
Voice transcription requires OPENAI_API_KEY
```

- Ensure `OPENAI_API_KEY` is set in `.env` (local) or dashboard (cloud)
- The key must start with `sk-`
- Check [platform.openai.com](https://platform.openai.com/) for billing/usage

### Google Maps API / "Find Nearby Vets" not working

**Symptoms:** Stuck on "Finding nearby vets..." or error message.

**Common causes:**

1. **API Key not set:**
   - Ensure `GOOGLE_MAPS_API_KEY` is set in `.env` or cloud dashboard
   - Key should start with `AIza...`

2. **Wrong API enabled:**
   - Must enable **"Places API (New)"** not the old Places API
   - Check at: https://console.cloud.google.com/apis/library/places.googleapis.com

3. **Billing not enabled:**
   - Google requires a billing account even for free tier
   - You won't be charged until you exceed $200/month

4. **Location permission denied:**
   - Browser must allow location access
   - Check browser settings → Privacy → Location

5. **Testing locally (HTTP):**
   - Browsers block geolocation on non-HTTPS sites (except localhost)
   - Use `http://localhost:5002` for testing, or deploy to HTTPS

**Debug steps:**

```bash
# Test the API key manually
curl "https://places.googleapis.com/v1/places:searchNearby" \
  -H "Content-Type: application/json" \
  -H "X-Goog-Api-Key: YOUR_API_KEY" \
  -H "X-Goog-FieldMask: places.displayName" \
  -d '{
    "locationRestriction": {
      "circle": {
        "center": {"latitude": 43.6532, "longitude": -79.3832},
        "radius": 5000
      }
    }
  }'
```

---

## Architecture Summary

```
User (Browser)
    │
    │  HTTP/HTTPS
    ▼
┌─────────────────────────────────────────┐
│         Docker Container / Host         │
│                                         │
│   Flask Server (port 5002)              │
│   ├── Serves frontend (static files)    │
│   ├── REST API (sessions, messages)     │
│   ├── Voice endpoints (Whisper, TTS)    │
│   └── Orchestrator                      │
│       ├── Agent A: Intake         ──┐   │
│       ├── Agent B: Safety Gate      │   │
│       ├── Agent C: Confidence Gate  │   │
│       ├── Agent D: Triage         ──┤── │──→ OpenAI API
│       ├── Agent E: Routing          │   │
│       ├── Agent F: Scheduling       │   │
│       └── Agent G: Guidance       ──┘   │
│                                         │
│   Data: clinic_rules.json               │
│         red_flags.json                  │
│         available_slots.json            │
└─────────────────────────────────────────┘
```

Everything runs in **one container**, **one process**, **one port**. The only external dependency is the OpenAI API (GPT-4o-mini, Whisper, TTS).
