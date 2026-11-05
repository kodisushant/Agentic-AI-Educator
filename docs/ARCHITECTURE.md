# AI Virtual Teacher: System Architecture & Data Flow

## 1. Executive Summary

The AI-Powered Interactive Virtual Teacher is an agentic education platform designed to replicate a 1-on-1 human tutoring experience. Instead of static text or passive video, the system orchestrates an active multimodal loop:
1. **Interactive Digital Whiteboard**: Step-by-step visual narration using structured geometric commands, LaTeX KaTeX formulas, and Mermaid charts.
2. **In-Browser Live Coding**: Execution of real Python code via Pyodide without requiring server-side compute sandboxes.
3. **Formative Understanding Checkpoints**: Frequent multiple-choice checkpoints that evaluate student thinking.
4. **Cognitive Misconception Diagnosis**: Rather than simple right/wrong grading, errors are matched against known misconception taxonomies.
5. **Adaptive Learner Model**: An Exponentially Weighted Moving Average (EWMA) knowledge graph with temporal forgetting decay that tracks concept-level mastery in real time.

---

## 2. End-to-End System Architecture

```mermaid
flowchart TB
    subgraph Frontend["Frontend Ecosystem (Next.js / Browser)"]
        UI_Classroom["Classroom UI (/frontend/classroom)\n• Whiteboard Canvas (Excalidraw/tldraw)\n• KaTeX LaTeX & Mermaid Renderer\n• Narration Captions & TTS Voice\n• Step Controls (Play/Pause/Next)"]
        UI_Code["Live Coding (/frontend/code)\n• Monaco Editor\n• Browser Pyodide Python Runner\n• Stdout & Error Feed"]
        UI_Quiz["Assessments (/frontend/quiz)\n• Interactive MCQ Checkpoints\n• Spaced Flashcard Deck"]
        UI_Dash["Learner Dashboard (/frontend/dashboard)\n• EWMA Mastery Heatmap & Charts\n• Diagnosed Misconception Alerts\n• Recommended Next Practice Banner\n• Attempt History Timeline"]
    end

    subgraph BackendAgent["Teacher Agent Brain (/backend/agent)"]
        LLM_Router["LLM Router (llm_router.py)\n• Multi-Provider Fallback\n• Gemini -> Groq -> Cerebras -> OpenRouter\n• Strict Pydantic Schema Validation\n• Disk Cache & Latency Timeouts"]
        Teacher_Loop["Teacher Agent Loop (teacher.py)\n• Dynamic Step Planning\n• Tool Execution Engine\n• Misconception Diagnosis"]
    end

    subgraph BackendLearner["Learner Model Service (/backend/learner)"]
        Learner_API["FastAPI Learner Service (main.py)\n• /learner/attempt\n• /learner/mastery\n• /learner/weak\n• /learner/recommend"]
        Mastery_Engine["Cognitive Engine (model.py)\n• EWMA Calculation Engine\n• Ebbinghaus Temporal Forgetting Decay\n• Pedagogical Recommendation Logic"]
        SQLite_DB[("SQLite Store (learner.db)\n• users\n• concepts\n• attempts\n• mastery\n• misconceptions")]
    end

    subgraph BackendAssess["Assessment Service (/backend/assess)"]
        Assess_API["Assessment Engine\n• /assess/quiz\n• /assess/flashcards\n• /assess/submit"]
    end

    UI_Classroom -->|POST /lesson/step| BackendAgent
    UI_Classroom -->|POST /lesson/check-answer| BackendAgent
    BackendAgent -->|POST /learner/attempt| Learner_API
    BackendAgent -->|GET /learner/weak| Learner_API
    UI_Quiz -->|POST /assess/submit| Assess_API
    Assess_API -->|POST /learner/attempt| Learner_API
    UI_Dash -->|GET /learner/mastery, /weak| Learner_API
    Learner_API --> Mastery_Engine
    Mastery_Engine --> SQLite_DB
```

---

## 3. Sequence Flow: The Adaptive Remediation Loop

```mermaid
sequenceDiagram
    autonumber
    actor Student
    participant Classroom as Classroom UI (/frontend/classroom)
    participant Teacher as Teacher Agent (/backend/agent)
    participant Learner as Learner Service (/backend/learner)
    participant DB as SQLite DB (learner.db)
    participant Dashboard as Dashboard (/frontend/dashboard)

    Student->>Classroom: Submits answer to checkpoint question
    Classroom->>Teacher: POST /lesson/check-answer {question_id, selected_index}
    Teacher->>Teacher: Evaluate answer & diagnose misconception
    Teacher->>Learner: POST /learner/attempt {concept_tag, is_correct, misconceptions}
    Learner->>DB: Query previous mastery score & last attempt timestamp
    Learner->>Learner: Calculate Ebbinghaus temporal decay
    Learner->>Learner: Compute new mastery score via EWMA
    Learner->>DB: Update mastery score, log attempt, upsert misconception
    Learner-->>Teacher: AttemptRecordResponse {new_mastery_score}
    Teacher->>Teacher: Synthesize corrective whiteboard commands
    Teacher-->>Classroom: CheckAnswerResponse {is_correct, detected_misconception, remediation, suggested_board_commands}
    Classroom->>Student: Displays visual correction & audio explanation
    Dashboard->>Learner: GET /learner/summary/demo_student
    Learner-->>Dashboard: Returns real-time updated mastery, weak concepts & recommendation
    Dashboard->>Student: Displays updated mastery charts & next recommended action
```

