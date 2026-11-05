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
- **Status:** Open
