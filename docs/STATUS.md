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
- **Status:** Unblocked & Ready to build
- **Completed:** None
- **In Progress:** Monaco + Pyodide runner, checkpoint quiz UI against `/assess/*` in `/contracts/openapi.json`
- **Blocked:** None

---

## Person 4: Learner model + dashboard + demo owner (/backend/learner, /frontend/dashboard, /docs)
- **Status:** Unblocked & Ready to build
- **Completed:** Initial project docs and requirements setup
- **In Progress:** SQLite learner database, mastery calculation against `/learner/*` in `/contracts/openapi.json`
- **Blocked:** None
