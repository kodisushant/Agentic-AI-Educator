# 5-Slide Pitch Deck Outline: AI Virtual Teacher

## Slide 1: The Problem — The Online Learning Crisis
- **Headline:** 85% of students drop out of online courses because video is passive and chatbots lack pedagogical structure.
- **Pain Points:**
  - **Static Video Lectures:** One-size-fits-all, cannot detect when a student is lost, zero interactive feedback.
  - **Generic LLM Chatbots:** Dump long walls of unstructured text; cannot draw diagrams, cannot verify live code execution, and have no memory of student misconceptions.
  - **Human 1-on-1 Tutoring:** The gold standard (Bloom's 2 Sigma Problem), but costs \$50-\$100/hour, making it inaccessible to the majority of learners.

---

## Slide 2: The Solution — AI-Powered Interactive Virtual Teacher
- **Headline:** The first multimodal agentic educator that combines a digital whiteboard, live browser coding, and cognitive knowledge modeling.
- **Core Pillars:**
  1. **Visual Whiteboard Canvas:** LLM emits structured geometric commands, KaTeX math formulas, and Mermaid diagrams animated step by step.
  2. **Zero-Latency In-Browser Code Execution:** Monaco editor powered by client-side Pyodide — runs Python with no expensive cloud sandboxes.
  3. **Cognitive Student Modeling:** SQLite-backed EWMA mastery engine tracking concepts and diagnosing misconceptions.

---

## Slide 3: The Secret Sauce — Agentic Misconception Diagnosis
- **Headline:** We don't just grade right vs. wrong. We diagnose *why* a student failed.
- **How it Works:**
  - When a student answers a checkpoint question incorrectly (e.g. Setting `high = mid - 1` when `target > arr[mid]`), the agent evaluates the mistake against a misconception taxonomy.
  - **Immediate Visual Remediation:** The teacher agent modifies the digital whiteboard in real time to circle the specific error and draw the correct intuition.
  - **Persistent Knowledge Graph:** Misconceptions are tagged and fed into future lesson planning, quizzes, and spaced flashcards.

---

## Slide 4: Architecture & Zero-Cost Economics
- **Headline:** Enterprise-grade reliability built entirely on $0/month compute and free LLM tiers.
- **Architecture Highlights:**
  - **Resilient LLM Router:** Automatic fallback order (Google Gemini $\to$ Groq $\to$ Cerebras $\to$ OpenRouter) with strict Pydantic JSON schema validation and disk caching.
  - **Client-Side Compute:** Code runs directly in the learner's browser via WebAssembly (Pyodide), eliminating expensive backend container infrastructure.
  - **Edge-Ready Database:** Lightweight SQLite with ACID durability, portable for edge nodes and local school deployments.

---

## Slide 5: Market Opportunity & Future Roadmap
- **Market Size:** \$340B global EdTech market; 1.5B students worldwide.
- **Roadmap:**
  - **Phase 1 (Hackathon):** End-to-end slice on Computer Science fundamentals (Binary Search, Recursion).
  - **Phase 2:** Multi-subject expansion (Linear Algebra, Calculus, Physics, Chemistry) with formula and graph plotting.
  - **Phase 3:** Full voice conversational loop using Web Speech API & Whisper for natural audio tutoring.
- **Vision:** democratizing Bloom's 2 Sigma 1-on-1 tutoring advantage for every child with an internet connection.
