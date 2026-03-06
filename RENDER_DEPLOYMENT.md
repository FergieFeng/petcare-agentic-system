# Render Deployment Guide with Docker + Password Protection

**Date:** March 6, 2026

Step-by-step instructions to deploy the PetCare Triage Agent to Render using Docker with HTTP Basic Auth password protection.

---

## Prerequisites

1. **GitHub account** with your code pushed
2. **Render account** (free tier works) at [render.com](https://render.com)
3. **OpenAI API key** from [platform.openai.com](https://platform.openai.com)
4. **Google Maps API key** (optional, for vet finder) from [Google Cloud Console](https://console.cloud.google.com)

---

## Step 1: Push Your Code to GitHub

Make sure your latest code (with the auth changes) is committed and pushed:

```bash
cd "/Users/syedturab/Desktop/Queens MMAI Course Material/Capstone/MMAI-Capstone-2026-main/petcare-clone"

# Check status
git status

# Add all changes
git add -A

# Commit with a message
git commit -m "feat: add HTTP Basic Auth password protection for deployment"

# Push to main
git push origin main
```

Verify your repo has these files at the root:
- `Dockerfile` ✅
- `requirements.txt` ✅
- `backend/api_server.py` ✅ (with auth code)
- `frontend/` folder ✅
- `.env.example` ✅

---

## Step 2: Create Render Account

1. Go to [render.com](https://render.com)
2. Sign up with your GitHub account (recommended) or email
3. Verify your email

---

## Step 3: Create New Web Service on Render

1. In the Render dashboard, click **"New"** (blue button, top right)
2. Select **"Web Service"**
3. Connect your GitHub account if not already connected
4. Find and select your repository: `petcare-agentic-system`
5. Click **"Connect"**

---

## Step 4: Configure the Service

Fill in these settings:

| Setting | Value |
|---------|-------|
| **Name** | `petcare-agent` (or any name you prefer) |
| **Region** | Oregon (US West) or closest to you |
| **Runtime** | **Docker** (important!) |
| **Branch** | `main` |
| **Root Directory** | (leave blank - uses repo root) |
| **Dockerfile Path** | `./Dockerfile` |

### Instance Type

- **Free** ($0/month) — Good for demo, sleeps after 15 min inactivity
- **Starter** ($7/month) — No cold starts, always on

For MMAI 891 presentation, **Free tier is sufficient**.

---

## Step 5: Add Environment Variables

This is where you configure the app. Click **"Advanced"** to expand, then add:

### Required Variables

| Key | Value | Notes |
|-----|-------|-------|
| `OPENAI_API_KEY` | `sk-your-key-here` | **Required** — Get from platform.openai.com |
| `APP_ENV` | `production` | Tells Flask to run in production mode |
| `PORT` | `5002` | Must match the port in Dockerfile |

### Password Protection (Optional but Recommended)

| Key | Value | Notes |
|-----|-------|-------|
| `AUTH_ENABLED` | `true` | Enables password protection |
| `AUTH_USERNAME` | *(your chosen username)* | Set only via Render dashboard — **never hardcode** |
| `AUTH_PASSWORD` | *(your chosen password)* | Set only via Render dashboard — **never hardcode** |

### Optional: Google Maps (for Vet Finder)

| Key | Value | Notes |
|-----|-------|-------|
| `GOOGLE_MAPS_API_KEY` | `AIza...` | Only if you want "Find Nearby Vets" feature |

### How to Add Variables:

1. Click **"Add Environment Variable"** button
2. Enter Key and Value
3. Click **"Add**" for each variable
4. All values are encrypted and secure

---

## Step 6: Deploy

1. Review all settings
2. Click **"Create Web Service"** (blue button at bottom)
3. Render will:
   - Pull your code from GitHub
   - Build the Docker image (~2-5 minutes)
   - Deploy the container
   - Assign a public URL

4. Wait for the build to complete. You'll see logs like:
   ```
   Building image...
   Successfully built
   Deploying...
   Your service is live at https://petcare-agent.onrender.com
   ```

---

## Step 7: Access Your Protected Site

1. Open the URL (e.g., `https://petcare-agent.onrender.com`)
2. You'll see a browser password prompt
3. Enter the username and password you set in Render's environment variables
4. You're in!

---

## Step 8: Test Everything

After logging in, test these features:

1. **Chat:** Type "My dog has been vomiting"
2. **Triage:** Check that urgency + guidance appears
3. **Booking:** Try booking an appointment
4. **Vet Finder:** Click "Find Nearby Vets" (if Google Maps key set)
5. **Photo Upload:** Try uploading a symptom photo
6. **PDF Export:** Download a triage summary
7. **Voice:** Test mic button (Chrome/Edge)
8. **Dark Mode:** Toggle in header

---

## Troubleshooting

### Build Fails

**Check:**
- Dockerfile exists in repo root
- requirements.txt has all dependencies
- No syntax errors in api_server.py

**View logs:** In Render dashboard → Logs tab

### App Crashes / 502 Error

**Common causes:**
- Missing `OPENAI_API_KEY`
- Wrong `PORT` (must be 5002)

**Fix:** Check Environment variables in Render dashboard

### Password Not Working

**Check:**
- `AUTH_ENABLED` is set to `true` (not `True` or `1`)
- `AUTH_USERNAME` and `AUTH_PASSWORD` are set exactly
- No extra spaces in values

### "Find Nearby Vets" Not Working

**Check:**
- `GOOGLE_MAPS_API_KEY` is set
- Google Places API (New) is enabled in Google Cloud Console
- Billing is enabled on Google Cloud (won't charge until >$200/month)

---

## Updating After Deployment

When you make code changes:

```bash
# Edit files locally
# ... make changes ...

# Commit and push
git add -A
git commit -m "your changes"
git push origin main
```

Render **auto-deploys** when you push to main! Just wait 2-3 minutes.

---

## Custom Domain (Optional)

For a professional demo, add a custom domain:

1. In Render dashboard → Settings → Custom Domain
2. Add your domain (e.g., `petcare.yourname.com`)
3. Follow DNS instructions
4. SSL certificate is auto-provisioned

---

## Security Notes

1. **Never commit `.env` file** to GitHub (it's in .gitignore)
2. **Render encrypts environment variables** automatically
3. **Password is sent over HTTPS** (encrypted in transit)
4. **Health check is public** (`/api/health`) for monitoring
5. **Static files are public** (CSS, JS, icons) — only the app requires auth

---

## Cost Estimate

| Component | Cost |
|-----------|------|
| Render Free Tier | $0/month (sleeps after 15 min) |
| Render Starter | $7/month (always on) |
| OpenAI API | ~$0.01-0.03 per session |
| Google Places API | Free (up to $200/month credit) |

For a 10-15 minute demo: **$0** (use Render Free + OpenAI credits)

---

## Quick Reference

| Task | Command/Action |
|------|----------------|
| Check logs | Render Dashboard → Logs |
| Restart service | Render Dashboard → Manual Deploy → Deploy Latest Version |
| Update env vars | Settings → Environment → Edit |
| View metrics | Metrics tab (CPU, memory, requests) |
| Custom domain | Settings → Custom Domain |

---

## Support

- **Render docs:** [render.com/docs](https://render.com/docs)
- **Flask docs:** [flask.palletsprojects.com](https://flask.palletsprojects.com)
- **OpenAI API:** [platform.openai.com](https://platform.openai.com)

---

**Your PetCare Triage Agent is now live and password-protected!** 🐾
