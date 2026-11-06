/**
 * ChatPanel - Teacher AI interactive chat panel.
 * Implements window.ChatPanel per the Hackathon Shared Spec:
 *   - mount(el, {apiBase, getContext})
 *   - POST {apiBase}/agent/chat with {message, topic, step_index, history, user_id} from getContext()
 *   - render markdown and code blocks, with "Run in editor" and "Copy" buttons
 *   - typing indicator, scroll to bottom, error/retry state, shows trace.source badge
 */

(function () {
  'use strict';

  class ChatPanelManager {
    constructor() {
      this.container = null;
      this.apiBase = 'http://localhost:8000';
      this.getContext = () => ({
        topic: 'Binary Search',
        step_index: 0,
        history: [],
        user_id: 'demo_student'
      });
      this.messages = [];
      this.isLoading = false;
      this.lastFailedMessage = null;
    }

    mount(el, options = {}) {
      if (typeof el === 'string') {
        el = document.querySelector(el);
      }
      if (!el) {
        console.error('[ChatPanel] Mount element not found');
        return;
      }
      this.container = el;
      if (options.apiBase) this.apiBase = options.apiBase.replace(/\/+$/, '');
      if (typeof options.getContext === 'function') this.getContext = options.getContext;

      this.renderUI();
      // Add initial teacher welcome message
      this.addMessage({
        sender: 'teacher',
        text: "Hello! I'm your AI Teacher. Ask me anything about the concept, or ask about errors you encounter while coding!",
        trace: { source: 'mock', provider: 'agent', latency_ms: 5 }
      });
    }

    renderUI() {
      this.container.innerHTML = `
        <div class="chat-panel-root" style="display: flex; flex-direction: column; height: 100%; min-height: 480px; background: #0f172a; border-radius: 8px; overflow: hidden; font-family: ui-sans-serif, system-ui, sans-serif; color: #f8fafc; border: 1px solid #334155;">
          <!-- Header -->
          <div style="display: flex; align-items: center; justify-content: space-between; padding: 10px 14px; background: #1e293b; border-bottom: 1px solid #334155;">
            <div style="display: flex; align-items: center; gap: 8px;">
              <span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: #10b981;"></span>
              <span style="font-weight: 600; font-size: 13px; color: #f8fafc;">Teacher Chat</span>
              <span style="font-size: 11px; color: #94a3b8; background: #0f172a; padding: 2px 6px; border-radius: 4px;">Socratic AI</span>
            </div>
            <button id="chat-clear-btn" style="background: none; border: none; color: #94a3b8; font-size: 11px; cursor: pointer; text-decoration: underline;">
              Clear History
            </button>
          </div>

          <!-- Messages Scroll View -->
          <div id="chat-messages-container" style="flex: 1 1 auto; padding: 14px; overflow-y: auto; display: flex; flex-direction: column; gap: 12px;"></div>

          <!-- Typing Indicator -->
          <div id="chat-typing-indicator" style="display: none; padding: 6px 14px; background: transparent;">
            <div style="display: inline-flex; align-items: center; gap: 6px; padding: 6px 12px; background: #1e293b; border-radius: 16px; font-size: 11px; color: #94a3b8; border: 1px solid #334155;">
              <span style="font-weight: 500;">Teacher is thinking</span>
              <span class="chat-dots" style="letter-spacing: 2px; font-size: 14px; color: #38bdf8;">•••</span>
            </div>
          </div>

          <!-- Error / Retry Banner -->
          <div id="chat-error-banner" style="display: none; align-items: center; justify-content: space-between; padding: 8px 14px; background: #450a0a; border-top: 1px solid #991b1b; font-size: 12px; color: #fca5a5;">
            <span id="chat-error-text">Failed to deliver message</span>
            <button id="chat-retry-btn" style="padding: 3px 8px; background: #dc2626; color: #fff; border: none; border-radius: 4px; font-size: 11px; cursor: pointer;">
              Retry ↺
            </button>
          </div>

          <!-- Input Footer -->
          <div style="padding: 10px 14px; background: #1e293b; border-top: 1px solid #334155; display: flex; gap: 8px;">
            <textarea id="chat-input" placeholder="Ask a question or request an explanation..." rows="1" style="flex: 1; padding: 8px 12px; background: #0f172a; color: #f8fafc; border: 1px solid #334155; border-radius: 6px; font-size: 12px; resize: none; outline: none; font-family: inherit;"></textarea>
            <button id="chat-send-btn" style="padding: 8px 14px; background: #2563eb; color: #ffffff; border: none; border-radius: 6px; font-size: 12px; font-weight: 600; cursor: pointer; transition: background 0.15s; white-space: nowrap;">
              Send
            </button>
          </div>
        </div>
      `;

      const input = this.container.querySelector('#chat-input');
      const sendBtn = this.container.querySelector('#chat-send-btn');
      const clearBtn = this.container.querySelector('#chat-clear-btn');
      const retryBtn = this.container.querySelector('#chat-retry-btn');

      const handleSend = () => {
        const text = input.value.trim();
        if (!text || this.isLoading) return;
        input.value = '';
        this.sendMessage(text);
      };

      sendBtn.addEventListener('click', handleSend);
      input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          handleSend();
        }
      });

      clearBtn.addEventListener('click', () => {
        this.messages = [];
        const msgContainer = this.container.querySelector('#chat-messages-container');
        msgContainer.innerHTML = '';
      });

      retryBtn.addEventListener('click', () => {
        if (this.lastFailedMessage) {
          const toRetry = this.lastFailedMessage;
          this.lastFailedMessage = null;
          this.container.querySelector('#chat-error-banner').style.display = 'none';
          this.sendMessage(toRetry);
        }
      });
    }

    sendQuestion(text) {
      if (!this.container) return;
      const input = this.container.querySelector('#chat-input');
      if (input) {
        input.value = text;
        input.focus();
      }
      this.sendMessage(text);
    }

    addMessage({ sender, text, trace, isError }) {
      this.messages.push({ sender, text, trace });
      const msgContainer = this.container.querySelector('#chat-messages-container');
      if (!msgContainer) return;

      const isUser = sender === 'user';
      const msgDiv = document.createElement('div');
      msgDiv.style.cssText = `display: flex; flex-direction: column; align-items: ${isUser ? 'flex-end' : 'flex-start'}; max-width: 100%;`;

      const bubble = document.createElement('div');
      bubble.style.cssText = `
        max-width: 88%;
        padding: 10px 14px;
        border-radius: ${isUser ? '12px 12px 2px 12px' : '12px 12px 12px 2px'};
        background: ${isUser ? '#1d4ed8' : '#1e293b'};
        color: #f8fafc;
        font-size: 13px;
        line-height: 1.5;
        border: 1px solid ${isUser ? '#2563eb' : '#334155'};
        word-break: break-word;
      `;

      bubble.innerHTML = this.formatMarkdown(text);
      this.attachCodeBlockEvents(bubble);

      msgDiv.appendChild(bubble);

      // Add trace badge for teacher messages
      if (!isUser && trace) {
        const traceEl = document.createElement('div');
        traceEl.style.cssText = 'display: inline-flex; align-items: center; gap: 6px; margin-top: 4px; font-size: 10px; color: #64748b;';
        
        const src = trace.source || trace.provider_used || 'mock';
        let badgeColor = '#64748b';
        let bg = '#1e293b';
        if (src === 'llm' || src === 'gemini' || src === 'groq') {
          badgeColor = '#34d399';
          bg = '#064e3b';
        } else if (src === 'cache') {
          badgeColor = '#60a5fa';
          bg = '#1e3a8a';
        } else if (src === 'mock') {
          badgeColor = '#f59e0b';
          bg = '#451a03';
        }

        const latency = trace.latency_ms ? ` • ${trace.latency_ms}ms` : '';
        const model = trace.model || trace.provider ? ` (${trace.provider || trace.model})` : '';

        traceEl.innerHTML = `
          <span style="background: ${bg}; color: ${badgeColor}; padding: 1px 6px; border-radius: 4px; font-weight: 600; text-transform: uppercase;">
            ${this.escapeHtml(src)}
          </span>
          <span>${this.escapeHtml(model)}${latency}</span>
        `;
        msgDiv.appendChild(traceEl);
      }

      msgContainer.appendChild(msgDiv);
      this.scrollToBottom();
    }

    formatMarkdown(text) {
      if (!text) return '';
      // Escape HTML first to prevent XSS
      let safe = this.escapeHtml(text);

      // Code blocks: ```python ... ``` or ``` ... ```
      safe = safe.replace(/```([a-zA-Z0-9_-]*)\n([\s\S]*?)```/g, (match, lang, code) => {
        const cleanLang = lang.trim() || 'python';
        const rawCode = this.unescapeHtml(code.trim());
        const encodedCode = encodeURIComponent(rawCode);

        return `
          <div class="chat-code-block" style="margin: 8px 0; background: #090d16; border-radius: 6px; border: 1px solid #334155; overflow: hidden;">
            <div style="display: flex; align-items: center; justify-content: space-between; padding: 4px 10px; background: #131b2e; border-bottom: 1px solid #1e293b; font-size: 11px;">
              <span style="color: #94a3b8; font-weight: 500;">${this.escapeHtml(cleanLang)}</span>
              <div style="display: flex; gap: 4px;">
                <button class="chat-code-copy-btn" data-code="${encodedCode}" style="background: #1e293b; color: #cbd5e1; border: 1px solid #334155; border-radius: 3px; padding: 2px 6px; font-size: 10px; cursor: pointer;">
                  Copy
                </button>
                <button class="chat-code-run-btn" data-code="${encodedCode}" style="background: #0284c7; color: #fff; border: none; border-radius: 3px; padding: 2px 8px; font-size: 10px; font-weight: 600; cursor: pointer;">
                  Run in editor ▶
                </button>
              </div>
            </div>
            <pre style="margin: 0; padding: 10px; font-family: ui-monospace, Menlo, Monaco, Consolas, monospace; font-size: 12px; color: #38bdf8; overflow-x: auto;"><code>${this.escapeHtml(rawCode)}</code></pre>
          </div>
        `;
      });

      // Inline code `...`
      safe = safe.replace(/`([^`]+)`/g, '<code style="background: #090d16; color: #38bdf8; padding: 2px 4px; border-radius: 3px; font-size: 12px; font-family: monospace;">$1</code>');

      // Bold **text**
      safe = safe.replace(/\*\*([^*]+)\*\*/g, '<strong style="color: #f1f5f9; font-weight: 600;">$1</strong>');

      // Italic *text*
      safe = safe.replace(/\*([^*]+)\*/g, '<em style="color: #cbd5e1;">$1</em>');

      // Line breaks
      safe = safe.replace(/\n/g, '<br/>');

      return safe;
    }

    attachCodeBlockEvents(element) {
      // Copy buttons
      const copyBtns = element.querySelectorAll('.chat-code-copy-btn');
      copyBtns.forEach((btn) => {
        btn.addEventListener('click', () => {
          const rawCode = decodeURIComponent(btn.getAttribute('data-code'));
          navigator.clipboard.writeText(rawCode).then(() => {
            const originalText = btn.textContent;
            btn.textContent = '✓ Copied!';
            setTimeout(() => { btn.textContent = originalText; }, 1500);
          }).catch(() => {
            btn.textContent = 'Failed';
          });
        });
      });

      // Run in editor buttons
      const runBtns = element.querySelectorAll('.chat-code-run-btn');
      runBtns.forEach((btn) => {
        btn.addEventListener('click', () => {
          const rawCode = decodeURIComponent(btn.getAttribute('data-code'));
          if (window.CodePanel && typeof window.CodePanel.loadChunk === 'function') {
            window.CodePanel.loadChunk({
              code: rawCode,
              explanation: "Loaded from teacher chat",
              expected_output: null
            });
          } else if (window.CodePanel && typeof window.CodePanel.setCode === 'function') {
            window.CodePanel.setCode(rawCode);
            if (typeof window.CodePanel.run === 'function') window.CodePanel.run();
          } else {
            console.warn('[ChatPanel] window.CodePanel not loaded');
          }
        });
      });
    }

    async sendMessage(text) {
      this.lastFailedMessage = null;
      this.container.querySelector('#chat-error-banner').style.display = 'none';

      // 1. Add user message
      this.addMessage({ sender: 'user', text });

      // 2. Prepare payload from getContext()
      const ctx = typeof this.getContext === 'function' ? this.getContext() : {};
      const topic = ctx.topic || 'Binary Search';
      const stepIndex = ctx.step_index !== undefined ? ctx.step_index : (ctx.current_step_index || 0);
      const userId = ctx.user_id || ctx.student_id || 'demo_student';
      
      // History formatting
      const history = (ctx.history || []).concat(
        this.messages.slice(-6).map(m => ({
          role: m.sender === 'user' ? 'user' : 'assistant',
          content: m.text
        }))
      );

      // Payload supporting both Member 1 spec and existing FastAPI models
      const payload = {
        message: text,
        topic: topic,
        concept: topic,
        step_index: stepIndex,
        current_step_index: stepIndex,
        history: history,
        user_id: userId,
        student_id: userId
      };

      // 3. Show typing indicator
      this.showTyping(true);
      const startTime = performance.now();

      try {
        const response = await fetch(`${this.apiBase}/agent/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        const duration = Math.round(performance.now() - startTime);

        const replyText = data.reply || data.response || "I'm here to help!";
        const trace = data.trace || {
          source: data.provider_metadata ? data.provider_metadata.provider : 'mock',
          provider: data.provider_metadata ? data.provider_metadata.provider : 'agent',
          latency_ms: duration
        };

        // If code snippet is included in response payload, append it
        let fullReply = replyText;
        if (data.code && !replyText.includes(data.code)) {
          fullReply += `\n\n\`\`\`python\n${data.code}\n\`\`\``;
        }

        this.showTyping(false);
        this.addMessage({
          sender: 'teacher',
          text: fullReply,
          trace: trace
        });

        // Trigger suggested whiteboard commands if board is available
        if (Array.isArray(data.board_commands || data.suggested_board_commands)) {
          const cmds = data.board_commands || data.suggested_board_commands;
          if (window.WhiteboardCanvas && typeof window.WhiteboardCanvas.executeCommands === 'function') {
            window.WhiteboardCanvas.executeCommands(cmds);
          }
        }
      } catch (err) {
        console.warn('[ChatPanel] Chat request error:', err);
        this.showTyping(false);
        this.lastFailedMessage = text;
        this.showError(`Error connecting to teacher: ${err.message || 'Network error'}`);
      }
    }

    showTyping(show) {
      this.isLoading = show;
      const indicator = this.container.querySelector('#chat-typing-indicator');
      if (indicator) {
        indicator.style.display = show ? 'block' : 'none';
        if (show) this.scrollToBottom();
      }
    }

    showError(msg) {
      const banner = this.container.querySelector('#chat-error-banner');
      const text = this.container.querySelector('#chat-error-text');
      if (banner && text) {
        text.textContent = msg;
        banner.style.display = 'flex';
        this.scrollToBottom();
      }
    }

    scrollToBottom() {
      const container = this.container.querySelector('#chat-messages-container');
      if (container) {
        setTimeout(() => {
          container.scrollTop = container.scrollHeight;
        }, 50);
      }
    }

    escapeHtml(str) {
      return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
    }

    unescapeHtml(str) {
      return String(str)
        .replace(/&amp;/g, '&')
        .replace(/&lt;/g, '<')
        .replace(/&gt;/g, '>');
    }
  }

  // Expose on window.ChatPanel
  const instance = new ChatPanelManager();
  window.ChatPanel = {
    mount: (el, options) => instance.mount(el, options),
    sendMessage: (text) => instance.sendMessage(text),
    sendQuestion: (text) => instance.sendQuestion(text)
  };
})();
