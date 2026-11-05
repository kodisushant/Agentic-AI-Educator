# Team Status Board

## Person 1: Tech lead + Agent brain (/backend/agent, /contracts)
- **Status:** Done (Initial Minimal Working Slice)
- **Completed:**
  - Published `/contracts/board_commands.json` (JSON Schema for polymorphic whiteboard commands: text, box, arrow, equation, mermaid, clear).
  - Published `/contracts/openapi.json` (OpenAPI spec for lesson streaming, mock endpoints, chat, tool execution).
  - Built `llm_router.py` with multi-provider fallback (Gemini, Groq, Cerebras, OpenRouter), disk cache, and mock fallback.
  - Built `tools.py` for teacher loop (`draw_on_board`, `run_code`, `ask_check_question`, `generate_quiz`, `update_mastery`, `recommend_next`).
  - Built `teacher.py` featuring a 5-step interactive Binary Search lesson slice with live coding, KaTeX math, Mermaid diagrams, and adaptive feedback.
  - Built FastAPI server in `main.py` with CORS, `/lesson/step`, `/lesson/step/stream`, `/mock/lesson`, `/agent/chat`, and `/tools/execute`.
- **In Progress:** Ready for frontend and assessment integration.
- **Blocked:** None.

---

## Person 2: Classroom frontend (/frontend/classroom)
- **Status:** Pending start
- **Completed:** None
- **In Progress:** Whiteboard canvas, step playback, chat UI against `/contracts/board_commands.json` or `/mock/lesson`
- **Blocked:** None

---

## Person 3: Live coding + assessment (/frontend/code, /frontend/quiz, /backend/assess)
- **Status:** Pending start
- **Completed:** None
- **In Progress:** Monaco + Pyodide runner, checkpoint quiz UI
- **Blocked:** None

---

## Person 4: Learner model + dashboard + demo owner (/backend/learner, /frontend/dashboard, /docs)
- **Status:** Pending start
- **Completed:** Initial project docs and requirements setup
- **In Progress:** SQLite learner database, mastery calculation
- **Blocked:** None
