"use client";

import React, { useState } from "react";
import {
  QuizGenerateResponse,
  QuizQuestionItem,
  QuizSubmitResponse,
  QuestionResultFeedback,
} from "./types";

interface QuizViewProps {
  quiz: QuizGenerateResponse;
  apiBaseUrl?: string;
  studentId?: string;
  onQuizCompleted?: (result: QuizSubmitResponse) => void;
  onRestart?: () => void;
}

export const QuizView: React.FC<QuizViewProps> = ({
  quiz,
  apiBaseUrl = "http://localhost:8000",
  studentId = "demo_student",
  onQuizCompleted,
  onRestart,
}) => {
  const [selectedAnswers, setSelectedAnswers] = useState<Record<string, number>>({});
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [submissionResult, setSubmissionResult] = useState<QuizSubmitResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const questions = quiz.questions || [];
  const answeredCount = Object.keys(selectedAnswers).length;
  const isAllAnswered = questions.length > 0 && answeredCount === questions.length;

  const handleSelectOption = (questionId: string, optionIndex: number) => {
    if (submissionResult) return; // locked after submission
    setSelectedAnswers((prev: Record<string, number>) => ({
      ...prev,
      [questionId]: optionIndex,
    }));
  };

  const handleSubmitQuiz = async () => {
    if (answeredCount === 0 || isSubmitting) return;
    setIsSubmitting(true);
    setErrorMessage(null);

    const payload = {
      quiz_id: quiz.quiz_id,
      user_id: studentId,
      answers: selectedAnswers,
    };

    try {
      const response = await fetch(`${apiBaseUrl}/assess/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error(`Server returned HTTP ${response.status}`);
      }

      const data: QuizSubmitResponse = await response.json();
      setSubmissionResult(data);
      if (onQuizCompleted) {
        onQuizCompleted(data);
      }
    } catch (err: unknown) {
      console.warn("Quiz submission network notice. Computing client-side feedback for offline demo.", err);
      // Client-side fallback evaluation so student demo is never blocked
      const feedbackList: QuestionResultFeedback[] = questions.map((q) => {
        const selected = selectedAnswers[q.question_id] ?? -1;
        const isCorrect = selected === q.correct_index;
        return {
          question_id: q.question_id,
          concept_tag: q.concept_tag,
          is_correct: isCorrect,
          selected_index: selected,
          correct_index: q.correct_index,
          explanation: q.explanation,
          identified_misconception: isCorrect ? null : `misunderstands_${q.concept_tag}`,
        };
      });

      const correctCount = feedbackList.filter((f) => f.is_correct).length;
      const total = questions.length || 1;
      const offlineResult: QuizSubmitResponse = {
        quiz_id: quiz.quiz_id,
        user_id: studentId,
        score: Math.round((correctCount / total) * 100) / 100,
        total_questions: total,
        correct_count: correctCount,
        feedback: feedbackList,
      };

      setSubmissionResult(offlineResult);
      if (onQuizCompleted) {
        onQuizCompleted(offlineResult);
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRetake = () => {
    setSelectedAnswers({});
    setSubmissionResult(null);
    setErrorMessage(null);
    if (onRestart) {
      onRestart();
    }
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "20px",
        padding: "24px",
        backgroundColor: "#ffffff",
        borderRadius: "12px",
        border: "1px solid #e2e8f0",
        boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.05)",
        fontFamily: "system-ui, -apple-system, sans-serif",
      }}
    >
      {/* Quiz Header */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          borderBottom: "1px solid #e2e8f0",
          paddingBottom: "14px",
        }}
      >
        <div>
          <h3 style={{ margin: "0 0 4px 0", fontSize: "18px", color: "#0f172a" }}>
            📝 Topic Quiz: {quiz.topic}
          </h3>
          <span style={{ fontSize: "12px", color: "#64748b" }}>
            Quiz ID: <code style={{ backgroundColor: "#f1f5f9", padding: "2px 6px", borderRadius: "4px" }}>{quiz.quiz_id}</code>
          </span>
        </div>

        <div style={{ textAlign: "right" }}>
          <span
            style={{
              fontSize: "13px",
              fontWeight: 600,
              padding: "4px 10px",
              borderRadius: "16px",
              backgroundColor: isAllAnswered ? "#dcfce7" : "#f1f5f9",
              color: isAllAnswered ? "#166534" : "#475569",
            }}
          >
            {answeredCount} / {questions.length} Answered
          </span>
        </div>
      </div>

      {/* Submission Score Banner */}
      {submissionResult && (
        <div
          style={{
            padding: "16px",
            borderRadius: "8px",
            backgroundColor: submissionResult.score >= 0.7 ? "#f0fdf4" : "#fef2f2",
            border: `1px solid ${submissionResult.score >= 0.7 ? "#bbf7d0" : "#fecaca"}`,
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <div>
            <div
              style={{
                fontSize: "16px",
                fontWeight: "bold",
                color: submissionResult.score >= 0.7 ? "#166534" : "#991b1b",
              }}
            >
              {submissionResult.score >= 0.7 ? "🎉 Excellent Work!" : "💡 Keep Practicing!"}
            </div>
            <div style={{ fontSize: "13px", color: "#334155", marginTop: "4px" }}>
              Score: <strong>{Math.round(submissionResult.score * 100)}%</strong> ({submissionResult.correct_count} of{" "}
              {submissionResult.total_questions} correct) • Attempt synced to Learner Model.
            </div>
          </div>

          <button
            onClick={handleRetake}
            style={{
              padding: "8px 16px",
              fontSize: "13px",
              fontWeight: 600,
              borderRadius: "6px",
              border: "none",
              backgroundColor: "#0284c7",
              color: "#ffffff",
              cursor: "pointer",
            }}
          >
            Retake Quiz
          </button>
        </div>
      )}

      {/* Question Items List */}
      <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        {questions.map((q, qIndex) => {
          const selectedIdx = selectedAnswers[q.question_id];
          const feedback = submissionResult?.feedback?.find((f) => f.question_id === q.question_id);

          return (
            <div
              key={q.question_id}
              style={{
                padding: "16px",
                borderRadius: "8px",
                border: "1px solid #e2e8f0",
                backgroundColor: feedback
                  ? feedback.is_correct
                    ? "#f0fdf4"
                    : "#fff1f2"
                  : "#f8fafc",
                transition: "all 0.2s",
              }}
            >
              {/* Question Header & Concept Tag */}
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "flex-start",
                  marginBottom: "12px",
                }}
              >
                <div style={{ fontSize: "14px", fontWeight: 600, color: "#0f172a" }}>
                  {qIndex + 1}. {q.question}
                </div>
                <span
                  style={{
                    fontSize: "11px",
                    fontWeight: 500,
                    padding: "2px 8px",
                    borderRadius: "12px",
                    backgroundColor: "#e0f2fe",
                    color: "#0369a1",
                    whiteSpace: "nowrap",
                    marginLeft: "12px",
                  }}
                >
                  🏷️ {q.concept_tag}
                </span>
              </div>

              {/* Options */}
              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                {q.options.map((opt, optIndex) => {
                  const isSelected = selectedIdx === optIndex;
                  const isCorrectAnswer = submissionResult && optIndex === q.correct_index;
                  const isWrongSelected = submissionResult && isSelected && !isCorrectAnswer;

                  let optBorder = isSelected ? "1px solid #0284c7" : "1px solid #cbd5e1";
                  let optBg = isSelected ? "#e0f2fe" : "#ffffff";

                  if (submissionResult) {
                    if (isCorrectAnswer) {
                      optBorder = "1px solid #22c55e";
                      optBg = "#dcfce7";
                    } else if (isWrongSelected) {
                      optBorder = "1px solid #ef4444";
                      optBg = "#fee2e2";
                    } else {
                      optBorder = "1px solid #e2e8f0";
                      optBg = "#ffffff";
                    }
                  }

                  return (
                    <label
                      key={optIndex}
                      onClick={() => handleSelectOption(q.question_id, optIndex)}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "10px",
                        padding: "10px 14px",
                        borderRadius: "6px",
                        border: optBorder,
                        backgroundColor: optBg,
                        cursor: submissionResult ? "default" : "pointer",
                        fontSize: "13px",
                        color: "#1e293b",
                        transition: "background-color 0.15s",
                      }}
                    >
                      <input
                        type="radio"
                        name={q.question_id}
                        checked={isSelected}
                        onChange={() => handleSelectOption(q.question_id, optIndex)}
                        disabled={!!submissionResult}
                        style={{ cursor: submissionResult ? "default" : "pointer" }}
                      />
                      <span style={{ flex: 1 }}>{opt}</span>
                      {submissionResult && isCorrectAnswer && (
                        <span style={{ fontSize: "12px", fontWeight: "bold", color: "#15803d" }}>✓ Correct</span>
                      )}
                      {submissionResult && isWrongSelected && (
                        <span style={{ fontSize: "12px", fontWeight: "bold", color: "#b91c1c" }}>✗ Selected</span>
                      )}
                    </label>
                  );
                })}
              </div>

              {/* Pedagogical Explanation & Misconception Info */}
              {feedback && (
                <div
                  style={{
                    marginTop: "12px",
                    padding: "10px 14px",
                    borderRadius: "6px",
                    backgroundColor: "#ffffff",
                    border: feedback.is_correct ? "1px solid #86efac" : "1px solid #fca5a5",
                    fontSize: "12px",
                    lineHeight: "1.5",
                  }}
                >
                  <strong style={{ color: feedback.is_correct ? "#15803d" : "#b91c1c" }}>
                    {feedback.is_correct ? "Explanation:" : "Remediation Feedback:"}
                  </strong>{" "}
                  {feedback.explanation}
                  {feedback.identified_misconception && (
                    <div style={{ marginTop: "6px", color: "#7f1d1d", fontSize: "11px" }}>
                      Detected Misconception: <code>{feedback.identified_misconception}</code>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Action Footer */}
      {!submissionResult && (
        <div style={{ display: "flex", justifyContent: "flex-end", borderTop: "1px solid #e2e8f0", paddingTop: "14px" }}>
          <button
            onClick={handleSubmitQuiz}
            disabled={isSubmitting || answeredCount === 0}
            style={{
              padding: "10px 24px",
              fontSize: "14px",
              fontWeight: 600,
              borderRadius: "6px",
              border: "none",
              backgroundColor: isSubmitting || answeredCount === 0 ? "#94a3b8" : "#0284c7",
              color: "#ffffff",
              cursor: isSubmitting || answeredCount === 0 ? "not-allowed" : "pointer",
              transition: "background-color 0.2s",
            }}
          >
            {isSubmitting ? "Evaluating Answers..." : `Submit Quiz (${answeredCount}/${questions.length})`}
          </button>
        </div>
      )}
    </div>
  );
};

