# AI-Powered Interactive Virtual Teacher: Project Context

Hackathon domain: **Agentic AI, Education & Learning**
Team: 4 people, working separately, each using an AI coding agent (Antigravity, Codex, etc.)
Repo: `https://github.com/<your-username>/<repo-name>` (branch: `main`)
Constraint: **free LLM API keys only**

---

## 1. Problem statement (summary)

Build an AI teacher that delivers a personalized, classroom-like experience. It must:

1. **Interactive teaching:** explain step by step on a digital whiteboard (diagrams, equations, visuals).
2. **Live coding:** write, execute and explain code in real time.
3. **Adaptive learning:** detect what a student struggles with from answers, mistakes and progress.
4. **Personalized assessment:** generate topic-specific quizzes and flashcards.
5. **Progress tracking:** keep a learning record, highlight weak areas, recommend what to practice.

## 2. Biggest risk

Scope. Five features plus four people working separately can produce four half-working parts and a broken demo. Build **one thin end-to-end slice early**, then deepen it. Pick ONE demo topic (e.g. gradient descent or Python recursion).

## 3. Architecture

- **Frontend:** React/Next.js, Excalidraw or tldraw (whiteboard), KaTeX (equations), Mermaid (diagrams), Monaco (code editor).
- **Live coding:** **Pyodide** runs Python in the browser (no sandbox server, free, reliable demo).
- **Backend:** FastAPI + SQLite.
- **Voice (optional):** browser Web Speech API for TTS/STT.
- **Agent loop (the "agentic" part):** plan, teach, check understanding, adapt. The LLM calls tools:
  `draw_on_board`, `run_code`, `ask_check_question`, `generate_quiz`, `update_mastery`, `recommend_next`.
- **Whiteboard approach:** LLM outputs a **validated JSON list of board commands** (text, box, arrow, equation, mermaid); the frontend renders them step by step. Do not ask the LLM for raw SVG or images.
- **Adaptive model:** per-concept mastery score (exponentially weighted average from quiz/exercise results, with decay) plus misconception tags extracted from wrong answers. Weak concepts feed the next lesson, quizzes and flashcards.

## 4. Free LLM APIs

Numbers change often and sources disagree. **Verify in each provider dashboard.**

| Provider | Use for | Notes |
|---|---|---|
| Google Gemini API (AI Studio) | Main lesson generation, large context | Pro models moved to paid in April 2026; Google stopped publishing free-tier limits on docs, so check your dashboard |
| Groq | Fast, interactive replies | Reported ~30 RPM and ~14,400 req/day on small models; exact limits are per-organisation in account settings |
| Cerebras | Batch jobs (pre-generating quizzes) | Reported ~1M tokens/day but only ~5 RPM, so not for live chat |
| OpenRouter `:free` | Backup only | ~20 req/min, ~50 req/day unless you buy credits; free model IDs expire |
| Mistral free / Cohere trial | Extra fallbacks | |

**Practical rules**
- Use a router in the backend with fallback order: Gemini, Groq, Cerebras, OpenRouter (LiteLLM or ~50 lines of your own).
- Every teammate creates their own keys (also multiplies rate limits). Rotate during demo.
- Cache responses; pre-generate and store the demo lesson content.
- Validate every LLM response with Pydantic and retry once on failure (small models are flaky at structured output).
- Free tiers may train on your prompts: no real student data.

## 5. Roles and ownership

| # | Role | Owns (folder) |
|---|---|---|
| 1 | **Tech lead + Agent brain:** LLM router, teacher loop, tool calling, schemas, contracts | `/backend/agent`, `/contracts` |
| 2 | **Classroom frontend:** whiteboard renderer, chat, step playback, voice | `/frontend/classroom` |
| 3 | **Live coding + assessment:** Pyodide runner, code-explain mode, quizzes and flashcards (generation + UI) | `/frontend/code`, `/frontend/quiz`, `/backend/assess` |
| 4 | **Learner model + dashboard + demo owner:** DB, mastery tracking, dashboard, seed data, README, pitch, demo script, deployment | `/backend/learner`, `/frontend/dashboard`, `/docs` |

