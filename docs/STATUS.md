# Team Status Board

## Person 1: Tech lead + Agent brain (/backend/agent, /contracts)
- **Status:** All Sprint Tasks Complete & Synced with Teammates (0 Conflicts)
- **Completed Tasks:**
  1. **Honesty Check:** Re-ran e2e & tests with `REAL_LLM=1`. All 10 steps PASS using mock/rule-based engines (API keys blank in local `.env`). STATUS.md honestly marks cloud LLM calls as MOCK/FALLBACK.
  2. **Safe Imports:** Wrapped learner & assess service imports in try/except with graceful fallback chain: in-process → HTTP → mock. `/health` exposes `services.learner.mode` and `services.assess.mode`.
  3. **Demo Topic (Recursion):** Full 5-step cached lesson (base case, call stack, tree recursion, vs iteration). Added `/demo/seed` and `/demo/reset` endpoints reusing Person 4's `seed.py`.
  4. **Agent Trace:** Added `AgentTrace` model (detected_misconception, strategy_chosen, mastery_before, mastery_after, provider_used) to `/lesson/step` and `/agent/chat` responses. Contracts updated.
  5. **Deploy:** Extended `/health` with per-provider key reachability. Added `render.yaml`, `requirements.txt`, deployment section in `README.md`. Lifespan auto-seeds SQLite on ephemeral disk (Render).
  6. **Contract Freeze:** All 16 endpoints in `openapi.json` annotated with `x-stability`:
     - **Stable (12):** `/health`, `/lesson/step`, `/lesson/check-answer`, `/mock/lesson`, `/agent/chat`, `/learner/attempt`, `/learner/mastery/{user_id}`, `/learner/weak/{user_id}`, `/learner/recommend/{user_id}`, `/assess/quiz`, `/assess/flashcards`, `/assess/submit`
     - **May-change (4):** `/lesson/step/stream`, `/tools/execute`, `/demo/seed`, `/demo/reset`
  7. **Single-Command Full Stack Launcher:** Added `start_all.bat` (Windows) and `start_all.sh` (Mac/Linux), plus matching `stop_all.bat` and `stop_all.sh`. Automatically verifies runtimes (Python, Node, npm), creates `.env` with key instructions if missing, supports `mock`/`real` mode flags, installs missing dependencies, launches backend on port 8000 + classroom UI on port 3000 + dashboard UI on port 3001 in separate terminal windows, verifies health, and launches browser. Enhanced gateway CORS and added summary/history pass-through routes for dashboard.
  8. **Teammate Sync & Integration Verification:** Rebased cleanly over Person 2's Pyodide live coding runner and freehand annotation tool commits (`85378e9`, `becce91`). Verified that all contracts, board commands, and endpoints remain 100% compatible.
- **What is REAL & VERIFIED:**
  - Learner Model, Assessment Engine, Teacher Rule Engine, Whiteboard Commands, FastAPI, all test suites (100% pass), and full-stack multi-service single-command launcher verified across ports 8000, 3000, 3001.
- **What is MOCK/FALLBACK:**
  - Cloud LLM calls (API keys blank in `.env`). Falls back safely to deterministic rule-based engine.
- **What is BROKEN:** None.
- **Teammate Blockers:** None.

---

## Person 2 / Member 3: Classroom UI (/frontend/classroom)
- **Status:** Complete, Redesigned & Verified (High-Contrast Theme, Real Tabs, 100dvh Layout, Contrast Audit)
- **Implemented & Verified:**
  - **Whiteboard Contrast & Theming:** Added explicit whiteboard CSS tokens (`--board-bg`, `--board-ink`, `--cell-bg`, `--cell-ink`, `--cell-border`, `--pointer-low`, `--pointer-high`, `--pointer-mid`, `--board-equation-bg`, `--board-equation-text`) for both light and dark modes. Overrides hardcoded box fills and text colors so array cells, math equations, and labels remain crisp in dark mode.
  - **Dark-Mode Aware Diagrams & KaTeX:** Mermaid diagrams dynamically initialize with neutral/dark theme palettes and listener for color-scheme changes; KaTeX equations use board equation tokens.
  - **Pointer Positioning:** Low/mid/high pointer arrows now render with low/high/mid labels positioned safely in a reserved row under the cells without overlapping arrows or cell contents.
  - **Single Active Tab View:** Enforced tab layout via CSS (`display: none !important` on `.hidden`) and JS so exactly one panel (Chat, Quiz, or Code) is displayed at a time, each taking 100% height with its own internal scroll. Chat input is pinned at the bottom and message list scrolls. Quiz notification dot appears only when a new question arrives.
  - **App Shell & Player Bar (100dvh):** Migrated `.classroom-app` to a 3-row CSS Grid (`52px 1fr 56px`) with `height: 100dvh; min-height: 0`, guaranteeing the bottom player bar is permanently anchored and never cut off at any viewport size (1280x720, 1024x700). Right panel widened to 420px.
  - **Header & Sidebar Synchronization:** Unified topic selection state via `syncTopicState()`. Header concept badge dynamically updates alongside sidebar active items to prevent state mismatches.
  - **Learner Dashboard Sizing & Typography:** Restyled `frontend/dashboard/index.html` with 24px+ card padding, exact type scale (28px header, 18px card titles, 16px body, 13px meta), charts >= 320px with un-truncated labels (`autoSkip: false`, font size 13px), and 2-column layout at 1280px collapsing to 1 column below 900px.
  - **WCAG AA Contrast Audit Utility:** Implemented `window.auditContrast()` in both classroom and dashboard, checking text nodes against effective background luminance (3:1 for large text, 4.5:1 for body text). All UI token pairs verify between 4.97:1 and 17.4:1 ratio.
