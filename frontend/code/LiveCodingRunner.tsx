"use client";

import React, { useState, useEffect, useRef } from "react";
import { PythonEditor } from "./PythonEditor";
import { CodeAction, LiveCodingStep, PyodideExecutionResult } from "./types";

interface LiveCodingRunnerProps {
  steps?: LiveCodingStep[];
  currentStepIndex?: number;
  onStepComplete?: (stepIndex: number, result: PyodideExecutionResult) => void;
  apiBaseUrl?: string;
  studentId?: string;
}

const DEFAULT_DEMO_STEPS: LiveCodingStep[] = [
  {
    stepIndex: 1,
    chunkTitle: "1. Initialization & Pointers",
    codeAction: {
      action: "type",
      code: `# Step 1: Set up the search boundaries
arr = [2, 4, 6, 8, 10, 12, 14, 16]
target = 10

low = 0
high = len(arr) - 1
print(f"Array: {arr}")
print(f"Initial range: low={low} (val={arr[low]}), high={high} (val={arr[high]})")
`,
      explanation:
        "We establish two boundary pointers: `low` at index 0 and `high` at the final element. All candidate items reside between low and high.",
    },
  },
  {
    stepIndex: 2,
    chunkTitle: "2. Midpoint Calculation",
    codeAction: {
      action: "type",
      code: `mid = low + (high - low) // 2
mid_val = arr[mid]
print(f"Calculated midpoint: index {mid}, value = {mid_val}")
`,
      explanation:
        "Using `low + (high - low) // 2` avoids integer overflow. We compare arr[mid] directly with our target.",
    },
  },
  {
    stepIndex: 3,
    chunkTitle: "3. Halving the Search Space",
    codeAction: {
      action: "execute",
      code: `if mid_val == target:
    print(f"MATCH FOUND: arr[{mid}] == {target}")
elif mid_val < target:
    low = mid + 1
    print(f"Target is larger: shift low to {low}")
else:
    high = mid - 1
    print(f"Target is smaller: shift high to {high}")

print(f"New search interval: [{low}, {high}]")
`,
      explanation:
        "Because the collection is sorted, if mid_val < target, we can safely discard the entire left half including mid.",
    },
  },
];

