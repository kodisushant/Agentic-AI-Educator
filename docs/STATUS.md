# Team Status Board

## Person 1: Tech lead + Agent brain (/backend/agent, /contracts)
- **Status:** Complete (Milestones 1 - 4 Delivered & Tested)
- **What is REAL:**
  - **Live Multi-Provider LLM Router:** Google Gemini (`gemini-3.1-flash-lite`, ~1.5s latency) and Groq (`qwen/qwen3.8-27b`, ~730ms latency) working with real API keys, strict Pydantic JSON schema validation, automatic fallback on failure/rate limits (HTTP 429), per-request timeouts (10s), total-step latency caps (25s), and SHA256 disk caching.
  - **Dynamic Lesson Generation:** The teacher agent prompts the LLM with the student's mastery profile and weak concepts to dynamically generate structured `LessonStep` payloads (narration, whiteboard commands, Python code chunks, checkpoint questions, visible reasoning traces, and provider metadata).
  - **Misconception Diagnosis & Adaptive Remediation:** Wrong checkpoint answers are automatically evaluated against misconception taxonomies (e.g. `confuses_direction_when_target_greater`, `fails_to_exclude_checked_midpoint`). The agent returns targeted visual remediations, sets `detected_misconception` on the response for the UI, and updates mastery via `update_mastery`.
  - **Complete API Contracts:** Published in `/contracts/openapi.json` and `/contracts/board_commands.json` for all 4 team roles.
  - **Thin Client & Single-Command Startup:** `backend/agent/client.py` provides thin clients for `LearnerClient` and `AssessClient`. Start commands `make dev`, `./run.sh`, or `run.bat` spin up the server in `MOCK_MODE`.
  - **Test Suite:** Synchronous mock test suite (`python backend/agent/test_agent.py`) + live provider test suite (`REAL_LLM=1 python backend/agent/test_agent.py`).
- **What is MOCKED:**
  - **Learner Store:** In-memory fallback mock database (`MOCK_MASTERY_DB`) used when Person 4's SQLite database service is offline or unreachable.
  - **Assessment Generator:** Canned questions and flashcard decks used when Person 3's assessment service is offline or unreachable.
  - **Fallback Lesson:** The 5-step interactive Binary Search lesson acts as a safe, crash-proof fallback if live LLM APIs exhaust all retries.
- **Teammate Blockers:**
  - **None!** All contracts, schemas, mock endpoints, and client bridges are in place and tested. Teammates (Persons 2, 3, 4) can develop and run their apps without obstacles.

---

## Person 2: Classroom frontend (/frontend/classroom)
- **Status:** Unblocked & Ready to build
- **Completed:** None
- **In Progress:** Whiteboard canvas (Excalidraw/tldraw), step playback, chat UI against `/contracts/board_commands.json` or `/mock/lesson`
- **Blocked:** None

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