- **Tested & Verified:**
  - Verified static HTTP serving via `python -m http.server 3000 --directory frontend/classroom`.
  - Verified plugin mount points and guarded calls with zero runtime errors.
  - Verified topic picker, fallback generation, voice playback fallback, and auto-layout styling.
  - Verified WCAG contrast math across all light and dark mode token pairs.
- **What is REAL & VERIFIED:**
  - Standalone Classroom HTML5 UI (`frontend/classroom/index.html`), stylesheets (`theme.css`, `layout.css`, `components.css`), and Dashboard (`frontend/dashboard/index.html`).
- **Teammate Blockers:** None.

---

## Person 3: Live coding + assessment (/frontend/code, /frontend/quiz, /backend/assess)
- **Status:** Complete, Tested & Integrated
- **Implemented:**
  - **In-Browser Python Editor & Pyodide:** `frontend/code/usePyodide.ts` with Pyodide WebAssembly runtime, standard I/O capture (`sys.stdout`/`sys.stderr`), and labeled simulation fallback.
  - **Monaco & Progressive Live Coding Runner:** `frontend/code/PythonEditor.tsx` and `frontend/code/LiveCodingRunner.tsx` with progressive character typing, Pause/Resume/Skip controls, explanation panel, and runtime error reporting to `POST /agent/chat`.
  - **MCQ Quiz Interface:** `frontend/quiz/QuizView.tsx` with concept tag badges, option selection, score calculation, pedagogical feedback, and automatic synchronization to `POST /learner/attempt`.
  - **Spaced Repetition Flashcards:** `frontend/quiz/FlashcardDeck.tsx` with 3D flip card animations, front/back reveals, hint triggers, and confidence self-assessment ratings.
  - **Unified Assessment Hub:** `frontend/quiz/AssessmentHub.tsx` combining topic quizzes, flashcards, and automated targeting of student weak concepts via `GET /learner/weak/{user_id}`.
  - **Assessment Backend & Router:** `backend/assess/service.py`, `backend/assess/router.py`, and `backend/assess/main.py` matching `/contracts/openapi.json`.
- **Tested:**
  - `backend/assess/test_assess.py` (5 unit & integration tests covering schema compliance, scoring, misconception diagnosis, attempt recording, edge cases, and router mounting via TestClient: all 5 passed).
  - `backend/agent/test_agent.py` (full agent suite: passed).
- **Integrated:**
  - Client bridge to Person 4's Learner Model (`AttemptRecordRequest` dispatched on every quiz answer).
  - Client bridge to Person 1's Agent Brain (`ChatMessageRequest` dispatched on code execution error).
  - Weak concept integration from Person 4 (`GET /learner/weak/{user_id}` feeding flashcards and quiz generator).
- **Blocked:**
  - None! All modules are operational and ready for teammate consumption.

---

## Person 4: Learner model + dashboard + demo owner (/backend/learner, /frontend/dashboard, /docs)
- **Status:** Complete & Tested (Milestones 1 - 4 Delivered)
- **What is REAL:**
  - **SQLite Database (`backend/learner/learner.db`):** 5 relational tables (`users`, `concepts`, `attempts`, `mastery`, `misconceptions`) with foreign key constraints, indexes, and full ACID durability.
  - **Adaptive EWMA Mastery Model with Temporal Decay (`backend/learner/model.py`):** Exponentially Weighted Moving Average formula with attempt-frequency weighting and Ebbinghaus forgetting decay ($\lambda = 0.03$/day).
  - **Misconception Diagnosis & Tracking:** Aggregates and logs specific diagnostic misconception tags (`confuses_direction_when_target_greater`, `confuses_low_with_high_shift`, `fails_to_exclude_checked_midpoint`, `infinite_loop_on_two_elements`) with targeted pedagogical remediation strings.
  - **Full Contract Endpoints (`backend/learner/main.py`):** `POST /learner/attempt`, `GET /learner/mastery/{user_id}`, `GET /learner/weak/{user_id}`, `GET /learner/recommend/{user_id}`, `GET /learner/history/{user_id}`, `GET /learner/summary/{user_id}`, and `POST /learner/seed`.
  - **Realistic Seed Data (`backend/learner/seed.py`):** Populates `demo_student` ("Alex Chen") benchmark state: bounds update weak score (0.45) with diagnosed misconceptions, complexity (0.80), intuition (0.90), edge cases (0.55), plus 11 realistic chronological attempts.
  - **Interactive Visual Dashboard (`frontend/dashboard/index.html`):** Standalone zero-dependency HTML5/Tailwind/Chart.js dashboard with live EWMA bar charts, weak area alerts, next-step recommendation banner, attempt history timeline, and real-time interactive attempt simulator.
  - **React/Next.js Components:** Published `frontend/dashboard/Dashboard.tsx` and `page.tsx` for seamless integration into Next.js.
  - **Comprehensive Docs & Pitch Materials:** Published `docs/ARCHITECTURE.md` (Mermaid flowcharts, sequence diagrams, ER schema), `docs/DEMO_SCRIPT.md` (3-minute hero moment script), `docs/PITCH_DECK.md` (5-slide judge pitch outline), and `docs/DEPLOYMENT.md`.
  - **Automated Test Suite (`backend/learner/test_learner.py`):** 100% pass on SQLite CRUD, EWMA calculations, Ebbinghaus decay, misconception links, and contract schemas.
- **What is MOCKED:**
  - **None in Learner Service:** Real SQLite database and live calculations are fully functional. Fallback memory caches remain available if operating offline.
- **Teammate Blockers:**
  - **None!** Backend learner service and dashboard are complete and tested. Teammates (Persons 1, 2, 3) have fully documented and operational endpoints and schemas.
