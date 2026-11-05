# AI-Powered Interactive Virtual Teacher

Agentic AI virtual educator delivering interactive whiteboard teaching, live coding execution, formative understanding checkpoints, adaptive mastery tracking, and personalized assessments.

## Quickstart (Zero-Dependency Mock Mode)

Teammates can run the full backend in **MOCK_MODE** with zero API keys required:

### Single Command Start:
- **macOS / Linux / Git Bash:**
  ```bash
  ./run.sh
  ```
  or with Make:
  ```bash
  make dev
  ```
- **Windows (Command Prompt):**
  ```cmd
  run.bat
  ```
- **Direct Uvicorn:**
  ```bash
  MOCK_MODE=true python -m uvicorn backend.agent.main:app --host 0.0.0.0 --port 8000 --reload
  ```

Once started:
- **API Documentation (Swagger UI):** `http://localhost:8000/docs`
- **Health Check:** `http://localhost:8000/health`
- **Canned Binary Search Lesson:** `http://localhost:8000/mock/lesson`

---

## API Contracts (`/contracts`)

All shared data models and API shapes live in `/contracts` (enforced by project rules):
- **`contracts/board_commands.json`**: JSON Schema for whiteboard draw elements (`text`, `box`, `arrow`, `equation`, `mermaid`, `clear`) and teaching steps.
- **`contracts/openapi.json`**: Complete OpenAPI 3.1 specification for all endpoints:
  - **Teacher Brain (`/backend/agent`):**
    - `POST /lesson/step` & `GET /lesson/step/stream` (SSE streaming)
    - `GET /mock/lesson` (canned 5-step Binary Search lesson)
    - `POST /agent/chat` (student chat & feedback)
    - `POST /tools/execute` (direct agent tool loop execution)
  - **Learner Model (`/backend/learner` - Person 4):**
    - `POST /learner/attempt`
    - `GET /learner/mastery/{user_id}`
    - `GET /learner/weak/{user_id}`
    - `GET /learner/recommend/{user_id}`
  - **Assess Engine (`/backend/assess` - Person 3):**
    - `POST /assess/quiz`
    - `POST /assess/flashcards`
    - `POST /assess/submit`

---

## Running Unit Tests

Run the test suite:
```bash
python backend/agent/test_agent.py
```
To run against real LLM providers (with `.env` keys):
```bash
REAL_LLM=1 python backend/agent/test_agent.py
```
