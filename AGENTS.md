# Project: AI Virtual Teacher (hackathon)
Stack: Next.js + FastAPI + SQLite + Pyodide. Free LLM APIs only via backend/agent/llm_router.py.

## Rules for every agent
1. You own ONLY your assigned folder. Never edit another folder. If you need a change
   there, add a request to /docs/REQUESTS.md instead.
2. API shapes live in /contracts (OpenAPI + JSON schemas). Never change a contract
   without telling the human first. Code against the contract, mock the other side.
3. Everyone pushes directly to main, but ONLY files inside your own folder.
   Workflow every time:
   - git pull --rebase origin main (before starting AND before pushing)
   - commit small and often with a clear message prefix: [backend], [frontend], [assess], [learner]
   - git push origin main
   - if push is rejected: pull --rebase again, resolve, push. Never use --force.
   Exception: /contracts can be changed only by Person 1. Others request changes
   in /docs/REQUESTS.md.
4. Never push code that breaks the app's build or startup. Run it locally first.
5. After each task, update /docs/STATUS.md (done / in progress / blocked).
6. All LLM calls go through llm_router.py. No direct provider SDK calls elsewhere.
7. All LLM output must be validated against a schema, with one retry on failure.
8. Prefer simple, working code over clever code. The demo must never crash.

github link : https://github.com/kodisushant/Agentic-AI-Educator