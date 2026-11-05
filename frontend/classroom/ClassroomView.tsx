import React, { useEffect, useState } from "react";
import {
  LessonStep,
  BoardCommand,
  CheckAnswerResponse,
} from "./types";
import { WhiteboardCanvas } from "./WhiteboardCanvas";
import { NarrationPanel } from "./NarrationPanel";
import { ControlsBar } from "./ControlsBar";
import { AgentThoughtsBanner } from "./AgentThoughtsBanner";
import { CheckQuestionCard } from "./CheckQuestionCard";
import { TeacherChat } from "./TeacherChat";

// Embedded 5-step fallback lesson compliant with /contracts/board_commands.json
const FALLBACK_LESSON: LessonStep[] = [
  {
    step_id: "bs_step_0",
    step_index: 0,
    total_steps: 5,
    concept: "Binary Search",
    narration:
      "Welcome to Binary Search! Imagine searching for a contact in a phonebook of 1,000 pages. Instead of checking every page one by one, you open to the exact middle. If the target name is alphabetically greater, you discard the entire first half! This divide-and-conquer strategy slashes time complexity from linear to logarithmic.",
    board_commands: [
      { type: "clear", id: "clear_0" },
      {
        type: "text",
        id: "title_text",
        content: "Binary Search: Divide & Conquer",
        x: 60.0,
        y: 40.0,
        size: 24,
        color: "#f8fafc",
      },
      {
        type: "text",
        id: "array_label",
        content: "Sorted Array (n = 10):",
        x: 60.0,
        y: 95.0,
        size: 15,
        color: "#94a3b8",
      },
      { type: "box", id: "box_0", label: "2", x: 60.0, y: 125.0, width: 55.0, height: 48.0, color: "#3b82f6", fill: "#1e293b" },
      { type: "box", id: "box_1", label: "5", x: 125.0, y: 125.0, width: 55.0, height: 48.0, color: "#3b82f6", fill: "#1e293b" },
      { type: "box", id: "box_2", label: "8", x: 190.0, y: 125.0, width: 55.0, height: 48.0, color: "#3b82f6", fill: "#1e293b" },
      { type: "box", id: "box_3", label: "12", x: 255.0, y: 125.0, width: 55.0, height: 48.0, color: "#3b82f6", fill: "#1e293b" },
      { type: "box", id: "box_4", label: "16", x: 320.0, y: 125.0, width: 55.0, height: 48.0, color: "#3b82f6", fill: "#1e293b" },
      { type: "box", id: "box_5", label: "23", x: 385.0, y: 125.0, width: 55.0, height: 48.0, color: "#3b82f6", fill: "#1e293b" },
      { type: "box", id: "box_6", label: "38", x: 450.0, y: 125.0, width: 55.0, height: 48.0, color: "#3b82f6", fill: "#1e293b" },
      { type: "box", id: "box_7", label: "56", x: 515.0, y: 125.0, width: 55.0, height: 48.0, color: "#3b82f6", fill: "#1e293b" },
      { type: "box", id: "box_8", label: "72", x: 580.0, y: 125.0, width: 55.0, height: 48.0, color: "#3b82f6", fill: "#1e293b" },
      { type: "box", id: "box_9", label: "91", x: 645.0, y: 125.0, width: 55.0, height: 48.0, color: "#3b82f6", fill: "#1e293b" },
      {
        type: "arrow",
        id: "arr_low",
        start_x: 87.0,
        start_y: 215.0,
        end_x: 87.0,
        end_y: 180.0,
        label: "low = 0",
        color: "#16a34a",
      },
      {
        type: "arrow",
        id: "arr_high",
        start_x: 672.0,
        start_y: 215.0,
        end_x: 672.0,
        end_y: 180.0,
        label: "high = 9",
        color: "#dc2626",
      },
      {
        type: "equation",
        id: "eq_complexity",
        latex: "\\mathcal{O}(\\log_2 n) \\ll \\mathcal{O}(n)",
        x: 60.0,
        y: 245.0,
        label: "Logarithmic vs Linear Efficiency",
      },
      {
        type: "mermaid",
        id: "flow_overview",
        chart:
          "graph LR\n  A[Sorted Array] --> B[Check Midpoint]\n  B -->|Target == Mid| C[Found!]\n  B -->|Target < Mid| D[Search Left Half]\n  B -->|Target > Mid| E[Search Right Half]",
        x: 60.0,
        y: 340.0,
        title: "Decision Logic Flowchart",
      },
    ],
    agent_thoughts:
      "Student mastery state: bounds=0.45, intuition=0.90. Initiating high-level divide-and-conquer visual.",
    provider_metadata: { provider: "groq", latency_ms: 710, cached: true },
  },
  {
    step_id: "bs_step_1",
    step_index: 1,
    total_steps: 5,
    concept: "Binary Search",
    narration:
      "Now we calculate our first midpoint: mid = low + (high - low) // 2. Here, 0 + (9 - 0) // 2 = 4. Element at index 4 is 16. Our target is 23! Because 23 is greater than 16, every item from index 0 through index 4 is strictly less than 23. We safely discard the entire left half!",
    board_commands: [
      { type: "box", id: "box_0", label: "2", x: 60.0, y: 125.0, width: 55.0, height: 48.0, color: "#64748b", fill: "#0f172a" },
      { type: "box", id: "box_1", label: "5", x: 125.0, y: 125.0, width: 55.0, height: 48.0, color: "#64748b", fill: "#0f172a" },
      { type: "box", id: "box_2", label: "8", x: 190.0, y: 125.0, width: 55.0, height: 48.0, color: "#64748b", fill: "#0f172a" },
      { type: "box", id: "box_3", label: "12", x: 255.0, y: 125.0, width: 55.0, height: 48.0, color: "#64748b", fill: "#0f172a" },
      { type: "box", id: "box_4", label: "16", x: 320.0, y: 125.0, width: 55.0, height: 48.0, color: "#f59e0b", fill: "#451a03" },
      { type: "box", id: "box_5", label: "23", x: 385.0, y: 125.0, width: 55.0, height: 48.0, color: "#10b981", fill: "#064e3b" },
      { type: "box", id: "box_6", label: "38", x: 450.0, y: 125.0, width: 55.0, height: 48.0, color: "#3b82f6", fill: "#1e293b" },
      { type: "box", id: "box_7", label: "56", x: 515.0, y: 125.0, width: 55.0, height: 48.0, color: "#3b82f6", fill: "#1e293b" },
      { type: "box", id: "box_8", label: "72", x: 580.0, y: 125.0, width: 55.0, height: 48.0, color: "#3b82f6", fill: "#1e293b" },
      { type: "box", id: "box_9", label: "91", x: 645.0, y: 125.0, width: 55.0, height: 48.0, color: "#3b82f6", fill: "#1e293b" },
      {
        type: "arrow",
        id: "arr_mid",
        start_x: 347.0,
        start_y: 215.0,
        end_x: 347.0,
        end_y: 180.0,
        label: "mid = 4 (value: 16)",
        color: "#f59e0b",
      },
      {
        type: "equation",
        id: "eq_mid",
        latex: "mid = low + \\left\\lfloor \\frac{high - low}{2} \\right\\rfloor = 0 + 4 = 4",
        x: 60.0,
        y: 245.0,
        label: "Safe Overflow Midpoint Calculation",
      },
      {
        type: "text",
        id: "probe_text",
        content: "Target = 23. Since 23 > array[4] (16), discard indices [0 .. 4].",
        x: 60.0,
        y: 335.0,
        size: 15,
        color: "#38bdf8",
      },
    ],
    agent_thoughts:
      "Emphasizing safe midpoint calculation to prevent integer overflow.",
    provider_metadata: { provider: "gemini", latency_ms: 1250, cached: false },
  },
  {
    step_id: "bs_step_2",
    step_index: 2,
    total_steps: 5,
    concept: "Binary Search",
    narration:
      "Time for a quick check! When target 23 is greater than array[mid] 16, how should we update our pointers? Think carefully about which elements are already ruled out.",
    board_commands: [
      {
        type: "text",
        id: "checkpoint_banner",
        content: "Checkpoint: Bounds Pointer Update",
        x: 60.0,
        y: 60.0,
        size: 20,
        color: "#fbbf24",
      },
      {
        type: "equation",
        id: "eq_bounds",
        latex: "target > array[mid] \\implies \\text{Search space is } [mid + 1, high]",
        x: 60.0,
        y: 110.0,
        label: "Invariant Rule",
      },
    ],
    check_question: {
      question_id: "bs_check_bounds",
      question:
        "When target (23) is greater than array[mid] (16), what is the correct update?",
      options: [
        "high = mid - 1",
        "low = mid + 1",
        "low = mid",
        "high = mid",
      ],
      correct_index: 1,
      explanation:
        "Because array[mid] was already checked and is too small, we set low = mid + 1 to inspect only elements to its right.",
      concept_tag: "binary_search_bounds_update",
    },
    agent_thoughts:
      "Checking bounds update logic. Student previously had bounds misconception.",
    provider_metadata: { provider: "groq", latency_ms: 680, cached: true },
  },
  {
    step_id: "bs_step_3",
    step_index: 3,
    total_steps: 5,
    concept: "Binary Search",
    narration:
      "Let's inspect the clean Python implementation. Notice while low <= high: the less-than-or-equal condition is essential for 1-element arrays. And we use mid + 1 and mid - 1 to guarantee the loop terminates.",
    board_commands: [
      {
        type: "text",
        id: "code_banner",
        content: "Python Implementation & Invariants",
        x: 60.0,
        y: 50.0,
        size: 20,
        color: "#38bdf8",
      },
      {
        type: "equation",
        id: "eq_termination",
        latex: "high - low \\text{ strictly decreases each iteration } \\implies \\mathcal{O}(\\log n)",
        x: 60.0,
        y: 100.0,
        label: "Loop Termination Invariant",
      },
      {
        type: "mermaid",
        id: "complexity_tree",
        chart:
          "graph TD\n  N[Array of size N] --> N2a[N/2]\n  N --> N2b[N/2]\n  N2a --> N4a[N/4]\n  N2a --> N4b[N/4]\n  N2b --> N4c[N/4]\n  N2b --> N4d[N/4]",
        x: 60.0,
        y: 180.0,
        title: "Subproblem Halving Tree",
      },
    ],
    code_action: {
      code: `def binary_search(arr, target):\n    low = 0\n    high = len(arr) - 1\n    while low <= high:\n        mid = low + (high - low) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            low = mid + 1\n        else:\n            high = mid - 1\n    return -1\n\n# Test execution\nnums = [2, 5, 8, 12, 16, 23, 38, 56, 72, 91]\nidx = binary_search(nums, 23)\nprint(f"Target 23 found at index {idx}!")`,
      language: "python",
      action: "execute",
      explanation: "Full Python implementation executing in-browser via Pyodide.",
    },
    agent_thoughts:
      "Transitioning from visual whiteboard to concrete runnable code.",
    provider_metadata: { provider: "gemini", latency_ms: 1100, cached: false },
  },
  {
    step_id: "bs_step_4",
    step_index: 4,
    total_steps: 5,
    concept: "Binary Search",
    narration:
      "Fantastic job completing the Binary Search module! You've mastered pointer convergence, logarithmic halving, and overflow-safe midpoint calculation. Continue to the Live Coding runner or take the targeted assessment quiz to reinforce your mastery score!",
    board_commands: [
      { type: "clear", id: "clear_end" },
      {
        type: "text",
        id: "summary_title",
        content: "Module Complete: Binary Search Mastery Achieved!",
        x: 60.0,
        y: 50.0,
        size: 22,
        color: "#34d399",
      },
      {
        type: "box",
        id: "box_summary",
        label: "Mastery: 85%",
        x: 60.0,
        y: 110.0,
        width: 180.0,
        height: 60.0,
        color: "#10b981",
        fill: "#064e3b",
      },
      {
        type: "text",
        id: "next_recommendation",
        content: "Recommended Next Concept: 'Two Pointers & Sliding Window'",
        x: 60.0,
        y: 200.0,
        size: 16,
        color: "#38bdf8",
      },
      {
        type: "mermaid",
        id: "learning_path",
        chart:
          "graph LR\n  A[Binary Search (Mastered)] --> B[Two Pointers]\n  B --> C[Sliding Window]\n  C --> D[Binary Search on Answer]",
        x: 60.0,
        y: 250.0,
        title: "Recommended Learning Trajectory",
      },
    ],
    agent_thoughts:
      "Final step completed. Updating student mastery profile in learner model.",
    is_final_step: true,
    provider_metadata: { provider: "groq", latency_ms: 690, cached: true },
  },
];

