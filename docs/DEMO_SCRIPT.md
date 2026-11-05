# 3-Minute Hackathon Demo Script: AI Virtual Teacher

**Topic:** Binary Search with Adaptive Misconception Remediation  
**Target Duration:** 3 minutes (180 seconds)  
**Roles:** Presenter / Driver  
**Key Persona:** Alex Chen (`demo_student`)

---

## Script Breakdown

### Act 1: The Hook & The Problem (0:00 - 0:35)
- **Visual:** Teacher Classroom UI on screen (`/frontend/classroom`). Blank digital canvas ready.
- **Speaker:**
  > "Every student has experienced this: you watch a 20-minute video lecture on algorithms, you think you understand it, but the moment you try to write the code yourself, you freeze. Static videos can't see your confusion, and standard AI chat bots just dump walls of markdown text.
  > Today, we're showing the **AI Virtual Teacher** — an agentic educator that combines a digital whiteboard, live browser Python execution, and an adaptive cognitive model that diagnoses *why* you made a mistake and fixes it in real time."

---

### Act 2: Interactive Teaching & Live Coding (0:35 - 1:20)
- **Visual:** Presenter clicks **"Start Lesson"**.
  - Whiteboard animates: array `[2, 5, 8, 12, 16, 23, 38, 56, 72, 91]`, `low=0`, `high=9`, target `23`.
  - LaTeX equation KaTeX renders: $\text{mid} = \lfloor \frac{0 + 9}{2} \rfloor = 4 \implies \text{arr}[4] = 16$.
  - Audio narration speaks step-by-step explanation.
  - Teacher switches to Live Code Mode: Python snippet types into Monaco editor and Pyodide executes in the browser without server latency.
- **Speaker:**
  > "Notice how the teacher doesn't just chat. It emits structured whiteboard commands — rendering geometric boxes, LaTeX equations, and Mermaid state machines step by step.
  > In the coding tab, Monaco and browser Pyodide execute real Python with zero cloud compute cost."

---

### Act 3: The Hero Moment — Diagnosing the Misconception (1:20 - 2:10)
- **Visual:** Classroom UI advances to **Checkpoint Question**:
  - *"Target is 23, but arr[mid] is 16. Since target > arr[mid], how should our pointers update?"*
  - Option A: `high = mid - 1`
  - Option B: `low = mid + 1` (Correct)
  - Option C: `low = mid`
  - Option D: `high = mid`
- **Action:** Presenter intentionally clicks **Option A** (`high = mid - 1`).
- **Visual:**
  - Screen flashes gentle diagnostic alert.
  - **Visible Agent Thought Trace** displays:  
    `"Diagnosed misconception: student confuses search direction when target is greater than midpoint. Emitting targeted visual arrow to right half of board."`
  - Whiteboard immediately draws a highlight box around indices `5` to `9` with an arrow: *"Target (23) > 16. Target lies to the RIGHT!"*
- **Speaker:**
  > "Here is where the magic happens. I intentionally chose Option A — a classic novice mistake.
  > A traditional quiz platform simply says: 'Wrong. Try again.'
  > But our agentic brain matches the error against our cognitive misconception taxonomy, identifies that I reversed the search direction, visually highlights the right partition on the whiteboard, and explains *why*."

---

### Act 4: Real-Time Learner Model & Dashboard (2:10 - 2:45)
- **Visual:** Presenter switches tab to **Learner Dashboard** (`/frontend/dashboard`).
- **Visual highlights:**
  - `binary_search_bounds_update` displays in Amber/Red with mastery score **45%**.
  - Red diagnostic badge: `⚠️ confuses_direction_when_target_greater`.
  - Next Recommended Step banner: *"Recommended: Targeted Quiz on Boundary Updates"*.
  - Presenter clicks **"Simulate Correct Answer (+Score)"** button.
  - EWMA chart smoothly animates upward to **56%**; history timeline logs the attempt live.
- **Speaker:**
  > "Behind the scenes, our SQLite Learner Model calculates mastery using an Exponentially Weighted Moving Average with Ebbinghaus forgetting decay.
  > The misconception is permanently tagged in Alex Chen's student knowledge graph.
  > When Alex practices tomorrow, the system automatically personalizes the quiz to reinforce this exact weak area."

---

### Act 5: Architecture, Zero-Cost Stack & Conclusion (2:45 - 3:00)
- **Visual:** Quick switch to Architecture slide or `/health` endpoint.
- **Speaker:**
  > "Best of all: this entire application runs on **free-tier LLMs** (Gemini Flash & Groq Qwen) with multi-provider fallback routing, and client-side Pyodide. Total server compute cost: $0.
  > Personalized 1-on-1 education is no longer a luxury. Thank you!"

---

## Backup Demo Checklist
- [x] Pre-seeded SQLite database with Alex Chen's profile (`py -m backend.learner.seed`)
- [x] Mock fallback mode verified in `backend/agent/test_agent.py`
- [x] Dashboard accessible standalone in `frontend/dashboard/index.html`
- [x] Screen recording of full flow saved locally as fallback in case of projector/network issues.
