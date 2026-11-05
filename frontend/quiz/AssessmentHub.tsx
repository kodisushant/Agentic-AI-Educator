"use client";

import React, { useState, useEffect } from "react";
import { QuizView } from "./QuizView";
import { FlashcardDeck } from "./FlashcardDeck";
import { QuizGenerateResponse, FlashcardsGenerateResponse } from "./types";

interface AssessmentHubProps {
  apiBaseUrl?: string;
  studentId?: string;
  defaultTopic?: string;
}

export const AssessmentHub: React.FC<AssessmentHubProps> = ({
  apiBaseUrl = "http://localhost:8000",
  studentId = "demo_student",
  defaultTopic = "Binary Search",
}) => {
  const [activeTab, setActiveTab] = useState<"quiz" | "flashcards">("quiz");
  const [selectedTopic, setSelectedTopic] = useState<string>(defaultTopic);
  const [weakConcepts, setWeakConcepts] = useState<string[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const [quizData, setQuizData] = useState<QuizGenerateResponse | null>(null);
  const [flashcardData, setFlashcardData] = useState<FlashcardsGenerateResponse | null>(null);

  // 1. Fetch weak concepts from Person 4's Learner Model contract (/learner/weak/{user_id})
  useEffect(() => {
    async function fetchWeakConcepts() {
      try {
        const res = await fetch(`${apiBaseUrl}/learner/weak/${studentId}`);
        if (res.ok) {
          const data = await res.json();
          if (data?.weak_concepts && Array.isArray(data.weak_concepts)) {
            const tags = data.weak_concepts
              .map((w: { concept_tag?: string }) => w.concept_tag || "")
              .filter(Boolean);
            setWeakConcepts(tags);
          }
        }
      } catch (err) {
        // Fallback default weak concept
        setWeakConcepts(["binary_search_bounds_update"]);
      }
    }
    fetchWeakConcepts();
  }, [apiBaseUrl, studentId]);

  // 2. Fetch Quiz
  const loadQuiz = async (topic: string, weak: string[]) => {
    setLoading(true);
    setErrorMessage(null);
    try {
      const res = await fetch(`${apiBaseUrl}/assess/quiz`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          topic,
          num_questions: 4,
          weak_concepts: weak,
          student_id: studentId,
        }),
      });
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      const data = await res.json();
      setQuizData(data);
    } catch (err: unknown) {
      const errMsg = err instanceof Error ? err.message : String(err);
      console.warn("Using offline fallback quiz data:", errMsg);
      setQuizData({
        quiz_id: "quiz_bs_fallback",
        topic,
        questions: [
          {
            question_id: "q_bs_1",
            concept_tag: "binary_search_precondition",
            question: "What is the mandatory prerequisite before applying Binary Search on a collection?",
            options: [
              "The elements must be sorted",
              "The elements must all be unique",
              "The list length must be a power of two",
              "The array must fit in cache",
            ],
            correct_index: 0,
            explanation: "Binary search relies on order to discard halves. Without sorting, half-elimination is invalid.",
          },
          {
            question_id: "q_bs_2",
            concept_tag: "binary_search_bounds_update",
            question: "If array[mid] < target in an ascending search, how are pointers updated?",
            options: [
              "high = mid - 1",
              "low = mid + 1",
              "low = mid",
              "high = mid",
            ],
            correct_index: 1,
            explanation: "Since the target is strictly larger than array[mid], we eliminate the left half up to mid.",
          },
          {
            question_id: "q_bs_3",
            concept_tag: "binary_search_complexity",
            question: "What is the worst-case time complexity of Binary Search on an array of size n?",
            options: ["O(1)", "O(log n)", "O(n)", "O(n log n)"],
            correct_index: 1,
            explanation: "Halving search space at each step takes log2(n) operations.",
          },
        ],
      });
    } finally {
      setLoading(false);
    }
  };

  // 3. Fetch Flashcards
  const loadFlashcards = async (topic: string, weak: string[]) => {
    setLoading(true);
    setErrorMessage(null);
    try {
      const res = await fetch(`${apiBaseUrl}/assess/flashcards`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          topic,
          count: 4,
          weak_concepts: weak,
          student_id: studentId,
        }),
      });
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      const data = await res.json();
      setFlashcardData(data);
    } catch (err: unknown) {
      const errMsg = err instanceof Error ? err.message : String(err);
      console.warn("Using offline fallback flashcards data:", errMsg);
      setFlashcardData({
        topic,
        cards: [
          {
            card_id: "fc_1",
            concept_tag: "binary_search_complexity",
            front: "What is the time complexity of Binary Search?",
            back: "O(log n) worst/average case, O(1) best case. Auxiliary space is O(1) for iterative.",
            hint: "Halves search space each step.",
          },
          {
            card_id: "fc_2",
            concept_tag: "binary_search_bounds_update",
            front: "When target < array[mid], which pointer moves?",
            back: "high = mid - 1",
            hint: "Search the lower half.",
          },
          {
            card_id: "fc_3",
            concept_tag: "binary_search_termination",
            front: "What is the loop termination condition for standard iterative Binary Search?",
            back: "while low <= high:",
            hint: "Check even when low == high.",
          },
        ],
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadQuiz(selectedTopic, weakConcepts);
    loadFlashcards(selectedTopic, weakConcepts);
  }, [selectedTopic]);

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "20px",
        fontFamily: "system-ui, -apple-system, sans-serif",
      }}
    >
      {/* Assessment Hub Top Bar */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "16px 20px",
          backgroundColor: "#f8fafc",
          borderRadius: "10px",
          border: "1px solid #e2e8f0",
        }}
      >
        <div style={{ display: "flex", gap: "10px" }}>
          <button
            onClick={() => setActiveTab("quiz")}
            style={{
              padding: "8px 16px",
              fontSize: "14px",
              fontWeight: 600,
              borderRadius: "6px",
              border: "none",
              backgroundColor: activeTab === "quiz" ? "#0284c7" : "#e2e8f0",
              color: activeTab === "quiz" ? "#ffffff" : "#475569",
              cursor: "pointer",
            }}
          >
            📝 Topic Quiz
          </button>

          <button
            onClick={() => setActiveTab("flashcards")}
            style={{
              padding: "8px 16px",
              fontSize: "14px",
              fontWeight: 600,
              borderRadius: "6px",
              border: "none",
              backgroundColor: activeTab === "flashcards" ? "#0284c7" : "#e2e8f0",
              color: activeTab === "flashcards" ? "#ffffff" : "#475569",
              cursor: "pointer",
            }}
          >
            🗂️ Flashcards Deck
          </button>
        </div>

        {/* Weak Concept Pill */}
        {weakConcepts.length > 0 && (
          <div style={{ fontSize: "12px", color: "#64748b" }}>
            Targeting weak concept:{" "}
            <span
              style={{
                backgroundColor: "#fee2e2",
                color: "#991b1b",
                padding: "3px 8px",
                borderRadius: "12px",
                fontWeight: 600,
              }}
            >
              ⚠️ {weakConcepts[0]}
            </span>
          </div>
        )}
      </div>

      {/* Main Content Area */}
      {loading ? (
        <div style={{ padding: "40px", textAlign: "center", color: "#64748b" }}>
          Generating assessment content tailored to your learning pace...
        </div>
      ) : activeTab === "quiz" && quizData ? (
        <QuizView
          quiz={quizData}
          apiBaseUrl={apiBaseUrl}
          studentId={studentId}
          onRestart={() => loadQuiz(selectedTopic, weakConcepts)}
        />
      ) : activeTab === "flashcards" && flashcardData ? (
        <FlashcardDeck
          cards={flashcardData.cards}
          topic={flashcardData.topic}
          onDeckComplete={() => setActiveTab("quiz")}
        />
      ) : (
        <div style={{ padding: "20px", textAlign: "center", color: "#94a3b8" }}>
          No assessment content currently available.
        </div>
      )}
    </div>
  );
};