export const ClassroomView: React.FC = () => {
  const [steps, setSteps] = useState<LessonStep[]>(FALLBACK_LESSON);
  const [currentStepIndex, setCurrentStepIndex] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [remediationCommands, setRemediationCommands] = useState<BoardCommand[]>([]);
  const [studentPersona, setStudentPersona] = useState<string>("demo_student");
  const [isBackendConnected, setIsBackendConnected] = useState<boolean>(false);
  const [isDontUnderstandLoading, setIsDontUnderstandLoading] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<"chat" | "checkpoint" | "code">("chat");

  const currentStep = steps[currentStepIndex] || FALLBACK_LESSON[0];

  // Try to load dynamic steps from backend on mount
  useEffect(() => {
    const fetchLesson = async () => {
      try {
        const res = await fetch("http://localhost:8000/mock/lesson");
        if (res.ok) {
          const data = await res.json();
          if (Array.isArray(data) && data.length > 0) {
            setSteps(data);
            setIsBackendConnected(true);
          }
        }
      } catch (e) {
        console.info("Using embedded lesson steps (offline mode).");
      }
    };
    fetchLesson();
  }, []);

  // Auto-switch to checkpoint tab if step has check_question
  useEffect(() => {
    if (currentStep.check_question) {
      setActiveTab("checkpoint");
    }
  }, [currentStepIndex, currentStep]);

  // Handle "I don't understand" adaptive trigger
  const handleDontUnderstand = async () => {
    setIsDontUnderstandLoading(true);
    try {
      const response = await fetch("http://localhost:8000/lesson/step", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          concept: currentStep.concept,
          student_id: studentPersona,
          step_index: currentStepIndex,
          feedback: "I do not understand",
        }),
      });

      if (response.ok) {
        const adaptedStep: LessonStep = await response.json();
        setSteps((prev) => {
          const updated = [...prev];
          updated[currentStepIndex] = adaptedStep;
          return updated;
        });
      } else {
        // Fallback adaptive explanation
        setSteps((prev) => {
          const updated = [...prev];
          updated[currentStepIndex] = {
            ...currentStep,
            narration: `Let's make this crystal clear: Imagine holding a 100-page book. If you're looking for page 75, and you flip to page 50, you instantly know page 75 cannot be in pages 1 to 50. You ignore that whole stack! That's all Binary Search is doing with arrays.`,
            agent_thoughts:
              "Student indicated confusion. Pivoted to simple real-world physical book analogy.",
            remediation: "Physical book analogy applied to clarify halving concept.",
          };
          return updated;
        });
      }
    } catch (e) {
      // Local fallback
      setSteps((prev) => {
        const updated = [...prev];
        updated[currentStepIndex] = {
          ...currentStep,
          narration: `Let's make this crystal clear: Think of the classic High-Low guessing game. When you guess 50 and the secret number is 75, you're told 'Too Low'. You never guess 1 through 50 again!`,
          agent_thoughts: "Offline adaptive analogy injected.",
          remediation: "High-low guessing game intuition provided.",
        };
        return updated;
      });
    } finally {
      setIsDontUnderstandLoading(false);
    }
  };

  const handleNextStep = () => {
    if (currentStepIndex < steps.length - 1) {
      setCurrentStepIndex((prev) => prev + 1);
      setRemediationCommands([]);
    }
  };

  const handlePrevStep = () => {
    if (currentStepIndex > 0) {
      setCurrentStepIndex((prev) => prev - 1);
      setRemediationCommands([]);
    }
  };

  const handleStepSelect = (index: number) => {
    setCurrentStepIndex(index);
    setRemediationCommands([]);
  };

  const handlePlayPause = () => {
    setIsPlaying((prev) => !prev);
  };

  const handleSpeechEnd = () => {
    if (isPlaying && currentStepIndex < steps.length - 1) {
      setTimeout(() => {
        setCurrentStepIndex((prev) => prev + 1);
      }, 1500);
    } else if (isPlaying && currentStepIndex >= steps.length - 1) {
      setIsPlaying(false);
    }
  };

  const handleAnswerSubmitted = (res: CheckAnswerResponse) => {
    if (res.suggested_board_commands && res.suggested_board_commands.length > 0) {
      setRemediationCommands(res.suggested_board_commands);
    }
  };

  const handleApplyChatCommands = (cmds: BoardCommand[]) => {
    setRemediationCommands(cmds);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans antialiased selection:bg-sky-500 selection:text-white">
      {/* Top Classroom Navigation Bar */}
      <header className="border-b border-slate-800 bg-slate-900/90 backdrop-blur sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-sky-500 to-indigo-600 flex items-center justify-center font-bold text-white shadow-lg shadow-sky-500/20">
              VT
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-sm font-semibold text-white">AI Virtual Teacher</h1>
                <span className="text-[11px] font-mono text-sky-400 bg-sky-950/80 px-2 py-0.5 rounded border border-sky-800/60">
                  {currentStep.concept}
                </span>
              </div>
              <p className="text-xs text-slate-400">Interactive Whiteboard & Live Classroom</p>
            </div>
          </div>

          {/* Right Status & Persona Selector */}
          <div className="flex items-center space-x-3">
            <div className="hidden sm:flex items-center bg-slate-800/80 rounded-lg p-1 border border-slate-700/60 text-xs">
              <span className="px-2 py-0.5 text-slate-400">Student:</span>
              <select
                value={studentPersona}
                onChange={(e) => setStudentPersona(e.target.value)}
                className="bg-slate-900 text-sky-400 font-semibold rounded px-2 py-0.5 border border-slate-700 focus:outline-none focus:border-sky-500 text-xs"
              >
                <option value="demo_student">Alex Chen (Demo Student)</option>
                <option value="novice_learner">Maya Patel (Novice Learner)</option>
              </select>
            </div>

            <span
              className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium border ${
                isBackendConnected
                  ? "bg-emerald-950/80 text-emerald-400 border-emerald-800/60"
                  : "bg-sky-950/80 text-sky-400 border-sky-800/60"
              }`}
            >
              <span
                className={`w-1.5 h-1.5 mr-1.5 rounded-full ${
                  isBackendConnected ? "bg-emerald-400" : "bg-sky-400"
                } animate-pulse`}
              />
              {isBackendConnected ? "Live Backend" : "Standby Mode"}
            </span>
          </div>
        </div>
      </header>

      {/* Main Classroom Workspace */}
      <main className="max-w-7xl mx-auto px-4 py-6 flex-1 w-full grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column (Whiteboard Canvas & Core Controls) - 8 Cols */}
        <div className="lg:col-span-8 flex flex-col space-y-4">
          {/* Digital Whiteboard Canvas */}
          <WhiteboardCanvas
            commands={currentStep.board_commands}
            remediationCommands={remediationCommands}
            stepIndex={currentStepIndex}
          />

          {/* Controls Bar (Play/Pause, Stepper, 'I don't understand') */}
          <ControlsBar
            currentStep={currentStepIndex}
            totalSteps={steps.length}
            isPlaying={isPlaying}
            onPlayPause={handlePlayPause}
            onNext={handleNextStep}
            onPrev={handlePrevStep}
            onStepSelect={handleStepSelect}
            onDontUnderstand={handleDontUnderstand}
            isDontUnderstandLoading={isDontUnderstandLoading}
          />

          {/* Teacher Spoken Narration Panel */}
          <NarrationPanel
            narration={currentStep.narration}
            stepIndex={currentStepIndex}
            concept={currentStep.concept}
            onSpeechEnd={handleSpeechEnd}
          />

          {/* Agent Cognitive Reasoning & Misconception Banner */}
          <AgentThoughtsBanner
            agentThoughts={currentStep.agent_thoughts}
            detectedMisconception={currentStep.detected_misconception}
            remediation={currentStep.remediation}
            providerMetadata={currentStep.provider_metadata}
          />
        </div>

        {/* Right Column (Sidebar: Chat / Checkpoint / Code Action) - 4 Cols */}
        <div className="lg:col-span-4 flex flex-col space-y-4">
          {/* Tab Selector */}
          <div className="flex bg-slate-900 p-1 rounded-xl border border-slate-800 text-xs">
            <button
              onClick={() => setActiveTab("chat")}
              className={`flex-1 py-1.5 rounded-lg font-medium transition ${
                activeTab === "chat"
                  ? "bg-sky-500 text-white shadow-md shadow-sky-500/20"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Teacher Chat
            </button>
            <button
              onClick={() => setActiveTab("checkpoint")}
              className={`flex-1 py-1.5 rounded-lg font-medium transition relative ${
                activeTab === "checkpoint"
                  ? "bg-sky-500 text-white shadow-md shadow-sky-500/20"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Checkpoint
              {currentStep.check_question && (
                <span className="w-2 h-2 rounded-full bg-amber-400 absolute top-1.5 right-2 animate-ping" />
              )}
            </button>
            {currentStep.code_action && (
              <button
                onClick={() => setActiveTab("code")}
                className={`flex-1 py-1.5 rounded-lg font-medium transition ${
                  activeTab === "code"
                    ? "bg-sky-500 text-white shadow-md shadow-sky-500/20"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                Code
              </button>
            )}
          </div>

          {/* Tab 1: Live Teacher Chat */}
          {activeTab === "chat" && (
            <TeacherChat
              concept={currentStep.concept}
              currentStepIndex={currentStepIndex}
              studentId={studentPersona}
              onApplyBoardCommands={handleApplyChatCommands}
            />
          )}

          {/* Tab 2: Formative Checkpoint Card */}
          {activeTab === "checkpoint" && (
            <div>
              {currentStep.check_question ? (
                <CheckQuestionCard
                  question={currentStep.check_question}
                  concept={currentStep.concept}
                  studentId={studentPersona}
                  onAnswerSubmitted={handleAnswerSubmitted}
                />
              ) : (
                <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 text-center text-slate-400 text-xs space-y-2">
                  <div className="w-10 h-10 rounded-xl bg-slate-800 flex items-center justify-center mx-auto text-slate-500">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                  </div>
                  <p className="font-semibold text-slate-300">No Checkpoint on this Step</p>
                  <p className="text-[11px] text-slate-500">
                    Advance to Step 3 to test your intuition on bounds pointer updates!
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Tab 3: Code Action Preview */}
          {activeTab === "code" && currentStep.code_action && (
            <div className="bg-slate-900/95 border border-slate-800 rounded-2xl p-4 shadow-xl flex flex-col space-y-3">
              <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                <div className="flex items-center space-x-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
                  <h4 className="text-xs font-semibold text-slate-200">Live Code Snippet</h4>
                </div>
                <span className="text-[10px] font-mono text-sky-400 bg-sky-950/80 px-2 py-0.5 rounded border border-sky-800/60">
                  {currentStep.code_action.language || "python"}
                </span>
              </div>
              <pre className="bg-slate-950 p-3 rounded-xl border border-slate-800/80 font-mono text-xs text-sky-300 overflow-x-auto leading-relaxed max-h-[360px]">
                {currentStep.code_action.code}
              </pre>
              {currentStep.code_action.explanation && (
                <p className="text-[11px] text-slate-400 leading-relaxed">
                  {currentStep.code_action.explanation}
                </p>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  );
};
