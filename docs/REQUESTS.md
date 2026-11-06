# Inter-Agent Change Requests

Use this file when you need changes outside your owned folder, especially contract modifications.
Only Person 1 may update `/contracts`.

### Template
```markdown
## Request: <Short title>
- **Date:** YYYY-MM-DD
- **From:** Person X (/assigned/folder)
- **Target:** /contracts or /backend/agent etc.
- **Details:** What needs to be changed and why
- **Status:** Open / Accepted / Closed
```


## Request: Mount assess_router in backend/agent/main.py (Optional)
- **Date:** 2026-11-05
- **From:** Person 3 (/backend/assess)
- **Target:** /backend/agent/main.py
- **Details:** Assessment endpoints (`/assess/quiz`, `/assess/flashcards`, `/assess/submit`) are fully implemented in `backend.assess.router.assess_router`. Person 1 can optionally mount `app.include_router(assess_router)` in `main.py` alongside the existing client fallback.
- **Status:** Accepted (Integrated via AssessClient real service bridge with resilient fallback)


## Request: frontend/dashboard package.json Next.js dependency
- **Date:** 2026-11-06
- **From:** Person 1 (/backend/agent)
- **Target:** /frontend/dashboard/package.json
- **Details:** The standalone `frontend/dashboard/index.html` runs cleanly on port 3001 with zero build step. However, `package.json` specifies `"dev": "next dev"` while `"next"` is omitted from `"dependencies"`. If Next.js SSR is intended, please add `"next": "^14.2.0"` (or similar) to `package.json`.
- **Status:** Open


## Request: Mount tts_router in backend/agent/main.py
- **Date:** 2026-11-06
- **From:** Member 2 (/backend/tts, /backend/assess, /backend/learner)
- **Target:** /backend/agent/main.py
- **Details:** Add ElevenLabs TTS router to the main backend application gateway.
  Exact lines for Member 1 to add in `backend/agent/main.py`:
  ```python
  from backend.tts.router import tts_router

  app.include_router(tts_router)
  ```
  This exposes:
  - `POST /tts`: Synthesizes speech with local `cache/tts/` caching and automatic browser fallback (`HTTP 503 {"fallback":"browser"}`).
  - `GET /tts/status`: Operational status endpoint reporting key configuration, default model, and cached files count without leaking secrets.
- **Status:** Open
