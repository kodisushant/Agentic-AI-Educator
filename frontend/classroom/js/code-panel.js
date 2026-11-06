/**
 * CodePanel - In-Browser Python Monaco Editor with Pyodide WebAssembly runtime.
 * Implements window.CodePanel per the Hackathon Shared Spec:
 *   - mount(el)
 *   - loadChunk({code, explanation, expected_output})
 *   - pause()
 *   - resume()
 *   - run()
 */

(function () {
  'use strict';

  // Pyodide Worker source code as inline script
  const PYODIDE_WORKER_CODE = `
    let pyodideInstance = null;
    let isInitializing = false;

    async function getPyodide() {
      if (pyodideInstance) return pyodideInstance;
      if (isInitializing) {
        while (isInitializing) {
          await new Promise(r => setTimeout(r, 50));
        }
        return pyodideInstance;
      }
      isInitializing = true;
      try {
        importScripts("https://cdn.jsdelivr.net/pyodide/v0.25.0/full/pyodide.js");
        pyodideInstance = await loadPyodide();
        isInitializing = false;
        return pyodideInstance;
      } catch (err) {
        isInitializing = false;
        throw err;
      }
    }

    self.onmessage = async function(e) {
      const { id, type, code } = e.data;
      if (type === 'init') {
        try {
          await getPyodide();
          self.postMessage({ id, type: 'ready' });
        } catch (err) {
          self.postMessage({ id, type: 'init_error', error: err.message || String(err) });
        }
      } else if (type === 'run') {
        try {
          const py = await getPyodide();
          const stdoutArr = [];
          const stderrArr = [];
          
          py.setStdout({ batched: (msg) => stdoutArr.push(msg) });
          py.setStderr({ batched: (msg) => stderrArr.push(msg) });

          const startTime = performance.now();
          const result = await py.runPythonAsync(code);
          const duration = Math.round(performance.now() - startTime);

          self.postMessage({
            id,
            type: 'done',
            stdout: stdoutArr.join('\\n'),
            stderr: stderrArr.join('\\n'),
            result: result !== undefined && result !== null ? String(result) : null,
            duration
          });
        } catch (err) {
          self.postMessage({
            id,
            type: 'error',
            error: err.message || String(err)
          });
        }
      }
    };
  `;

  class CodePanelManager {
    constructor() {
      this.container = null;
      this.editor = null;
      this.worker = null;
      this.pyodideStatus = 'unloaded'; // 'unloaded' | 'loading' | 'ready' | 'error'
      this.isExecuting = false;
      this.currentExecId = 0;
      
      // Typing animation state
      this.typingTimer = null;
      this.isPaused = false;
      this.typingTargetCode = '';
      this.typingCurrentIndex = 0;
      this.typingExplanation = '';
      this.typingExpectedOutput = null;

      // Pending chunk info
      this.lastExecutionOutput = '';
      this.lastExecutionError = '';
    }

    mount(el) {
      if (typeof el === 'string') {
        el = document.querySelector(el);
      }
      if (!el) {
        console.error('[CodePanel] Mount element not found');
        return;
      }
      this.container = el;
      this.renderUI();
      this.initMonaco();
      this.initPyodide();
    }

    renderUI() {
      this.container.innerHTML = `
        <div class="code-panel-root" style="display: flex; flex-direction: column; height: 100%; min-height: 480px; background: #0f172a; border-radius: 8px; overflow: hidden; font-family: ui-sans-serif, system-ui, sans-serif; color: #f8fafc; border: 1px solid #334155;">
          <!-- Header Bar -->
          <div style="display: flex; align-items: center; justify-content: space-between; padding: 10px 14px; background: #1e293b; border-bottom: 1px solid #334155;">
            <div style="display: flex; align-items: center; gap: 8px;">
              <span style="font-weight: 600; font-size: 13px; letter-spacing: 0.02em; color: #38bdf8;">Python Live Playground</span>
              <span id="cp-pyodide-status" style="display: inline-flex; align-items: center; gap: 5px; font-size: 11px; padding: 2px 8px; border-radius: 9999px; background: #334155; color: #94a3b8;">
                <span style="width: 6px; height: 6px; border-radius: 50%; background: #eab308; display: inline-block;"></span>
                loading Python...
              </span>
            </div>
            
            <div style="display: flex; align-items: center; gap: 6px;">
              <!-- Typing controls (hidden unless chunk is typing) -->
              <div id="cp-typing-controls" style="display: none; align-items: center; gap: 4px; margin-right: 6px;">
                <button id="cp-pause-btn" style="padding: 4px 8px; background: #475569; color: #fff; border: none; border-radius: 4px; font-size: 11px; cursor: pointer;">Pause</button>
                <button id="cp-skip-btn" style="padding: 4px 8px; background: #334155; color: #cbd5e1; border: none; border-radius: 4px; font-size: 11px; cursor: pointer;">Skip</button>
              </div>

              <button id="cp-clear-btn" style="padding: 5px 12px; background: #334155; color: #e2e8f0; border: none; border-radius: 5px; font-size: 12px; font-weight: 500; cursor: pointer; transition: background 0.15s;">
                Clear
              </button>
              <button id="cp-run-btn" style="display: inline-flex; align-items: center; gap: 5px; padding: 5px 14px; background: #0284c7; color: #ffffff; border: none; border-radius: 5px; font-size: 12px; font-weight: 600; cursor: pointer; transition: background 0.15s;">
                <span id="cp-run-icon">▶</span> Run
              </button>
            </div>
          </div>

          <!-- Explanation Banner (optional chunk explanation) -->
          <div id="cp-explanation-box" style="display: none; padding: 8px 14px; background: #1e1b4b; border-bottom: 1px solid #312e81; color: #c7d2fe; font-size: 12px; line-height: 1.4;">
            <div style="font-weight: 600; color: #818cf8; margin-bottom: 2px;">Teacher's Note:</div>
            <div id="cp-explanation-text"></div>
          </div>

          <!-- Monaco Editor Mount Container -->
          <div id="cp-editor-container" style="flex: 1 1 55%; min-height: 200px; position: relative;">
            <div id="cp-editor-placeholder" style="position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; color: #64748b; font-size: 13px;">
              Initializing editor...
            </div>
          </div>

          <!-- Output Header and Body -->
          <div style="flex: 0 0 auto; display: flex; flex-direction: column; background: #090d16; border-top: 1px solid #334155; max-height: 45%;">
            <div style="display: flex; align-items: center; justify-content: space-between; padding: 6px 14px; background: #131b2e; border-bottom: 1px solid #1e293b;">
              <span style="font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: #94a3b8;">Output Terminal</span>
              <div id="cp-output-badges" style="display: flex; align-items: center; gap: 6px;"></div>
            </div>

            <!-- Terminal Output Area -->
            <div id="cp-output-body" style="padding: 10px 14px; font-family: ui-monospace, Menlo, Monaco, Consolas, monospace; font-size: 12px; line-height: 1.5; color: #e2e8f0; min-height: 90px; max-height: 180px; overflow-y: auto; white-space: pre-wrap; word-break: break-all;">
              <span style="color: #64748b;">Ready. Click "Run" to execute Python code.</span>
            </div>

            <!-- Error Action Bar: Ask Teacher About This Error -->
            <div id="cp-error-bar" style="display: none; align-items: center; justify-content: space-between; padding: 8px 14px; background: #450a0a; border-top: 1px solid #991b1b;">
              <span style="font-size: 12px; color: #fca5a5;">Python execution error detected</span>
              <button id="cp-ask-teacher-btn" style="padding: 4px 10px; background: #dc2626; color: #fff; border: none; border-radius: 4px; font-size: 11px; font-weight: 600; cursor: pointer;">
                Ask teacher about this error 💬
              </button>
            </div>
          </div>
        </div>
      `;

      // Attach event listeners
      this.container.querySelector('#cp-run-btn').addEventListener('click', () => this.run());
      this.container.querySelector('#cp-clear-btn').addEventListener('click', () => this.clear());
      this.container.querySelector('#cp-pause-btn').addEventListener('click', () => {
        if (this.isPaused) {
          this.resume();
        } else {
          this.pause();
        }
      });
      this.container.querySelector('#cp-skip-btn').addEventListener('click', () => this.skipTyping());
      this.container.querySelector('#cp-ask-teacher-btn').addEventListener('click', () => this.askTeacherAboutError());
    }

    initMonaco() {
      const editorHost = this.container.querySelector('#cp-editor-container');
      
      const setupEditor = () => {
        try {
          const placeholder = this.container.querySelector('#cp-editor-placeholder');
          if (placeholder) placeholder.remove();

          this.editor = window.monaco.editor.create(editorHost, {
            value: `# Python Live Code Playground\ndef binary_search(arr, target):\n    low = 0\n    high = len(arr) - 1\n    while low <= high:\n        mid = (low + high) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            low = mid + 1\n        else:\n            high = mid - 1\n    return -1\n\nnumbers = [1, 3, 5, 7, 9, 11]\nprint("Searching for 7 in", numbers)\nindex = binary_search(numbers, 7)\nprint("Found at index:", index)\n`,
            language: 'python',
            theme: 'vs-dark',
            automaticLayout: true,
            minimap: { enabled: false },
            fontSize: 13,
            lineNumbers: 'on',
            scrollBeyondLastLine: false,
            padding: { top: 8, bottom: 8 }
          });
        } catch (err) {
          console.error('[CodePanel] Monaco creation error:', err);
          this.fallbackTextarea(editorHost);
        }
      };

      if (window.monaco && window.monaco.editor) {
        setupEditor();
      } else {
        // Load monaco via require.js CDN
        if (!window.require) {
          const loaderScript = document.createElement('script');
          loaderScript.src = 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.45.0/min/vs/loader.min.js';
          loaderScript.onload = () => {
            window.require.config({
              paths: { vs: 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.45.0/min/vs' }
            });
            window.require(['vs/editor/editor.main'], () => {
              setupEditor();
            });
          };
          loaderScript.onerror = () => {
            console.warn('[CodePanel] Monaco CDN failed to load; using fallback editor');
            this.fallbackTextarea(editorHost);
          };
          document.head.appendChild(loaderScript);
        } else {
          window.require(['vs/editor/editor.main'], () => {
            setupEditor();
          });
        }
      }
    }

    fallbackTextarea(host) {
      host.innerHTML = `
        <textarea id="cp-fallback-code" style="width: 100%; height: 100%; background: #0f172a; color: #38bdf8; font-family: monospace; font-size: 13px; border: none; padding: 12px; outline: none; resize: none; box-sizing: border-box;"># Python Code
print("Hello from Python")
</textarea>
      `;
      this.editor = {
        getValue: () => host.querySelector('#cp-fallback-code').value,
        setValue: (val) => { host.querySelector('#cp-fallback-code').value = val; },
        layout: () => {}
      };
    }

    initPyodide() {
      this.setPyodideStatus('loading');
      try {
        const blob = new Blob([PYODIDE_WORKER_CODE], { type: 'application/javascript' });
        const workerUrl = URL.createObjectURL(blob);
        this.worker = new Worker(workerUrl);

        this.worker.onmessage = (e) => {
          const { type, error } = e.data;
          if (type === 'ready') {
            this.setPyodideStatus('ready');
          } else if (type === 'init_error') {
            console.warn('[CodePanel] Pyodide worker init error:', error);
            this.setPyodideStatus('error');
          }
        };

        this.worker.onerror = (err) => {
          console.warn('[CodePanel] Pyodide Worker error, will fall back:', err);
          this.setPyodideStatus('error');
        };

        // Trigger init in worker
        this.worker.postMessage({ id: 0, type: 'init' });
      } catch (err) {
        console.warn('[CodePanel] Web Worker creation blocked:', err);
        this.setPyodideStatus('error');
      }
    }

    setPyodideStatus(status) {
      this.pyodideStatus = status;
      const el = this.container.querySelector('#cp-pyodide-status');
      if (!el) return;

      if (status === 'loading') {
        el.innerHTML = `<span style="width: 6px; height: 6px; border-radius: 50%; background: #eab308; display: inline-block;"></span> loading Python...`;
        el.style.background = '#334155';
        el.style.color = '#e2e8f0';
      } else if (status === 'ready') {
        el.innerHTML = `<span style="width: 6px; height: 6px; border-radius: 50%; background: #22c55e; display: inline-block;"></span> Python Ready`;
        el.style.background = '#064e3b';
        el.style.color = '#86efac';
      } else if (status === 'error') {
        el.innerHTML = `<span style="width: 6px; height: 6px; border-radius: 50%; background: #f97316; display: inline-block;"></span> Python (Fallback)`;
        el.style.background = '#451a03';
        el.style.color = '#fdba74';
      }
    }

    setCode(code) {
      if (this.editor && typeof this.editor.setValue === 'function') {
        this.editor.setValue(code);
      }
    }

    getCode() {
      if (this.editor && typeof this.editor.getValue === 'function') {
        return this.editor.getValue();
      }
      return '';
    }

    /**
     * loadChunk({code, explanation, expected_output}):
     * types the code in gradually (cancelable), shows explanation, auto-runs at end and compares.
     */
    loadChunk({ code, explanation, expected_output }) {
      if (!code) return;
      this.stopTyping();

      this.typingTargetCode = code;
      this.typingCurrentIndex = 0;
      this.typingExplanation = explanation || '';
      this.typingExpectedOutput = expected_output !== undefined ? expected_output : null;
      this.isPaused = false;

      // Display explanation if provided
      const expBox = this.container.querySelector('#cp-explanation-box');
      const expText = this.container.querySelector('#cp-explanation-text');
      if (this.typingExplanation) {
        expText.textContent = this.typingExplanation;
        expBox.style.display = 'block';
      } else {
        expBox.style.display = 'none';
      }

      // Show typing controls
      const typingControls = this.container.querySelector('#cp-typing-controls');
      typingControls.style.display = 'inline-flex';
      const pauseBtn = this.container.querySelector('#cp-pause-btn');
      pauseBtn.textContent = 'Pause';

      // Clear editor and output
      this.setCode('');
      this.clearOutput();

      this.stepTyping();
    }

    stepTyping() {
      if (this.isPaused) return;

      const chunkSize = 2; // type 2 characters per tick for smooth progressive typing
      const nextIndex = Math.min(this.typingCurrentIndex + chunkSize, this.typingTargetCode.length);
      this.typingCurrentIndex = nextIndex;

      const currentSnippet = this.typingTargetCode.slice(0, nextIndex);
      this.setCode(currentSnippet);

      if (this.typingCurrentIndex < this.typingTargetCode.length) {
        this.typingTimer = setTimeout(() => this.stepTyping(), 25);
      } else {
        // Typing finished!
        this.finishTyping();
      }
    }

    pause() {
      this.isPaused = true;
      if (this.typingTimer) {
        clearTimeout(this.typingTimer);
        this.typingTimer = null;
      }
      const pauseBtn = this.container.querySelector('#cp-pause-btn');
      if (pauseBtn) pauseBtn.textContent = 'Resume';
    }

    resume() {
      if (!this.isPaused) return;
      this.isPaused = false;
      const pauseBtn = this.container.querySelector('#cp-pause-btn');
      if (pauseBtn) pauseBtn.textContent = 'Pause';
      this.stepTyping();
    }

    stopTyping() {
      if (this.typingTimer) {
        clearTimeout(this.typingTimer);
        this.typingTimer = null;
      }
      this.isPaused = false;
      const typingControls = this.container.querySelector('#cp-typing-controls');
      if (typingControls) typingControls.style.display = 'none';
    }

    skipTyping() {
      this.stopTyping();
      this.setCode(this.typingTargetCode);
      this.finishTyping();
    }

    finishTyping() {
      this.stopTyping();
      // Auto-run at the end of typing
      this.run((stdout, stderr, error) => {
        if (this.typingExpectedOutput !== null && !error) {
          this.compareOutput(stdout, this.typingExpectedOutput);
        }
      });
    }

    compareOutput(actual, expected) {
      const normActual = String(actual || '').trim();
      const normExpected = String(expected || '').trim();
      const badgeContainer = this.container.querySelector('#cp-output-badges');

      if (normActual === normExpected) {
        const badge = document.createElement('span');
        badge.style.cssText = 'padding: 2px 8px; border-radius: 4px; font-size: 11px; background: #064e3b; color: #86efac; font-weight: 600;';
        badge.textContent = '✓ Output Matches Expected';
        badgeContainer.appendChild(badge);
      } else {
        const badge = document.createElement('span');
        badge.style.cssText = 'padding: 2px 8px; border-radius: 4px; font-size: 11px; background: #451a03; color: #fde047; font-weight: 500;';
        badge.textContent = `Expected: "${normExpected}"`;
        badgeContainer.appendChild(badge);
      }
    }

    /**
     * run(): executes editor's code with 5s timeout guard and stdout/stderr capture
     */
    run(onFinishCallback) {
      if (this.isExecuting) return;
      const code = this.getCode();
      if (!code.trim()) return;

      this.isExecuting = true;
      const runBtn = this.container.querySelector('#cp-run-btn');
      const runIcon = this.container.querySelector('#cp-run-icon');
      runBtn.style.opacity = '0.7';
      runBtn.style.cursor = 'wait';
      runIcon.textContent = '⏳';

      const outputBody = this.container.querySelector('#cp-output-body');
      const errorBar = this.container.querySelector('#cp-error-bar');
      const badges = this.container.querySelector('#cp-output-badges');
      badges.innerHTML = '';
      errorBar.style.display = 'none';
      outputBody.innerHTML = '<span style="color: #94a3b8;">Executing Python code...</span>';

      const execId = ++this.currentExecId;
      let timedOut = false;

      // 5-second timeout guard
      const timeoutId = setTimeout(() => {
        timedOut = true;
        this.handleExecutionTimeout(execId, onFinishCallback);
      }, 5000);

      const cleanup = () => {
        clearTimeout(timeoutId);
        this.isExecuting = false;
        runBtn.style.opacity = '1';
        runBtn.style.cursor = 'pointer';
        runIcon.textContent = '▶';
      };

      if (this.worker && this.pyodideStatus !== 'error') {
        const messageHandler = (e) => {
          if (e.data.id !== execId) return;
          this.worker.removeEventListener('message', messageHandler);
          if (timedOut) return;

          cleanup();
          const { type, stdout, stderr, error, duration } = e.data;

          if (type === 'done') {
            this.handleExecutionSuccess(stdout, stderr, duration);
            if (onFinishCallback) onFinishCallback(stdout, stderr, null);
          } else {
            this.handleExecutionError(error || stderr || 'Runtime error');
            if (onFinishCallback) onFinishCallback(stdout, stderr, error);
          }
        };

        this.worker.addEventListener('message', messageHandler);
        this.worker.postMessage({ id: execId, type: 'run', code });
      } else {
        // Fallback: direct simulation or lightweight Python interpreter fallback
        setTimeout(() => {
          if (timedOut) return;
          cleanup();
          this.simulateExecution(code, onFinishCallback);
        }, 100);
      }
    }

    handleExecutionTimeout(execId, onFinishCallback) {
      this.isExecuting = false;
      const runBtn = this.container.querySelector('#cp-run-btn');
      const runIcon = this.container.querySelector('#cp-run-icon');
      runBtn.style.opacity = '1';
      runBtn.style.cursor = 'pointer';
      runIcon.textContent = '▶';

      // Terminate hanging worker to break infinite loops
      if (this.worker) {
        try {
          this.worker.terminate();
        } catch (_) {}
        this.initPyodide();
      }

      const errorMsg = 'TimeoutError: Execution exceeded 5.0s time limit (possible infinite loop).';
      this.handleExecutionError(errorMsg);
      if (onFinishCallback) onFinishCallback('', '', errorMsg);
    }

    handleExecutionSuccess(stdout, stderr, duration) {
      const outputBody = this.container.querySelector('#cp-output-body');
      const badges = this.container.querySelector('#cp-output-badges');
      this.lastExecutionOutput = stdout || '';
      this.lastExecutionError = '';

      outputBody.innerHTML = '';

      if (stdout) {
        const outPre = document.createElement('div');
        outPre.style.color = '#38bdf8';
        outPre.textContent = stdout;
        outputBody.appendChild(outPre);
      }

      if (stderr) {
        const errPre = document.createElement('div');
        errPre.style.color = '#fbbf24';
        errPre.textContent = stderr;
        outputBody.appendChild(errPre);
      }

      if (!stdout && !stderr) {
        outputBody.innerHTML = '<span style="color: #64748b;">(Code executed with no output)</span>';
      }

      if (duration !== undefined) {
        const durBadge = document.createElement('span');
        durBadge.style.cssText = 'padding: 2px 6px; border-radius: 4px; font-size: 11px; background: #1e293b; color: #94a3b8;';
        durBadge.textContent = `${duration}ms`;
        badges.appendChild(durBadge);
      }
    }

    handleExecutionError(error) {
      const outputBody = this.container.querySelector('#cp-output-body');
      const errorBar = this.container.querySelector('#cp-error-bar');
      this.lastExecutionError = error;

      outputBody.innerHTML = `<div style="color: #f87171; font-weight: 500;">${this.escapeHtml(error)}</div>`;
      errorBar.style.display = 'flex';
    }

    simulateExecution(code, onFinishCallback) {
      // Clean fallback if Web Worker is restricted
      try {
        let simulatedOut = '';
        const printRegex = /print\((.*?)\)/g;
        let match;
        while ((match = printRegex.exec(code)) !== null) {
          try {
            // Evaluates simple strings or numbers
            simulatedOut += eval(match[1]) + '\n';
          } catch (_) {
            simulatedOut += match[1].replace(/['"]/g, '') + '\n';
          }
        }
        if (!simulatedOut) simulatedOut = 'Program ran successfully (simulated).\n';
        this.handleExecutionSuccess(simulatedOut.trim(), '', 12);
        if (onFinishCallback) onFinishCallback(simulatedOut.trim(), '', null);
      } catch (err) {
        this.handleExecutionError(String(err));
        if (onFinishCallback) onFinishCallback('', '', String(err));
      }
    }

    askTeacherAboutError() {
      const code = this.getCode();
      const error = this.lastExecutionError || 'Unknown error occurred';

      if (window.ChatPanel && typeof window.ChatPanel.sendQuestion === 'function') {
        const prompt = `I ran this code:\n\`\`\`python\n${code}\n\`\`\`\nAnd got this error:\n\`\`\`\n${error}\n\`\`\`\nCan you explain why this happened and how to fix it?`;
        window.ChatPanel.sendQuestion(prompt);
      } else {
        alert(`Error message to teacher:\n\n${error}\n\n(ChatPanel not connected yet)`);
      }
    }

    clear() {
      this.clearOutput();
      const expBox = this.container.querySelector('#cp-explanation-box');
      if (expBox) expBox.style.display = 'none';
      this.stopTyping();
    }

    clearOutput() {
      const outputBody = this.container.querySelector('#cp-output-body');
      const errorBar = this.container.querySelector('#cp-error-bar');
      const badges = this.container.querySelector('#cp-output-badges');
      if (outputBody) outputBody.innerHTML = '<span style="color: #64748b;">Terminal cleared.</span>';
      if (errorBar) errorBar.style.display = 'none';
      if (badges) badges.innerHTML = '';
      this.lastExecutionOutput = '';
      this.lastExecutionError = '';
    }

    escapeHtml(str) {
      return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
    }
  }

  // Expose on window.CodePanel
  const instance = new CodePanelManager();
  window.CodePanel = {
    mount: (el) => instance.mount(el),
    loadChunk: (chunk) => instance.loadChunk(chunk),
    pause: () => instance.pause(),
    resume: () => instance.resume(),
    run: () => instance.run(),
    // Helpful extra utilities
    setCode: (code) => instance.setCode(code),
    getCode: () => instance.getCode(),
    clear: () => instance.clear()
  };
})();