## 6. Git workflow (decided)

- Everyone **pushes directly to `main`, but only inside their own folder.**
- `/contracts` can only be changed by Person 1. Others request changes in `/docs/REQUESTS.md`.
- Workflow every time: `git pull --rebase origin main`, commit small with prefix (`[backend]`, `[frontend]`, `[assess]`, `[learner]`), `git push origin main`. If rejected: pull --rebase again, resolve, push. **Never force-push.**
- Never push code that breaks build or startup; run locally first.
- Tag known-good commits (`git tag stable-1`) every time the slice works end to end, so you can roll back fast.
- Keep `.gitignore` and `.env.example` from the first commit. If a key is ever pushed, **rotate it immediately** (deleting the commit is not enough).
- Repo owner must add all teammates as collaborators with write access, and each person must be logged in to git (`gh auth login` or a personal access token).

## 7. Working separately: what that changes

- Agents only see what is on GitHub; **the repo is the only coordination channel.**
- Per-person setup:
  ```
  git clone https://github.com/<you>/<repo>.git
  cd <repo>
  cp .env.example .env   # fill in your own keys
  ```
  Open the cloned folder in the agent (Antigravity / Codex).
- Keys never go in the repo (`.env` is gitignored). Share only via a private chat.
- Pull at the start of every task and every 30-60 min; push after every finished feature. Read `/docs/STATUS.md` and `/docs/REQUESTS.md` after each pull.
- **Contracts and mocks first:** Person 1 pushes contracts + a mock backend (`MOCK_MODE=true`) within the first hour. Everyone must be able to run their part in two commands (document in README).
- `STATUS.md` has one section per person; each edits only their own section (avoids merge conflicts).
- Sync rhythm: a 10-minute call every 2-3 hours; Person 1 pulls everything, runs the full app, posts "works / broken: X".
- Deploy early so everyone sees the integrated state at one URL: backend on Render or Hugging Face Spaces, frontend on Vercel. Person 4 owns this.

## 8. AGENTS.md (put at repo root)

For Codex, `AGENTS.md` is read automatically. For Antigravity, also paste the same text into its rules/instructions file (not certain it reads `AGENTS.md` by default).

```
# Project: AI Virtual Teacher (hackathon)
Repo: https://github.com/<your-username>/<repo-name>
Branch: main (everyone pushes here, inside their own folder only)
Stack: Next.js + FastAPI + SQLite + Pyodide. Free LLM APIs only via backend/agent/llm_router.py.

## Rules for every agent
1. You own ONLY your assigned folder. Never edit another folder. If you need a change
   there, add a request to /docs/REQUESTS.md instead.
2. API shapes live in /contracts (OpenAPI + JSON schemas). Never change a contract
   without telling the human first. Code against the contract, mock the other side.
3. Everyone pushes directly to main, but ONLY files inside your own folder.
   Workflow every time:
   - git pull --rebase origin main (before starting AND before pushing)
   - commit small and often with a prefix: [backend], [frontend], [assess], [learner]
   - git push origin main
   - if push is rejected: pull --rebase again, resolve, push. Never use --force.
   Exception: /contracts can be changed only by Person 1. Others request changes
   in /docs/REQUESTS.md.
4. Never push code that breaks the app's build or startup. Run it locally first.
5. Never commit secrets. Keys go in .env (gitignored); update .env.example.
6. After each task, update your section of /docs/STATUS.md (done / in progress / blocked).
7. All LLM calls go through llm_router.py. No direct provider SDK calls elsewhere.
8. All LLM output must be validated against a schema, with one retry on failure.
9. Run git pull --rebase at the START of every task and every ~30-60 min.
   Push after every finished feature. Read /docs/STATUS.md and /docs/REQUESTS.md after every pull.
10. Prefer simple, working code over clever code. The demo must never crash.
```