---

## 4. Learner Database Schema (SQLite)

```mermaid
erDiagram
    USERS ||--o{ ATTEMPTS : makes
    USERS ||--o{ MASTERY : has
    USERS ||--o{ MISCONCEPTIONS : exhibits
    CONCEPTS ||--o{ ATTEMPTS : evaluated_in
    CONCEPTS ||--o{ MASTERY : measured_by
    CONCEPTS ||--o{ MISCONCEPTIONS : associated_with

    USERS {
        text id PK "e.g. demo_student"
        text name "Alex Chen"
        text email "alex.chen@student.edu"
        text created_at "ISO-8601"
        text last_active "ISO-8601"
    }

    CONCEPTS {
        text tag PK "e.g. binary_search_bounds_update"
        text name "Binary Search Bounds Update"
        text topic "Binary Search"
        text description "Adjusting low and high pointers"
        text difficulty "beginner | intermediate | advanced"
    }

    ATTEMPTS {
        integer id PK "AUTOINCREMENT"
        text user_id FK "References USERS(id)"
        text concept_tag FK "References CONCEPTS(tag)"
        text question_id "Optional question reference"
        integer is_correct "1 for true, 0 for false"
        real time_spent_seconds "Response latency in seconds"
        text misconceptions_json "Array of diagnosed misconception tags"
        text metadata_json "Context metadata"
        text created_at "ISO-8601 timestamp"
    }

    MASTERY {
        text user_id PK, FK "References USERS(id)"
        text concept_tag PK, FK "References CONCEPTS(tag)"
        real score "0.05 to 1.00 EWMA mastery score"
        integer attempt_count "Cumulative attempts on concept"
        text last_attempt_at "ISO-8601 timestamp"
        text updated_at "ISO-8601 timestamp"
    }

    MISCONCEPTIONS {
        integer id PK "AUTOINCREMENT"
        text user_id FK "References USERS(id)"
        text concept_tag FK "References CONCEPTS(tag)"
        text misconception_tag "e.g. confuses_direction_when_target_greater"
        integer frequency "Times observed"
        text last_observed_at "ISO-8601 timestamp"
    }
```

---

## 5. Mathematical Models

### 5.1 Exponentially Weighted Moving Average (EWMA)
To compute smooth, adaptive mastery updates that respond quickly to newly learned concepts without fluctuating erratically:

$$M_{t} = \alpha_{\text{eff}} \cdot R_{t} + (1 - \alpha_{\text{eff}}) \cdot M_{t-1}$$

Where:
- $R_{t} \in [0.0, 1.0]$ is the performance on the current attempt (1.0 for correct, 0.0 for incorrect, with time-efficiency micro-adjustments).
- $\alpha_{\text{eff}} = \min\left(0.50, \alpha_{\text{base}} \cdot \frac{1.5}{\sqrt{N_{\text{attempts}}}}\right)$, ensuring high responsiveness during initial attempts and stability as confidence grows.
- $M_{t}$ is bounded strictly to $[0.05, 1.00]$.

### 5.2 Ebbinghaus Forgetting Decay
Knowledge decays when a student does not practice a concept over extended periods:

$$M_{\text{decayed}} = M_{\text{last}} \cdot e^{-\lambda \cdot \Delta t}$$

Where:
- $\Delta t$ is the elapsed time in days since $t_{\text{last\_attempt}}$.
- $\lambda = 0.03$ (approx. 3% decay per day of inactivity, retaining foundational retention).

---

## 6. Diagnosed Misconception Taxonomy (Binary Search Benchmark)

| Misconception Tag | Student Mistake | Pedagogical Remediation |
|---|---|---|
| `confuses_direction_when_target_greater` | Sets `high = mid - 1` when `target > arr[mid]` | Pointer shift logic: when target is larger, the target must lie in the right sub-array (`low = mid + 1`). |
| `confuses_low_with_high_shift` | Inverts `low` and `high` pointer updates | Clear visual distinction between left bound (`low`) and right bound (`high`). |
| `fails_to_exclude_checked_midpoint` | Sets `low = mid` or `high = mid` | Exclude checked midpoint: always shift by $+1$ or $-1$ to prevent infinite loops. |
| `infinite_loop_on_two_elements` | Does not terminate on two adjacent items | Integer floor division ensures progress toward single-element termination. |
