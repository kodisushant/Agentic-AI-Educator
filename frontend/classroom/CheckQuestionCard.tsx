import React, { useState } from "react";
import { CheckQuestion, CheckAnswerResponse, BoardCommand } from "./types";

interface CheckQuestionCardProps {
  question: CheckQuestion;
  concept: string;
  studentId?: string;
  onAnswerSubmitted?: (result: CheckAnswerResponse) => void;
  className?: string;
}

export const CheckQuestionCard: React.FC<CheckQuestionCardProps> = ({
  question,
  concept,
  studentId = "demo_student",
  onAnswerSubmitted,
  className = "",
}) => {
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [result, setResult] = useState<CheckAnswerResponse | null>(null);

  const handleSubmit = async () => {
    if (selectedIndex === null || isSubmitting) return;

    setIsSubmitting(true);
    try {
      const response = await fetch("http://localhost:8000/lesson/check-answer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question_id: question.question_id,
          selected_index: selectedIndex,
          concept,
          student_id: studentId,
        }),
      });

      let data: CheckAnswerResponse;
      if (response.ok) {
        data = await response.json();
      } else {
        // Fallback local evaluation matching contracts
        const isCorrect = selectedIndex === question.correct_index;
        data = {
          is_correct: isCorrect,
          correct_index: question.correct_index,
          explanation: question.explanation,
          detected_misconception: isCorrect
            ? null
            : selectedIndex === 0
            ? "confuses_direction_when_target_greater"
            : "fails_to_exclude_checked_midpoint",
          remediation: isCorrect
            ? "Great understanding!"
            : `You selected option ${selectedIndex}. When target > array[mid], the target is in the right half, so low must advance to mid + 1.`,
          updated_mastery_score: isCorrect ? 0.8 : 0.45,
          suggested_board_commands: isCorrect
            ? []
            : [
                {
                  type: "text",
                  id: "misconception_alert",
                  content: "Diagnosed Misconception: Search direction confusion",
                  x: 60.0,
                  y: 350.0,
                  size: 16,
                  color: "#dc2626",
                },
              ],
        };
      }

      setResult(data);
      onAnswerSubmitted?.(data);
    } catch (err) {
      console.warn("Check answer submission failed, using offline evaluator:", err);
      const isCorrect = selectedIndex === question.correct_index;
      const data: CheckAnswerResponse = {
        is_correct: isCorrect,
        correct_index: question.correct_index,
        explanation: question.explanation,
        detected_misconception: isCorrect ? null : "confuses_direction_when_target_greater",
        remediation: isCorrect
          ? "Spot on! Advancing low preserves the invariant."
          : "Notice that because array[mid] is smaller than our target, the answer can only be to the right of mid.",
        updated_mastery_score: isCorrect ? 0.75 : 0.4,
      };
      setResult(data);
      onAnswerSubmitted?.(data);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReset = () => {
    setSelectedIndex(null);
    setResult(null);
  };

  return (
    <div
      className={`bg-slate-900/95 border border-indigo-500/30 rounded-2xl p-5 shadow-2xl backdrop-blur transition-all duration-300 ${className}`}
    >
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-4">
        <div className="flex items-center space-x-2">
          <span className="w-2.5 h-2.5 rounded-full bg-amber-400 animate-pulse" />
          <h3 className="text-sm font-semibold text-slate-100">Understanding Checkpoint</h3>
        </div>
        <span className="text-[11px] font-mono text-indigo-400 bg-indigo-950/80 px-2 py-0.5 rounded border border-indigo-800/60">
          {question.concept_tag}
        </span>
      </div>

      {/* Question Prompt */}
      <p className="text-sm font-medium text-slate-100 mb-4 leading-relaxed">
        {question.question}
      </p>

      {/* Options List */}
      <div className="space-y-2 mb-4">
        {question.options.map((option, idx) => {
          const isSelected = selectedIndex === idx;
          const isCorrect = result && idx === result.correct_index;
          const isIncorrectSelection = result && isSelected && !result.is_correct;

          let optionStyle =
            "bg-slate-800/80 border-slate-700/80 text-slate-200 hover:bg-slate-800 hover:border-slate-600";

          if (result) {
            if (isCorrect) {
              optionStyle = "bg-emerald-950/80 border-emerald-600 text-emerald-200";
            } else if (isIncorrectSelection) {
              optionStyle = "bg-rose-950/80 border-rose-600 text-rose-200";
            } else {
              optionStyle = "bg-slate-850/60 border-slate-800 text-slate-400 opacity-60";
            }
          } else if (isSelected) {
            optionStyle = "bg-sky-950/80 border-sky-500 text-sky-100 ring-2 ring-sky-500/30";
          }

          return (
            <div
              key={idx}
              onClick={() => !result && setSelectedIndex(idx)}
              className={`p-3 rounded-xl border text-xs font-mono flex items-center justify-between cursor-pointer transition-all ${optionStyle}`}
            >
              <div className="flex items-center space-x-3">
                <span className="w-5 h-5 rounded-md bg-slate-900/80 border border-slate-700 flex items-center justify-center font-bold text-[10px] text-slate-400">
                  {String.fromCharCode(65 + idx)}
                </span>
                <span>{option}</span>
              </div>

              {result && isCorrect && (
                <span className="text-emerald-400 text-xs font-sans font-semibold flex items-center gap-1">
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                      clipRule="evenodd"
                    />
                  </svg>
                  Correct
                </span>
              )}

              {result && isIncorrectSelection && (
                <span className="text-rose-400 text-xs font-sans font-semibold flex items-center gap-1">
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                      clipRule="evenodd"
                    />
                  </svg>
                  Incorrect
                </span>
              )}
            </div>
          );
        })}
      </div>

      {/* Action / Result Feedback */}
      {!result ? (
        <button
          onClick={handleSubmit}
          disabled={selectedIndex === null || isSubmitting}
          className="w-full py-2.5 bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 disabled:opacity-40 text-white font-medium text-xs rounded-xl shadow-lg shadow-sky-500/20 transition flex items-center justify-center gap-2"
        >
          {isSubmitting ? (
            <>
              <svg className="animate-spin w-3.5 h-3.5 text-white" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              Diagnosing answer...
            </>
          ) : (
            "Check My Answer"
          )}
        </button>
      ) : (
        <div className="space-y-3 pt-2">
          {/* Explanation Alert */}
          <div
            className={`p-3 rounded-xl border text-xs leading-relaxed ${
              result.is_correct
                ? "bg-emerald-950/60 border-emerald-800/80 text-emerald-200"
                : "bg-rose-950/60 border-rose-800/80 text-rose-200"
            }`}
          >
            <div className="font-semibold mb-1 flex items-center justify-between">
              <span>{result.is_correct ? "✓ Well Done!" : "⚠️ Pedagogical Correction:"}</span>
              <span className="font-mono text-[10px] bg-slate-900/80 px-2 py-0.5 rounded">
                Mastery: {Math.round(result.updated_mastery_score * 100)}%
              </span>
            </div>
            <p>{result.remediation || result.explanation}</p>
          </div>

          <button
            onClick={handleReset}
            className="w-full py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium rounded-xl border border-slate-700 transition"
          >
            Try Again
          </button>
        </div>
      )}
    </div>
  );
};