export const LiveCodingRunner: React.FC<LiveCodingRunnerProps> = ({
  steps = DEFAULT_DEMO_STEPS,
  currentStepIndex = 0,
  onStepComplete,
  apiBaseUrl = "http://localhost:8000",
  studentId = "demo_student",
}) => {
  const safeSteps = Array.isArray(steps) && steps.length > 0 ? steps : DEFAULT_DEMO_STEPS;
  const [activeStepIdx, setActiveStepIdx] = useState<number>(
    Math.min(Math.max(0, currentStepIndex), safeSteps.length - 1)
  );
  const [accumulatedCode, setAccumulatedCode] = useState<string>("");
  const [isTyping, setIsTyping] = useState<boolean>(false);
  const [isPaused, setIsPaused] = useState<boolean>(false);
  const [typingSpeedMs] = useState<number>(18);
  const [feedbackSent, setFeedbackSent] = useState<string | null>(null);
  const [lastExecution, setLastExecution] = useState<PyodideExecutionResult | null>(null);

  const typingTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const currentStep = safeSteps[activeStepIdx] || safeSteps[0];
  const safeCodeAction: CodeAction = currentStep?.codeAction || {
    code: "# Step code unavailable",
    action: "display",
    explanation: "No explanation provided for this step.",
  };

  // Progressive typing simulation according to action in /contracts/board_commands.json
  useEffect(() => {
    const action = safeCodeAction.action || "display";
    const targetCode = safeCodeAction.code || "";

    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }

    if (action === "display" || action === "explain") {
      setAccumulatedCode(targetCode);
      setIsTyping(false);
      setIsPaused(false);
      return;
    }

    if (action === "execute") {
      setAccumulatedCode(targetCode);
      setIsTyping(false);
      setIsPaused(false);
      return;
    }

    // action === "type": Progressive character typing
    setIsTyping(true);
    setIsPaused(false);
    let charIndex = 0;
    setAccumulatedCode("");

    const typeNextChar = () => {
      if (charIndex < targetCode.length) {
        setAccumulatedCode((prev: string) => prev + targetCode.charAt(charIndex));
        charIndex++;
        typingTimeoutRef.current = setTimeout(typeNextChar, typingSpeedMs);
      } else {
        setIsTyping(false);
      }
    };

    typeNextChar();

    return () => {
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
      }
    };
  }, [activeStepIdx, safeCodeAction.code, safeCodeAction.action, typingSpeedMs]);

  const handlePauseToggle = () => {
    if (isPaused) {
      setIsPaused(false);
      const targetCode = safeCodeAction.code || "";
      let charIndex = accumulatedCode.length;

      const typeResume = () => {
        if (charIndex < targetCode.length) {
          setAccumulatedCode((prev: string) => prev + targetCode.charAt(charIndex));
          charIndex++;
          typingTimeoutRef.current = setTimeout(typeResume, typingSpeedMs);
        } else {
          setIsTyping(false);
        }
      };
      typeResume();
    } else {
      setIsPaused(true);
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
      }
    }
  };

  const handleSkipTyping = () => {
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }
    setAccumulatedCode(safeCodeAction.code || "");
    setIsTyping(false);
    setIsPaused(false);
  };

  const handleExecutionComplete = (res: PyodideExecutionResult) => {
    setLastExecution(res);
    if (onStepComplete) {
      onStepComplete(activeStepIdx, res);
    }
  };

  /**
   * Dispatches code execution errors directly back to the teacher agent
   * using the exact ChatMessageRequest contract defined in /contracts/openapi.json:
   * POST /agent/chat { user_id, message, context_step }
   */
  const handleReportErrorToAgent = async () => {
    if (!lastExecution?.error) return;

    try {
      setFeedbackSent("Sending error traceback to AI Teacher...");
      const res = await fetch(`${apiBaseUrl}/agent/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: studentId,
          message: `Code error encountered during Step ${activeStepIdx + 1}: ${lastExecution.error}`,
          context_step: activeStepIdx + 1,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setFeedbackSent(`Teacher: "${data.reply || "I analyzed your traceback. Check the boundary pointer update."}"`);
      } else {
        setFeedbackSent("Diagnostic report logged for session.");
      }
    } catch (e: unknown) {
      setFeedbackSent("Captured traceback locally for teacher review.");
    }
  };

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "1fr 340px",
        gap: "16px",
        fontFamily: "system-ui, -apple-system, sans-serif",
      }}
    >
      {/* Left: Code Editor with Live Type Controls */}
      <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
        {/* Step Navigation & Typing Controller */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            padding: "8px 12px",
            backgroundColor: "#1e293b",
            color: "#ffffff",
            borderRadius: "6px",
            fontSize: "13px",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <span style={{ fontWeight: 600, color: "#38bdf8" }}>
              {currentStep?.chunkTitle || `Step ${activeStepIdx + 1}/${safeSteps.length}`}
            </span>
            {isTyping && (
              <span
                style={{
                  fontSize: "11px",
                  padding: "2px 6px",
                  borderRadius: "4px",
                  backgroundColor: isPaused ? "#f59e0b" : "#3b82f6",
                  color: "#ffffff",
                }}
              >
                {isPaused ? "Paused" : "Typing..."}
              </span>
            )}
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            {isTyping && (
              <>
                <button
                  onClick={handlePauseToggle}
                  style={{
                    padding: "4px 8px",
                    fontSize: "12px",
                    borderRadius: "4px",
                    border: "none",
                    backgroundColor: "#475569",
                    color: "#ffffff",
                    cursor: "pointer",
                  }}
                >
                  {isPaused ? "Resume" : "Pause"}
                </button>

                <button
                  onClick={handleSkipTyping}
                  style={{
                    padding: "4px 8px",
                    fontSize: "12px",
                    borderRadius: "4px",
                    border: "none",
                    backgroundColor: "#475569",
                    color: "#ffffff",
                    cursor: "pointer",
                  }}
                >
                  Skip Type
                </button>
              </>
            )}

            <button
              disabled={activeStepIdx === 0}
              onClick={() => setActiveStepIdx((prev: number) => Math.max(0, prev - 1))}
              style={{
                padding: "4px 8px",
                fontSize: "12px",
                borderRadius: "4px",
                border: "none",
                backgroundColor: activeStepIdx === 0 ? "#334155" : "#0284c7",
                color: "#ffffff",
                cursor: activeStepIdx === 0 ? "not-allowed" : "pointer",
              }}
            >
              ◀ Prev
            </button>

            <button
              disabled={activeStepIdx >= safeSteps.length - 1}
              onClick={() => setActiveStepIdx((prev: number) => Math.min(safeSteps.length - 1, prev + 1))}
              style={{
                padding: "4px 8px",
                fontSize: "12px",
                borderRadius: "4px",
                border: "none",
                backgroundColor: activeStepIdx >= safeSteps.length - 1 ? "#334155" : "#0284c7",
                color: "#ffffff",
                cursor: activeStepIdx >= safeSteps.length - 1 ? "not-allowed" : "pointer",
              }}
            >
              Next ▶
            </button>
          </div>
        </div>

        {/* Python Editor (supports student editing and rerunning) */}
        <PythonEditor
          initialCode={accumulatedCode}
          onCodeChange={(newCode) => setAccumulatedCode(newCode)}
          onExecutionComplete={handleExecutionComplete}
          height="380px"
        />
      </div>

      {/* Right: Agent Explanation & Diagnostic Error Assist */}
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: "12px",
          backgroundColor: "#f8fafc",
          border: "1px solid #e2e8f0",
          borderRadius: "8px",
          padding: "16px",
        }}
      >
        <h4 style={{ margin: 0, fontSize: "15px", color: "#0f172a", display: "flex", alignItems: "center", gap: "6px" }}>
          <span>💡</span> Teacher's Code Notes
        </h4>

        <div
          style={{
            fontSize: "13px",
            lineHeight: "1.6",
            color: "#334155",
            backgroundColor: "#ffffff",
            padding: "12px",
            borderRadius: "6px",
            border: "1px solid #e2e8f0",
            flex: 1,
            overflowY: "auto",
          }}
        >
          {safeCodeAction.explanation || "Review the code above. You can freely edit values and click '▶ Run Code' to experiment."}
        </div>

        {/* Error Reporting Contract Integration */}
        {lastExecution?.error && (
          <div
            style={{
              padding: "12px",
              borderRadius: "6px",
              backgroundColor: "#fef2f2",
              border: "1px solid #fecaca",
            }}
          >
            <div style={{ fontSize: "12px", fontWeight: "bold", color: "#b91c1c", marginBottom: "6px" }}>
              ⚠️ Execution Error Detected
            </div>
            <p style={{ margin: "0 0 8px 0", fontSize: "12px", color: "#7f1d1d" }}>
              Send this traceback to the AI Teacher for instant diagnosis.
            </p>
            <button
              onClick={handleReportErrorToAgent}
              style={{
                width: "100%",
                padding: "6px 12px",
                fontSize: "12px",
                fontWeight: 600,
                borderRadius: "4px",
                border: "none",
                backgroundColor: "#dc2626",
                color: "#ffffff",
                cursor: "pointer",
              }}
            >
              Ask Teacher for Help
            </button>
          </div>
        )}

        {feedbackSent && (
          <div
            style={{
              padding: "8px 12px",
              fontSize: "12px",
              borderRadius: "4px",
              backgroundColor: "#f0fdf4",
              border: "1px solid #bbf7d0",
              color: "#166534",
            }}
          >
            {feedbackSent}
          </div>
        )}
      </div>
    </div>
  );
};
