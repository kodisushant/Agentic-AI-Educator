/**
 * QuizPanel - Formative assessment and flashcards interactive panel.
 * Implements window.QuizPanel per the Hackathon Shared Spec:
 *   - mount(el, {apiBase, getUserId})
 *   - fetch quiz from /assess/quiz
 *   - show result IMMEDIATELY on click (grade locally, then confirm via /assess/submit in background)
 *   - 3s timeout with a retry state
 *   - final score and weak concepts
 *   - flashcards flip view
 */

(function () {
  'use strict';

  // Fallback question bank if backend is slow/offline
  const FALLBACK_QUIZ = {
    quiz_id: 'quiz_bs_fallback',
    topic: 'Binary Search',
    questions: [
      {
        question_id: 'q_bs_1',
        concept_tag: 'binary_search_precondition',
        question: 'What is the mandatory prerequisite before applying Binary Search on a collection?',
        options: [
          'The elements must be sorted',
          'The elements must all be unique',
          'The list length must be an even number',
          'The array must fit entirely in CPU L1 cache'
        ],
        correct_index: 0,
        explanation: 'Binary search relies on monotonic ordering to eliminate half the remaining search space on each comparison.'
      },
      {
        question_id: 'q_bs_2',
        concept_tag: 'binary_search_bounds_update',
        question: 'When target > arr[mid] in an ascending array, how should the search boundaries be updated?',
        options: [
          'high = mid - 1',
          'low = mid + 1',
          'low = mid',
          'high = mid'
        ],
        correct_index: 1,
        explanation: 'Since target is strictly greater than arr[mid], the target must reside in the right partition: low = mid + 1.'
      },
      {
        question_id: 'q_bs_3',
        concept_tag: 'binary_search_complexity',
        question: 'What is the worst-case time complexity of Binary Search on an array of size n?',
        options: [
          'O(1)',
          'O(log n)',
          'O(n)',
          'O(n log n)'
        ],
        correct_index: 1,
        explanation: 'The search space is divided by 2 at each iteration: n -> n/2 -> n/4 -> ... -> 1, which requires O(log n) steps.'
      }
    ]
  };

  const FALLBACK_FLASHCARDS = {
    topic: 'Binary Search',
    cards: [
      {
        card_id: 'fc_1',
        concept_tag: 'binary_search_precondition',
        front: 'What condition MUST be met to use Binary Search?',
        back: 'The input collection must be sorted in monotonic order (ascending or descending).',
        hint: 'Think about why we can safely discard halves of the search space.'
      },
      {
        card_id: 'fc_2',
        concept_tag: 'binary_search_bounds_update',
        front: 'Target is GREATER than arr[mid]. Where do you search next?',
        back: 'Search the right half by setting: low = mid + 1',
        hint: 'Exclude mid because we already checked it and it did not match.'
      },
      {
        card_id: 'fc_3',
        concept_tag: 'binary_search_complexity',
        front: 'What is the time complexity of Binary Search?',
        back: 'O(log n) time complexity, and O(1) auxiliary space (iterative).',
        hint: 'Halving the space at each step.'
      },
      {
        card_id: 'fc_4',
        concept_tag: 'binary_search_termination',
        front: 'What is the standard loop termination condition?',
        back: 'while low <= high (terminates when low > high, meaning element was not found).',
        hint: 'Do we check when low == high?'
      }
    ]
  };

  class QuizPanelManager {
    constructor() {
      this.container = null;
      this.apiBase = 'http://localhost:8000';
      this.getUserId = () => 'demo_student';
      this.currentMode = 'quiz'; // 'quiz' | 'flashcards'
      
      // Quiz state
      this.quizData = null;
      this.userAnswers = {}; // { question_id: selected_index }
      this.isSubmitting = false;
      this.backendResult = null;

      // Flashcards state
      this.flashcardsData = null;
      this.currentCardIndex = 0;
      this.isCardFlipped = false;
    }

    mount(el, options = {}) {
      if (typeof el === 'string') {
        el = document.querySelector(el);
      }
      if (!el) {
        console.error('[QuizPanel] Mount element not found');
        return;
      }
      this.container = el;
      if (options.apiBase) this.apiBase = options.apiBase.replace(/\/+$/, '');
      if (typeof options.getUserId === 'function') this.getUserId = options.getUserId;

      this.renderUI();
      this.fetchQuiz();
    }

    renderUI() {
      this.container.innerHTML = `
        <div class="quiz-panel-root" style="display: flex; flex-direction: column; height: 100%; min-height: 480px; background: #0f172a; border-radius: 8px; overflow: hidden; font-family: ui-sans-serif, system-ui, sans-serif; color: #f8fafc; border: 1px solid #334155;">
          <!-- Top Navigation Header -->
          <div style="display: flex; align-items: center; justify-content: space-between; padding: 10px 14px; background: #1e293b; border-bottom: 1px solid #334155;">
            <div style="display: flex; align-items: center; gap: 4px; background: #0f172a; padding: 2px; border-radius: 6px; border: 1px solid #334155;">
              <button id="qp-tab-quiz" style="padding: 4px 12px; font-size: 11px; font-weight: 600; border: none; border-radius: 4px; cursor: pointer; background: #2563eb; color: #fff;">
                Quiz
              </button>
              <button id="qp-tab-flashcards" style="padding: 4px 12px; font-size: 11px; font-weight: 600; border: none; border-radius: 4px; cursor: pointer; background: transparent; color: #94a3b8;">
                Flashcards
              </button>
            </div>

            <div style="display: flex; align-items: center; gap: 8px;">
              <span id="qp-status-badge" style="font-size: 10px; color: #94a3b8; background: #334155; padding: 2px 6px; border-radius: 4px;">
                Topic: Binary Search
              </span>
              <button id="qp-reload-btn" title="Reload assessment" style="background: none; border: none; color: #94a3b8; cursor: pointer; font-size: 12px;">
                ↺
              </button>
            </div>
          </div>

          <!-- Main Content Area -->
          <div id="qp-body" style="flex: 1 1 auto; padding: 16px; overflow-y: auto;">
            <!-- Rendered dynamically -->
          </div>
        </div>
      `;

      // Tab switching
      const tabQuiz = this.container.querySelector('#qp-tab-quiz');
      const tabCards = this.container.querySelector('#qp-tab-flashcards');
      const reloadBtn = this.container.querySelector('#qp-reload-btn');

      tabQuiz.addEventListener('click', () => {
        if (this.currentMode !== 'quiz') {
          this.currentMode = 'quiz';
          tabQuiz.style.background = '#2563eb';
          tabQuiz.style.color = '#fff';
          tabCards.style.background = 'transparent';
          tabCards.style.color = '#94a3b8';
          if (this.quizData) this.renderQuiz();
          else this.fetchQuiz();
        }
      });

      tabCards.addEventListener('click', () => {
        if (this.currentMode !== 'flashcards') {
          this.currentMode = 'flashcards';
          tabCards.style.background = '#2563eb';
          tabCards.style.color = '#fff';
          tabQuiz.style.background = 'transparent';
          tabQuiz.style.color = '#94a3b8';
          if (this.flashcardsData) this.renderFlashcards();
          else this.fetchFlashcards();
        }
      });

      reloadBtn.addEventListener('click', () => {
        if (this.currentMode === 'quiz') this.fetchQuiz();
        else this.fetchFlashcards();
      });
    }

    /**
     * Fetch quiz with 3s timeout and retry state
     */
    async fetchQuiz() {
      const bodyEl = this.container.querySelector('#qp-body');
      bodyEl.innerHTML = `
        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; gap: 10px; color: #94a3b8; font-size: 13px;">
          <div class="qp-spinner" style="font-size: 20px;">⏳</div>
          <div>Loading adaptive quiz (3s timeout guard)...</div>
        </div>
      `;

      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 3000);

      try {
        const res = await fetch(`${this.apiBase}/assess/quiz`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            topic: 'Binary Search',
            num_questions: 3,
            difficulty: 'beginner',
            weak_concepts: []
          }),
          signal: controller.signal
        });
        clearTimeout(timeoutId);

        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        this.quizData = data;
        this.userAnswers = {};
        this.backendResult = null;
        this.renderQuiz();
      } catch (err) {
        clearTimeout(timeoutId);
        console.warn('[QuizPanel] Fetch quiz error or timeout:', err);
        // Show Retry button with graceful fallback option
        this.showRetryState('quiz', err.name === 'AbortError' ? 'Quiz request timed out after 3.0s' : 'Failed to connect to assessment service');
      }
    }

    showRetryState(target, message) {
      const bodyEl = this.container.querySelector('#qp-body');
      bodyEl.innerHTML = `
        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; gap: 12px; padding: 20px; text-align: center;">
          <div style="font-size: 28px;">⚠️</div>
          <div style="font-size: 13px; font-weight: 600; color: #f87171;">${this.escapeHtml(message)}</div>
          <div style="font-size: 12px; color: #94a3b8;">You can retry the request or load standard offline questions.</div>
          <div style="display: flex; gap: 8px; margin-top: 8px;">
            <button id="qp-retry-action" style="padding: 6px 14px; background: #2563eb; color: #fff; border: none; border-radius: 5px; font-size: 12px; font-weight: 600; cursor: pointer;">
              Retry ↺
            </button>
            <button id="qp-fallback-action" style="padding: 6px 14px; background: #334155; color: #cbd5e1; border: none; border-radius: 5px; font-size: 12px; cursor: pointer;">
              Use Demo Questions
            </button>
          </div>
        </div>
      `;

      bodyEl.querySelector('#qp-retry-action').addEventListener('click', () => {
        if (target === 'quiz') this.fetchQuiz();
        else this.fetchFlashcards();
      });

      bodyEl.querySelector('#qp-fallback-action').addEventListener('click', () => {
        if (target === 'quiz') {
          this.quizData = FALLBACK_QUIZ;
          this.userAnswers = {};
          this.renderQuiz();
        } else {
          this.flashcardsData = FALLBACK_FLASHCARDS;
          this.currentCardIndex = 0;
          this.isCardFlipped = false;
          this.renderFlashcards();
        }
      });
    }

    renderQuiz() {
      const bodyEl = this.container.querySelector('#qp-body');
      if (!this.quizData || !this.quizData.questions || this.quizData.questions.length === 0) {
        bodyEl.innerHTML = '<div style="color: #94a3b8; font-size: 13px;">No quiz questions available.</div>';
        return;
      }

      const questions = this.quizData.questions;
      let html = `<div style="display: flex; flex-direction: column; gap: 20px;">`;

      questions.forEach((q, qIndex) => {
        const answeredIndex = this.userAnswers[q.question_id];
        const isAnswered = answeredIndex !== undefined;

        html += `
          <div class="qp-question-card" data-qid="${q.question_id}" style="background: #1e293b; border-radius: 8px; padding: 14px; border: 1px solid #334155;">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
              <span style="font-size: 11px; font-weight: 600; text-transform: uppercase; color: #38bdf8;">Question ${qIndex + 1} of ${questions.length}</span>
              <span style="font-size: 10px; background: #0f172a; color: #94a3b8; padding: 2px 6px; border-radius: 4px;">${this.escapeHtml(q.concept_tag || 'concept')}</span>
            </div>

            <div style="font-size: 13px; font-weight: 500; color: #f8fafc; margin-bottom: 12px; line-height: 1.4;">
              ${this.escapeHtml(q.question)}
            </div>

            <div class="qp-options-list" style="display: flex; flex-direction: column; gap: 6px;">
        `;

        q.options.forEach((opt, optIndex) => {
          let btnStyle = 'background: #0f172a; border: 1px solid #334155; color: #e2e8f0;';
          let statusIcon = '';

          if (isAnswered) {
            const isCorrectOption = optIndex === q.correct_index;
            const isUserSelected = optIndex === answeredIndex;

            if (isCorrectOption) {
              btnStyle = 'background: #064e3b; border: 1px solid #059669; color: #a7f3d0; font-weight: 600;';
              statusIcon = ' ✓';
            } else if (isUserSelected && !isCorrectOption) {
              btnStyle = 'background: #450a0a; border: 1px solid #dc2626; color: #fca5a5;';
              statusIcon = ' ✗';
            } else {
              btnStyle = 'background: #0f172a; border: 1px solid #1e293b; color: #64748b; opacity: 0.6;';
            }
          }

          html += `
            <button 
              class="qp-option-btn" 
              data-qid="${q.question_id}" 
              data-opt-index="${optIndex}" 
              ${isAnswered ? 'disabled' : ''}
              style="display: flex; align-items: center; justify-content: space-between; text-align: left; padding: 8px 12px; border-radius: 6px; font-size: 12px; cursor: ${isAnswered ? 'default' : 'pointer'}; transition: all 0.1s; ${btnStyle}">
              <span>${this.escapeHtml(opt)}</span>
              <span>${statusIcon}</span>
            </button>
          `;
        });

        html += `</div>`;

        // Immediate explanation display if answered
        if (isAnswered) {
          const isCorrect = answeredIndex === q.correct_index;
          html += `
            <div style="margin-top: 10px; padding: 8px 12px; border-radius: 6px; background: ${isCorrect ? '#022c22' : '#2a0a0a'}; border: 1px solid ${isCorrect ? '#065f46' : '#7f1d1d'}; font-size: 11px; line-height: 1.4; color: ${isCorrect ? '#6ee7b7' : '#fca5a5'};">
              <strong>${isCorrect ? 'Correct!' : 'Incorrect.'}</strong> ${this.escapeHtml(q.explanation || '')}
            </div>
          `;
        }

        html += `</div>`;
      });

      // Check if all questions have been answered to show summary
      const totalAnswered = Object.keys(this.userAnswers).length;
      if (totalAnswered === questions.length) {
        html += this.renderQuizSummary(questions);
      }

      html += `</div>`;
      bodyEl.innerHTML = html;

      // Attach click events on option buttons
      bodyEl.querySelectorAll('.qp-option-btn:not([disabled])').forEach((btn) => {
        btn.addEventListener('click', (e) => {
          const qid = btn.getAttribute('data-qid');
          const optIndex = parseInt(btn.getAttribute('data-opt-index'), 10);
          this.handleOptionClick(qid, optIndex);
        });
      });

      // Summary review or retake buttons
      const retakeBtn = bodyEl.querySelector('#qp-summary-retake-btn');
      if (retakeBtn) {
        retakeBtn.addEventListener('click', () => {
          this.userAnswers = {};
          this.renderQuiz();
        });
      }

      const flashcardJumpBtn = bodyEl.querySelector('#qp-summary-cards-btn');
      if (flashcardJumpBtn) {
        flashcardJumpBtn.addEventListener('click', () => {
          this.container.querySelector('#qp-tab-flashcards').click();
        });
      }
    }

    /**
     * Shows result IMMEDIATELY on click!
     * Grades locally in 0ms, then submits in background to /assess/submit
     */
    handleOptionClick(questionId, selectedIndex) {
      if (this.userAnswers[questionId] !== undefined) return;
      this.userAnswers[questionId] = selectedIndex;

      // Re-render immediately to reflect green/red and explanation
      this.renderQuiz();

      // Background confirmation via /assess/submit
      this.confirmSubmitInBackground(questionId, selectedIndex);
    }

    async confirmSubmitInBackground(questionId, selectedIndex) {
      const userId = typeof this.getUserId === 'function' ? this.getUserId() : 'demo_student';
      const quizId = this.quizData ? this.quizData.quiz_id : 'quiz_bs_101';

      try {
        const res = await fetch(`${this.apiBase}/assess/submit`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            quiz_id: quizId,
            user_id: userId,
            answers: { [questionId]: selectedIndex }
          })
        });

        if (res.ok) {
          const result = await res.json();
          this.backendResult = result;
        }
      } catch (err) {
        console.warn('[QuizPanel] Background submit sync failed (local grade preserved):', err);
      }
    }

    renderQuizSummary(questions) {
      let correctCount = 0;
      const weakConcepts = [];

      questions.forEach((q) => {
        if (this.userAnswers[q.question_id] === q.correct_index) {
          correctCount++;
        } else {
          weakConcepts.push(q.concept_tag || 'Concept');
        }
      });

      const scorePercent = Math.round((correctCount / questions.length) * 100);
      const isPerfect = scorePercent === 100;

      return `
        <div style="background: #1e1b4b; border-radius: 8px; padding: 16px; border: 1px solid #4338ca; text-align: center; margin-top: 10px;">
          <div style="font-size: 11px; font-weight: 600; text-transform: uppercase; color: #a5b4fc; letter-spacing: 0.05em; margin-bottom: 4px;">
            Assessment Complete
          </div>
          <div style="font-size: 26px; font-weight: 700; color: ${isPerfect ? '#4ade80' : scorePercent >= 60 ? '#38bdf8' : '#f87171'}; margin-bottom: 6px;">
            ${correctCount} / ${questions.length} (${scorePercent}%)
          </div>

          ${
            weakConcepts.length > 0
              ? `
            <div style="margin: 12px 0; padding: 10px; background: #0f172a; border-radius: 6px; text-align: left; border: 1px solid #312e81;">
              <div style="font-size: 11px; font-weight: 600; color: #f87171; margin-bottom: 4px;">Weak Concepts Identified:</div>
              <ul style="margin: 0; padding-left: 18px; font-size: 11px; color: #cbd5e1;">
                ${weakConcepts.map(c => `<li><code>${this.escapeHtml(c)}</code></li>`).join('')}
              </ul>
            </div>
          `
              : `<div style="font-size: 12px; color: #86efac; margin-bottom: 12px;">🌟 Mastered! No weak areas detected on this topic.</div>`
          }

          <div style="display: flex; gap: 8px; justify-content: center;">
            <button id="qp-summary-retake-btn" style="padding: 6px 12px; background: #312e81; color: #c7d2fe; border: 1px solid #4338ca; border-radius: 5px; font-size: 11px; font-weight: 600; cursor: pointer;">
              Retake Quiz ↺
            </button>
            <button id="qp-summary-cards-btn" style="padding: 6px 12px; background: #4f46e5; color: #fff; border: none; border-radius: 5px; font-size: 11px; font-weight: 600; cursor: pointer;">
              Practice Flashcards 🎴
            </button>
          </div>
        </div>
      `;
    }

    /**
     * Fetch Flashcards with 3s timeout
     */
    async fetchFlashcards() {
      const bodyEl = this.container.querySelector('#qp-body');
      bodyEl.innerHTML = `
        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; gap: 10px; color: #94a3b8; font-size: 13px;">
          <div class="qp-spinner" style="font-size: 20px;">⏳</div>
          <div>Loading spaced-repetition flashcards (3s timeout guard)...</div>
        </div>
      `;

      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 3000);

      try {
        const res = await fetch(`${this.apiBase}/assess/flashcards`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            topic: 'Binary Search',
            count: 4,
            concept_tags: []
          }),
          signal: controller.signal
        });
        clearTimeout(timeoutId);

        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        this.flashcardsData = data;
        this.currentCardIndex = 0;
        this.isCardFlipped = false;
        this.renderFlashcards();
      } catch (err) {
        clearTimeout(timeoutId);
        console.warn('[QuizPanel] Fetch flashcards error or timeout:', err);
        this.showRetryState('flashcards', err.name === 'AbortError' ? 'Flashcards request timed out after 3.0s' : 'Failed to connect to flashcard service');
      }
    }

    renderFlashcards() {
      const bodyEl = this.container.querySelector('#qp-body');
      if (!this.flashcardsData || !this.flashcardsData.cards || this.flashcardsData.cards.length === 0) {
        bodyEl.innerHTML = '<div style="color: #94a3b8; font-size: 13px;">No flashcards available.</div>';
        return;
      }

      const cards = this.flashcardsData.cards;
      const card = cards[this.currentCardIndex];

      bodyEl.innerHTML = `
        <div style="display: flex; flex-direction: column; height: 100%; gap: 14px; align-items: center; justify-content: center;">
          <!-- Card Progress -->
          <div style="display: flex; align-items: center; justify-content: space-between; width: 100%; max-width: 360px; font-size: 11px; color: #94a3b8;">
            <span>Card ${this.currentCardIndex + 1} of ${cards.length}</span>
            <span style="background: #1e293b; padding: 2px 6px; border-radius: 4px; color: #38bdf8;">${this.escapeHtml(card.concept_tag || 'Concept')}</span>
          </div>

          <!-- Flip Card Container (Perspective 3D) -->
          <div id="qp-flashcard-box" style="perspective: 1000px; width: 100%; max-width: 360px; height: 210px; cursor: pointer;">
            <div id="qp-card-inner" style="position: relative; width: 100%; height: 100%; text-align: center; transition: transform 0.4s; transform-style: preserve-3d; transform: ${this.isCardFlipped ? 'rotateY(180deg)' : 'rotateY(0deg)'};">
              
              <!-- Front Side -->
              <div style="position: absolute; width: 100%; height: 100%; -webkit-backface-visibility: hidden; backface-visibility: hidden; background: #1e293b; border: 1px solid #334155; border-radius: 10px; padding: 18px; display: flex; flex-direction: column; justify-content: space-between; box-sizing: border-box;">
                <div style="font-size: 10px; text-transform: uppercase; font-weight: 600; color: #38bdf8; letter-spacing: 0.05em;">Question (Front)</div>
                <div style="font-size: 14px; font-weight: 500; color: #f8fafc; line-height: 1.4;">${this.escapeHtml(card.front)}</div>
                <div style="font-size: 11px; color: #64748b;">(Click card to reveal answer)</div>
              </div>

              <!-- Back Side -->
              <div style="position: absolute; width: 100%; height: 100%; -webkit-backface-visibility: hidden; backface-visibility: hidden; background: #064e3b; border: 1px solid #059669; border-radius: 10px; padding: 18px; display: flex; flex-direction: column; justify-content: space-between; box-sizing: border-box; transform: rotateY(180deg);">
                <div style="font-size: 10px; text-transform: uppercase; font-weight: 600; color: #86efac; letter-spacing: 0.05em;">Answer (Back)</div>
                <div style="font-size: 13px; font-weight: 500; color: #ecfdf5; line-height: 1.4;">${this.escapeHtml(card.back)}</div>
                <div style="font-size: 11px; color: #a7f3d0;">(Click card to flip back)</div>
              </div>

            </div>
          </div>

          <!-- Hint display if available -->
          ${
            card.hint
              ? `
            <div id="qp-hint-box" style="display: none; width: 100%; max-width: 360px; font-size: 11px; background: #1e1b4b; border: 1px solid #312e81; color: #c7d2fe; padding: 6px 12px; border-radius: 6px;">
              💡 <strong>Hint:</strong> ${this.escapeHtml(card.hint)}
            </div>
            <button id="qp-toggle-hint-btn" style="background: none; border: none; font-size: 11px; color: #818cf8; cursor: pointer; text-decoration: underline;">
              Show Hint
            </button>
          `
              : ''
          }

          <!-- Controls: Prev, Flip, Next -->
          <div style="display: flex; align-items: center; gap: 8px; margin-top: 4px;">
            <button id="qp-card-prev" ${this.currentCardIndex === 0 ? 'disabled' : ''} style="padding: 6px 14px; background: #334155; color: #f8fafc; border: none; border-radius: 5px; font-size: 12px; cursor: ${this.currentCardIndex === 0 ? 'not-allowed' : 'pointer'}; opacity: ${this.currentCardIndex === 0 ? 0.4 : 1};">
              ◀ Prev
            </button>
            <button id="qp-card-flip" style="padding: 6px 16px; background: #0284c7; color: #fff; border: none; border-radius: 5px; font-size: 12px; font-weight: 600; cursor: pointer;">
              Flip 🔄
            </button>
            <button id="qp-card-next" ${this.currentCardIndex === cards.length - 1 ? 'disabled' : ''} style="padding: 6px 14px; background: #334155; color: #f8fafc; border: none; border-radius: 5px; font-size: 12px; cursor: ${this.currentCardIndex === cards.length - 1 ? 'not-allowed' : 'pointer'}; opacity: ${this.currentCardIndex === cards.length - 1 ? 0.4 : 1};">
              Next ▶
            </button>
          </div>
        </div>
      `;

      // Flip click handlers
      const cardBox = bodyEl.querySelector('#qp-flashcard-box');
      const flipBtn = bodyEl.querySelector('#qp-card-flip');
      const toggleFlip = () => {
        this.isCardFlipped = !this.isCardFlipped;
        const inner = bodyEl.querySelector('#qp-card-inner');
        if (inner) {
          inner.style.transform = this.isCardFlipped ? 'rotateY(180deg)' : 'rotateY(0deg)';
        }
      };

      cardBox.addEventListener('click', toggleFlip);
      flipBtn.addEventListener('click', toggleFlip);

      // Prev / Next
      const prevBtn = bodyEl.querySelector('#qp-card-prev');
      const nextBtn = bodyEl.querySelector('#qp-card-next');

      if (prevBtn) {
        prevBtn.addEventListener('click', () => {
          if (this.currentCardIndex > 0) {
            this.currentCardIndex--;
            this.isCardFlipped = false;
            this.renderFlashcards();
          }
        });
      }

      if (nextBtn) {
        nextBtn.addEventListener('click', () => {
          if (this.currentCardIndex < cards.length - 1) {
            this.currentCardIndex++;
            this.isCardFlipped = false;
            this.renderFlashcards();
          }
        });
      }

      // Hint toggle
      const hintBtn = bodyEl.querySelector('#qp-toggle-hint-btn');
      if (hintBtn) {
        hintBtn.addEventListener('click', () => {
          const hintBox = bodyEl.querySelector('#qp-hint-box');
          if (hintBox) {
            const isVisible = hintBox.style.display !== 'none';
            hintBox.style.display = isVisible ? 'none' : 'block';
            hintBtn.textContent = isVisible ? 'Show Hint' : 'Hide Hint';
          }
        });
      }
    }

    escapeHtml(str) {
      return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
    }
  }

  // Expose on window.QuizPanel
  const instance = new QuizPanelManager();
  window.QuizPanel = {
    mount: (el, options) => instance.mount(el, options),
    fetchQuiz: () => instance.fetchQuiz(),
    fetchFlashcards: () => instance.fetchFlashcards()
  };
})();
