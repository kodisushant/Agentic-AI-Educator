"use client";

import React, { useState } from "react";
import { FlashcardItem } from "./types";

interface FlashcardDeckProps {
  cards: FlashcardItem[];
  topic: string;
  onRateCard?: (cardId: string, rating: "mastered" | "review") => void;
  onDeckComplete?: () => void;
}

export const FlashcardDeck: React.FC<FlashcardDeckProps> = ({
  cards,
  topic,
  onRateCard,
  onDeckComplete,
}) => {
  const [currentIndex, setCurrentIndex] = useState<number>(0);
  const [isFlipped, setIsFlipped] = useState<boolean>(false);
  const [showHint, setShowHint] = useState<boolean>(false);
  const [reviewedCards, setReviewedCards] = useState<Record<string, "mastered" | "review">>({});

  if (!cards || cards.length === 0) {
    return (
      <div
        style={{
          padding: "32px",
          textAlign: "center",
          backgroundColor: "#f8fafc",
          borderRadius: "12px",
          border: "1px dashed #cbd5e1",
          color: "#64748b",
        }}
      >
        No flashcards available for this topic.
      </div>
    );
  }

  const currentCard = cards[currentIndex];
  if (!currentCard) {
    return null;
  }
  const progressPercent = Math.round(((currentIndex + 1) / cards.length) * 100);

  const handleFlip = () => {
    setIsFlipped((prev: boolean) => !prev);
  };

  const handleNext = () => {
    if (currentIndex < cards.length - 1) {
      setCurrentIndex((prev: number) => prev + 1);
      setIsFlipped(false);
      setShowHint(false);
    } else if (onDeckComplete) {
      onDeckComplete();
    }
  };

  const handlePrev = () => {
    if (currentIndex > 0) {
      setCurrentIndex((prev: number) => prev - 1);
      setIsFlipped(false);
      setShowHint(false);
    }
  };

  const handleRate = (rating: "mastered" | "review") => {
    setReviewedCards((prev: Record<string, "mastered" | "review">) => ({ ...prev, [currentCard.card_id]: rating }));
    if (onRateCard) {
      onRateCard(currentCard.card_id, rating);
    }
    handleNext();
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: "16px",
        fontFamily: "system-ui, -apple-system, sans-serif",
        maxWidth: "600px",
        margin: "0 auto",
      }}
    >
      {/* Header and Progress */}
      <div style={{ width: "100%", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h3 style={{ margin: "0 0 4px 0", fontSize: "18px", color: "#0f172a" }}>
            🗂️ Flashcards: {topic}
          </h3>
          <span style={{ fontSize: "12px", color: "#64748b" }}>
            Card {currentIndex + 1} of {cards.length}
          </span>
        </div>
        <span
          style={{
            fontSize: "12px",
            fontWeight: 600,
            padding: "3px 8px",
            borderRadius: "12px",
            backgroundColor: "#e0f2fe",
            color: "#0369a1",
          }}
        >
          🏷️ {currentCard.concept_tag}
        </span>
      </div>

      {/* Progress Bar */}
      <div
        style={{
          width: "100%",
          height: "6px",
          backgroundColor: "#e2e8f0",
          borderRadius: "3px",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            width: `${progressPercent}%`,
            height: "100%",
            backgroundColor: "#0284c7",
            transition: "width 0.3s ease",
          }}
        />
      </div>

      {/* Interactive 3D Flip Card Container */}
      <div
        onClick={handleFlip}
        style={{
          width: "100%",
          minHeight: "260px",
          perspective: "1000px",
          cursor: "pointer",
        }}
      >
        <div
          style={{
            width: "100%",
            minHeight: "260px",
            position: "relative",
            textAlign: "center",
            transition: "transform 0.6s cubic-bezier(0.4, 0, 0.2, 1)",
            transformStyle: "preserve-3d",
            transform: isFlipped ? "rotateY(180deg)" : "rotateY(0deg)",
            borderRadius: "16px",
            boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)",
          }}
        >
          {/* Card Front */}
          <div
            style={{
              position: "absolute",
              width: "100%",
              height: "100%",
              backfaceVisibility: "hidden",
              borderRadius: "16px",
              backgroundColor: "#ffffff",
              border: "1px solid #cbd5e1",
              padding: "32px 24px",
              boxSizing: "border-box",
              display: "flex",
              flexDirection: "column",
              justifyContent: "space-between",
            }}
          >
            <div style={{ fontSize: "11px", fontWeight: "bold", color: "#64748b", textTransform: "uppercase" }}>
              Question / Prompt (Click to flip)
            </div>

            <div style={{ fontSize: "18px", fontWeight: 600, color: "#0f172a", lineHeight: "1.5" }}>
              {currentCard.front}
            </div>

            <div style={{ display: "flex", justifyContent: "center" }}>
              {currentCard.hint && (
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    setShowHint((prev: boolean) => !prev);
                  }}
                  style={{
                    background: "none",
                    border: "1px dashed #94a3b8",
                    padding: "4px 10px",
                    borderRadius: "12px",
                    fontSize: "11px",
                    color: "#475569",
                    cursor: "pointer",
                  }}
                >
                  {showHint ? `💡 Hint: ${currentCard.hint}` : "💡 Need a hint?"}
                </button>
              )}
            </div>
          </div>

          {/* Card Back */}
          <div
            style={{
              position: "absolute",
              width: "100%",
              height: "100%",
              backfaceVisibility: "hidden",
              borderRadius: "16px",
              backgroundColor: "#0f172a",
              color: "#ffffff",
              border: "1px solid #1e293b",
              padding: "32px 24px",
              boxSizing: "border-box",
              display: "flex",
              flexDirection: "column",
              justifyContent: "space-between",
              transform: "rotateY(180deg)",
            }}
          >
            <div style={{ fontSize: "11px", fontWeight: "bold", color: "#38bdf8", textTransform: "uppercase" }}>
              Explanation / Core Concept
            </div>

            <div style={{ fontSize: "16px", lineHeight: "1.6", color: "#f8fafc" }}>{currentCard.back}</div>

            <div style={{ fontSize: "12px", color: "#94a3b8" }}>Click to flip back</div>
          </div>
        </div>
      </div>

      {/* Spaced Repetition Mastery Controls */}
      <div style={{ width: "100%", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <button
          onClick={handlePrev}
          disabled={currentIndex === 0}
          style={{
            padding: "8px 16px",
            fontSize: "13px",
            borderRadius: "6px",
            border: "1px solid #cbd5e1",
            backgroundColor: "#ffffff",
            color: currentIndex === 0 ? "#94a3b8" : "#334155",
            cursor: currentIndex === 0 ? "not-allowed" : "pointer",
          }}
        >
          ◀ Previous
        </button>

        <div style={{ display: "flex", gap: "10px" }}>
          <button
            onClick={() => handleRate("review")}
            style={{
              padding: "8px 14px",
              fontSize: "13px",
              fontWeight: 600,
              borderRadius: "6px",
              border: "1px solid #fecaca",
              backgroundColor: "#fef2f2",
              color: "#b91c1c",
              cursor: "pointer",
            }}
          >
            Needs Practice
          </button>

          <button
            onClick={() => handleRate("mastered")}
            style={{
              padding: "8px 14px",
              fontSize: "13px",
              fontWeight: 600,
              borderRadius: "6px",
              border: "1px solid #bbf7d0",
              backgroundColor: "#f0fdf4",
              color: "#15803d",
              cursor: "pointer",
            }}
          >
            Mastered!
          </button>
        </div>

        <button
          onClick={handleNext}
          disabled={currentIndex >= cards.length - 1}
          style={{
            padding: "8px 16px",
            fontSize: "13px",
            borderRadius: "6px",
            border: "1px solid #cbd5e1",
            backgroundColor: "#ffffff",
            color: currentIndex >= cards.length - 1 ? "#94a3b8" : "#334155",
            cursor: currentIndex >= cards.length - 1 ? "not-allowed" : "pointer",
          }}
        >
          Next ▶
        </button>
      </div>
    </div>
  );
};

