"use client";

import React, { useState, useEffect, useRef } from "react";
import { usePyodide } from "./usePyodide";
import { PyodideExecutionResult } from "./types";

interface MonacoEditorInstance {
  getValue: () => string;
  setValue: (value: string) => void;
  onDidChangeModelContent: (listener: () => void) => void;
  dispose: () => void;
}

interface MonacoNamespace {
  editor: {
    create: (
      element: HTMLElement,
      options: {
        value: string;
        language: string;
        theme: string;
        readOnly?: boolean;
        minimap?: { enabled: boolean };
        fontSize?: number;
        automaticLayout?: boolean;
        scrollBeyondLastLine?: boolean;
      }
    ) => MonacoEditorInstance;
  };
}

declare global {
  interface Window {
    monaco?: MonacoNamespace;
    require?: {
      config: (config: { paths: Record<string, string> }) => void;
      (modules: string[], callback: () => void): void;
    };
  }
}

interface PythonEditorProps {
  initialCode?: string;
  onCodeChange?: (code: string) => void;
  onExecutionComplete?: (res: PyodideExecutionResult) => void;
  readOnly?: boolean;
  height?: string;
  theme?: "vs-dark" | "light";
}

const DEFAULT_PYTHON_CODE = `# Binary Search Implementation
def binary_search(arr, target):
    low = 0
    high = len(arr) - 1
    
    while low <= high:
        mid = low + (high - low) // 2
        print(f"Checking index {mid}, value = {arr[mid]}")
        
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
            
    return -1

# Test sample
numbers = [1, 3, 5, 7, 9, 11, 13]
target = 7
print(f"Searching for {target} in {numbers}")
result = binary_search(numbers, target)
print(f"Found {target} at index: {result}")
`;