## 9. Prompts per person's agent

**Everyone, first message:**
> Read AGENTS.md and /contracts before writing code. Confirm your owned folder and summarize your task in 5 lines, then start. Build a minimal working version first, then improve.

**Person 1: Agent brain**
> Build the backend teacher agent in /backend/agent. (1) llm_router.py: provider fallback Gemini, Groq, Cerebras, OpenRouter using env keys, with retry, timeout, and a disk cache. (2) A tool-calling loop where the teacher can call: draw_on_board, run_code, ask_check_question, generate_quiz, update_mastery, recommend_next. (3) Define Pydantic schemas for board commands (text, box, arrow, equation, mermaid) and publish them in /contracts as JSON schema + OpenAPI. (4) A /lesson/step streaming endpoint that returns the next teaching step as validated JSON. Also write a mock mode that returns a canned lesson so teammates aren't blocked. Commit contracts within the first hour.

**Person 2: Classroom frontend**
> Build the classroom UI in /frontend/classroom. Use the contracts for board commands. Render commands on an Excalidraw/tldraw canvas with KaTeX equations and Mermaid diagrams, animated step by step with a narration caption panel and a chat box. Add play/pause/next-step and an "I don't understand" button that sends feedback to the agent. Use the mock backend until the real one is ready. Make it look polished, since the demo depends on it. Add browser TTS for narration as a toggle.

**Person 3: Coding + assessment**
> Build in /frontend/code and /frontend/quiz and /backend/assess. (1) Monaco editor + Pyodide runner that executes Python in-browser and returns stdout/errors. (2) "Live coding" mode: the agent supplies code in chunks, each chunk is typed into the editor, executed, and explained with the output shown. The student can edit and re-run; errors get sent back to the agent. (3) Endpoints and UI for topic-specific MCQ quizzes and flashcards generated from the student's weak concepts, with schema-validated output and per-question concept tags. Submitted answers must post to the learner API in /contracts.

**Person 4: Learner model + dashboard + demo**
> Build in /backend/learner and /frontend/dashboard and /docs. SQLite tables: users, concepts, attempts, mastery, misconceptions. Mastery = exponentially weighted score per concept, updated from quiz and exercise results, with decay over time. Endpoints: record_attempt, get_mastery, get_weak_concepts, recommend_next. Dashboard: mastery heatmap/bar chart, weak-area list, recommended next topics, history timeline. Seed realistic demo data for a student persona. Also own README, architecture diagram, 3-minute demo script, pitch deck outline, and early deployment (Render/HF Spaces + Vercel).

## 10. Timeline (scale to hackathon length)

- **First hour, everyone together:** pick ONE demo topic, set up repo and keys, Person 1 commits contracts and mocks. Nobody builds before contracts exist.
- **First third:** each part works alone against mocks.
- **By halfway (the gate):** one full vertical slice works: teach, whiteboard, live code, check question, quiz, mastery update, dashboard. If not, cut features.
- **Last third:** polish, fallbacks, bug bash, pitch rehearsal.
- **Feature freeze:** 3-4 hours before submission.

## 11. What wins

- **Demo, not features.** Script a 3-minute story: student gets a concept wrong, the agent notices the specific misconception, re-explains differently, generates a targeted quiz, and the dashboard shows the weak area improving.
- **Show the agent's reasoning visibly** (e.g. "Detected: confuses learning rate with epochs") so it looks agentic, not a chatbot with a whiteboard.
- **Record a backup demo video** and pre-cache the demo lesson; live APIs fail on stage.
- **Be honest about limits** in Q&A (heuristic mastery model, free-tier limits). Judges push on this.

## 12. Open questions

- Hackathon duration?
- Required stack or a mandatory deployed link?
- Which demo topic does the team pick?
- Who owns deployment (suggested: Person 4)?
