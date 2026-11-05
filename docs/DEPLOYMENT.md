# Deployment Guide: AI Virtual Teacher

This guide covers deploying the AI Virtual Teacher platform to zero-cost, free-tier cloud platforms (Render / Hugging Face Spaces for FastAPI backend, and Vercel / GitHub Pages for Next.js / Static Dashboard).

---

## 1. Environment Variables Checklist

Ensure these variables are configured in `.env` (local) or the cloud deployment dashboard:

```env
# Server Configuration
BACKEND_PORT=8000
LEARNER_PORT=8002
MOCK_MODE=true

# Database Path
LEARNER_DB_PATH=backend/learner/learner.db

# LLM Provider Keys (Optional in MOCK_MODE, Required for Live AI)
GEMINI_API_KEY=AIzaSy...
GROQ_API_KEY=gsk_...
CEREBRAS_API_KEY=csk_...
OPENROUTER_API_KEY=sk-or-...
```

---

## 2. Deploying Backend to Render (Free Web Service)

1. Create a free account at [render.com](https://render.com).
2. Connect your GitHub repository: `https://github.com/<your-username>/Agentic-AI-Educator`.
3. Select **New Web Service**:
   - **Environment:** `Python 3`
   - **Build Command:**
     ```bash
     pip install -r requirements.txt || pip install fastapi uvicorn pydantic requests
     python -m backend.learner.seed
     ```
   - **Start Command:**
     ```bash
     python -m uvicorn backend.agent.main:app --host 0.0.0.0 --port $PORT
     ```
4. In **Environment Variables**, add:
   - `MOCK_MODE=false` (or `true` if demonstrating without API keys)
   - `GEMINI_API_KEY` and `GROQ_API_KEY`
5. Click **Deploy Web Service**. Render provides a live URL (e.g. `https://agentic-teacher.onrender.com`).

---

## 3. Deploying Backend to Hugging Face Spaces (Free Docker / Python)

1. Create a new Space on [huggingface.co/spaces](https://huggingface.co/spaces).
2. Select **FastAPI** or **Docker** SDK.
3. Configure `app.py` in repo root or point directly to `backend.agent.main:app`:
   ```python
   from backend.agent.main import app
   ```
4. In Space Settings $\to$ Repository Secrets, add your API keys.

---

## 4. Deploying Frontend to Vercel (Free Next.js Hosting)

1. Connect your repository to [vercel.com](https://vercel.com).
2. Set Root Directory to `frontend` or repo root.
3. Add Environment Variable:
   - `NEXT_PUBLIC_API_URL=https://<your-render-url>.onrender.com`
4. Click **Deploy**. Vercel will build and assign a global CDN URL.

---

## 5. Standalone Dashboard (GitHub Pages / Local)

The file `frontend/dashboard/index.html` is fully self-contained:
- It requires no node or npm build step.
- It can be opened directly in any browser (`double-click` or `Live Server`).
- It connects automatically to `http://localhost:8000` or `http://localhost:8002` if running, and smoothly falls back to local client state if offline.

---

## 6. Single-Command Local Startup

### Windows:
```cmd
run.bat
```

### macOS / Linux:
```bash
./run.sh
# or
make dev
```

### Verify Endpoints:
- Swagger Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`
- Learner Mastery API: `http://localhost:8000/learner/mastery/demo_student`
- Dashboard: Open `frontend/dashboard/index.html` in browser.