export const PythonEditor: React.FC<PythonEditorProps> = ({
  initialCode = DEFAULT_PYTHON_CODE,
  onCodeChange,
  onExecutionComplete,
  readOnly = false,
  height = "420px",
  theme = "vs-dark",
}) => {
  const [code, setCode] = useState<string>(initialCode);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<"stdout" | "errors">("stdout");
  const [output, setOutput] = useState<PyodideExecutionResult | null>(null);
  const [monacoLoaded, setMonacoLoaded] = useState<boolean>(false);

  const editorContainerRef = useRef<HTMLDivElement | null>(null);
  const monacoInstanceRef = useRef<MonacoEditorInstance | null>(null);

  const { status: pyodideStatus, runPython } = usePyodide();

  // 1. Attempt to load Monaco Editor dynamically via AMD Loader
  useEffect(() => {
    if (typeof window === "undefined") return;

    if (window.monaco) {
      setMonacoLoaded(true);
      return;
    }

    const scriptId = "monaco-amd-loader";
    if (!document.getElementById(scriptId)) {
      const script = document.createElement("script");
      script.id = scriptId;
      script.src = "https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.45.0/min/vs/loader.min.js";
      script.async = true;
      script.onload = () => {
        const requireFn = window.require;
        if (requireFn) {
          requireFn.config({
            paths: { vs: "https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.45.0/min/vs" },
          });
          requireFn(["vs/editor/editor.main"], () => {
            setMonacoLoaded(true);
          });
        }
      };
      script.onerror = () => {
        console.info("Monaco CDN loader skipped; using native framework editor fallback.");
      };
      document.head.appendChild(script);
    }
  }, []);

  // 2. Mount Monaco Editor instance into container if available
  useEffect(() => {
    if (!monacoLoaded || !editorContainerRef.current || !window.monaco) return;

    const monaco = window.monaco;
    if (!monacoInstanceRef.current) {
      const editor = monaco.editor.create(editorContainerRef.current, {
        value: code,
        language: "python",
        theme: theme === "vs-dark" ? "vs-dark" : "vs",
        readOnly,
        minimap: { enabled: false },
        fontSize: 13,
        automaticLayout: true,
        scrollBeyondLastLine: false,
      });

      editor.onDidChangeModelContent(() => {
        const val = editor.getValue();
        setCode(val);
        if (onCodeChange) onCodeChange(val);
      });

      monacoInstanceRef.current = editor;
    }

    return () => {
      if (monacoInstanceRef.current) {
        monacoInstanceRef.current.dispose();
        monacoInstanceRef.current = null;
      }
    };
  }, [monacoLoaded, theme, readOnly, onCodeChange, code]);

  // 3. Keep Monaco and code state in sync when initialCode changes externally (e.g. Live Coding runner)
  useEffect(() => {
    if (initialCode !== undefined) {
      setCode(initialCode);
      if (monacoInstanceRef.current && monacoInstanceRef.current.getValue() !== initialCode) {
        monacoInstanceRef.current.setValue(initialCode);
      }
    }
  }, [initialCode]);

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newCode = e.target.value;
    setCode(newCode);
    if (onCodeChange) onCodeChange(newCode);
  };

  const handleRunCode = async () => {
    if (isRunning) return;
    setIsRunning(true);
    try {
      const currentCode = monacoInstanceRef.current ? monacoInstanceRef.current.getValue() : code;
      const res = await runPython(currentCode);
      setOutput(res);
      if (res.error) {
        setActiveTab("errors");
      } else {
        setActiveTab("stdout");
      }
      if (onExecutionComplete) {
        onExecutionComplete(res);
      }
    } finally {
      setIsRunning(false);
    }
  };

  const handleResetCode = () => {
    setCode(initialCode);
    if (monacoInstanceRef.current) {
      monacoInstanceRef.current.setValue(initialCode);
    }
    if (onCodeChange) {
      onCodeChange(initialCode);
    }
  };

  const handleClearOutput = () => {
    setOutput(null);
  };

  const isDark = theme === "vs-dark";

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        borderRadius: "8px",
        overflow: "hidden",
        border: isDark ? "1px solid #334155" : "1px solid #cbd5e1",
        backgroundColor: isDark ? "#0f172a" : "#f8fafc",
        fontFamily: "'Fira Code', Menlo, Monaco, 'Courier New', monospace",
        boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
      }}
    >
      {/* Editor Header Toolbar */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "8px 16px",
          backgroundColor: isDark ? "#1e293b" : "#e2e8f0",
          borderBottom: isDark ? "1px solid #334155" : "1px solid #cbd5e1",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <span style={{ fontSize: "14px", fontWeight: "bold", color: isDark ? "#38bdf8" : "#0284c7" }}>
            🐍 {monacoLoaded ? "Monaco + Pyodide Python Editor" : "Python In-Browser Editor (Pyodide)"}
          </span>
          <span
            style={{
              fontSize: "11px",
              padding: "2px 8px",
              borderRadius: "12px",
              backgroundColor: pyodideStatus.isSimulatedFallback
                ? "#d97706"
                : pyodideStatus.ready
                ? "#059669"
                : pyodideStatus.loading
                ? "#d97706"
                : "#64748b",
              color: "#ffffff",
            }}
          >
            {pyodideStatus.isSimulatedFallback
              ? "Offline Simulator Mode"
              : pyodideStatus.ready
              ? "Pyodide WASM Active"
              : pyodideStatus.loading
              ? "Loading WebAssembly..."
              : "Ready"}
          </span>
        </div>

        {/* Action Controls */}
        <div style={{ display: "flex", gap: "8px" }}>
          <button
            onClick={handleRunCode}
            disabled={isRunning}
            style={{
              padding: "6px 14px",
              fontSize: "13px",
              fontWeight: 600,
              borderRadius: "6px",
              border: "none",
              backgroundColor: isRunning ? "#94a3b8" : "#22c55e",
              color: "#ffffff",
              cursor: isRunning ? "not-allowed" : "pointer",
              display: "flex",
              alignItems: "center",
              gap: "6px",
              transition: "background-color 0.2s",
            }}
          >
            {isRunning ? "Running..." : "▶ Run Code"}
          </button>

          <button
            onClick={handleResetCode}
            disabled={isRunning || readOnly}
            style={{
              padding: "6px 12px",
              fontSize: "13px",
              borderRadius: "6px",
              border: isDark ? "1px solid #475569" : "1px solid #94a3b8",
              backgroundColor: "transparent",
              color: isDark ? "#cbd5e1" : "#475569",
              cursor: isRunning || readOnly ? "not-allowed" : "pointer",
            }}
          >
            Reset
          </button>

          <button
            onClick={handleClearOutput}
            disabled={!output}
            style={{
              padding: "6px 12px",
              fontSize: "13px",
              borderRadius: "6px",
              border: isDark ? "1px solid #475569" : "1px solid #94a3b8",
              backgroundColor: "transparent",
              color: isDark ? "#cbd5e1" : "#475569",
              cursor: !output ? "not-allowed" : "pointer",
            }}
          >
            Clear Output
          </button>
        </div>
      </div>

      {/* Editor Body: Monaco instance if loaded, else high-fidelity fallback textarea */}
      <div style={{ position: "relative", height, backgroundColor: isDark ? "#0f172a" : "#ffffff" }}>
        {monacoLoaded ? (
          <div ref={editorContainerRef} style={{ width: "100%", height: "100%" }} />
        ) : (
          <textarea
            value={code}
            onChange={handleTextareaChange}
            readOnly={readOnly}
            spellCheck={false}
            style={{
              width: "100%",
              height: "100%",
              padding: "16px",
              backgroundColor: isDark ? "#0f172a" : "#ffffff",
              color: isDark ? "#f1f5f9" : "#0f172a",
              fontSize: "14px",
              lineHeight: "1.6",
              fontFamily: "inherit",
              border: "none",
              resize: "none",
              outline: "none",
              boxSizing: "border-box",
              whiteSpace: "pre",
              overflowWrap: "normal",
              overflowX: "auto",
            }}
          />
        )}
      </div>

      {/* Output Console Panel */}
      <div
        style={{
          borderTop: isDark ? "1px solid #334155" : "1px solid #cbd5e1",
          backgroundColor: isDark ? "#090d16" : "#f1f5f9",
          minHeight: "160px",
          display: "flex",
          flexDirection: "column",
        }}
      >
        {/* Output Header Tabs */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "6px 16px",
            borderBottom: isDark ? "1px solid #1e293b" : "1px solid #e2e8f0",
            backgroundColor: isDark ? "#111827" : "#e2e8f0",
          }}
        >
          <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
            <button
              onClick={() => setActiveTab("stdout")}
              style={{
                background: "none",
                border: "none",
                fontSize: "12px",
                fontWeight: activeTab === "stdout" ? "bold" : "normal",
                color: activeTab === "stdout" ? (isDark ? "#38bdf8" : "#0284c7") : isDark ? "#94a3b8" : "#64748b",
                cursor: "pointer",
                paddingBottom: "2px",
                borderBottom: activeTab === "stdout" ? "2px solid #38bdf8" : "2px solid transparent",
              }}
            >
              Output (stdout)
            </button>
            <button
              onClick={() => setActiveTab("errors")}
              style={{
                background: "none",
                border: "none",
                fontSize: "12px",
                fontWeight: activeTab === "errors" ? "bold" : "normal",
                color: activeTab === "errors" ? "#ef4444" : isDark ? "#94a3b8" : "#64748b",
                cursor: "pointer",
                paddingBottom: "2px",
                borderBottom: activeTab === "errors" ? "2px solid #ef4444" : "2px solid transparent",
              }}
            >
              Errors {output?.error ? "(!)" : ""}
            </button>

            {output?.isSimulated && (
              <span
                style={{
                  fontSize: "11px",
                  padding: "1px 6px",
                  borderRadius: "4px",
                  backgroundColor: "#f59e0b",
                  color: "#ffffff",
                  fontWeight: "bold",
                }}
              >
                Offline Fallback Result
              </span>
            )}
          </div>

          {output && (
            <span style={{ fontSize: "11px", color: isDark ? "#94a3b8" : "#64748b" }}>
              Time: {output.executionTimeMs}ms • Status: {output.success ? "Success" : "Failed"}
            </span>
          )}
        </div>

        {/* Output Content */}
        <div
          style={{
            padding: "12px 16px",
            flex: 1,
            maxHeight: "220px",
            overflowY: "auto",
            fontSize: "13px",
            lineHeight: "1.5",
          }}
        >
          {!output ? (
            <span style={{ color: isDark ? "#475569" : "#94a3b8", fontStyle: "italic" }}>
              Click '▶ Run Code' to execute Python code in your browser.
            </span>
          ) : activeTab === "stdout" ? (
            output.stdout ? (
              <pre style={{ margin: 0, color: isDark ? "#4ade80" : "#166534", whiteSpace: "pre-wrap" }}>
                {output.stdout}
              </pre>
            ) : (
              <span style={{ color: isDark ? "#64748b" : "#94a3b8", fontStyle: "italic" }}>
                (No stdout output produced)
              </span>
            )
          ) : output.error ? (
            <pre style={{ margin: 0, color: "#f87171", whiteSpace: "pre-wrap" }}>{output.error}</pre>
          ) : (
            <span style={{ color: isDark ? "#4ade80" : "#166534" }}>No errors recorded.</span>
          )}
        </div>
      </div>
    </div>
  );
};
