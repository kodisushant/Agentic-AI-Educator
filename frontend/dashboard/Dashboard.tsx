"use client";

import React, { useEffect, useState } from "react";

interface WeakConcept {
  concept_tag: string;
  mastery_score: number;
  active_misconceptions: string[];
  recommended_action: string;
}

interface AttemptItem {
  id: number;
  concept_tag: string;
  is_correct: boolean;
  time_spent_seconds: number;
  misconceptions: string[];
  created_at: string;
}

interface Recommendation {
  recommended_concept: string;
  reason: string;
  suggested_action: "lesson" | "quiz" | "flashcard";
}

interface LearnerData {
  user_id: string;
  overall_score: number;
  concept_scores: Record<string, number>;
  attempt_counts: Record<string, number>;
  weak_concepts: WeakConcept[];
  recommendation: Recommendation;
  history: AttemptItem[];
}

export default function LearnerDashboard({ userId = "demo_student" }: { userId?: string }) {
  const [data, setData] = useState<LearnerData | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchLearnerData = async () => {
    try {
      const res = await fetch(`http://localhost:8000/learner/mastery/${userId}`);
      if (res.ok) {
        const mastery = await res.json();
        const weakRes = await (await fetch(`http://localhost:8000/learner/weak/${userId}`)).json();
        const recRes = await (await fetch(`http://localhost:8000/learner/recommend/${userId}`)).json();
        setData({
          user_id: userId,
          overall_score: mastery.overall_score,
          concept_scores: mastery.concept_scores,
          attempt_counts: mastery.attempt_counts,
          weak_concepts: weakRes.weak_concepts || [],
          recommendation: recRes,
          history: [],
        });
      }
    } catch {
      // Default fallback
      setData({
        user_id: "demo_student",
        overall_score: 0.66,
        concept_scores: {
          binary_search_intuition: 0.90,
          binary_search_bounds_update: 0.45,
          binary_search_complexity: 0.80,
          binary_search_edge_cases: 0.55,
        },
        attempt_counts: {
          binary_search_intuition: 3,
          binary_search_bounds_update: 4,
          binary_search_complexity: 2,
          binary_search_edge_cases: 2,
        },
        weak_concepts: [
          {
            concept_tag: "binary_search_bounds_update",
            mastery_score: 0.45,
            active_misconceptions: ["confuses_direction_when_target_greater"],
            recommended_action: "Review pointer movement: when target > mid, search the right partition.",
          },
        ],
        recommendation: {
          recommended_concept: "binary_search_bounds_update",
          reason: "Priority practice: lowest mastery (0.45) with active misconceptions.",
          suggested_action: "quiz",
        },
        history: [],
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLearnerData();
  }, [userId]);

  if (loading || !data) {
    return <div className="p-8 text-center text-slate-400">Loading student learner model...</div>;
  }

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6 bg-slate-900 text-slate-100 rounded-2xl border border-slate-800">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-xl font-bold text-white">Learner Mastery & Misconception Model</h2>
          <p className="text-sm text-slate-400">Student: {data.user_id} • EWMA Algorithm with Ebbinghaus Decay</p>
        </div>
        <div className="text-right">
          <span className="text-2xl font-extrabold text-sky-400">{Math.round(data.overall_score * 100)}%</span>
          <p className="text-xs text-slate-400">Overall Mastery</p>
        </div>
      </div>

      {/* Recommendation Card */}
      <div className="bg-sky-950/40 border border-sky-800/60 p-4 rounded-xl flex items-center justify-between">
        <div className="space-y-1">
          <span className="text-xs uppercase font-bold text-sky-400">Recommended Next Step</span>
          <h4 className="text-base font-semibold text-white">{data.recommendation.recommended_concept.replace(/_/g, " ").toUpperCase()}</h4>
          <p className="text-xs text-slate-300">{data.recommendation.reason}</p>
        </div>
        <span className="px-3 py-1 rounded-lg text-xs font-bold uppercase bg-amber-500/20 text-amber-300 border border-amber-500/30">
          {data.recommendation.suggested_action}
        </span>
      </div>

      {/* Concept Breakdown Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {Object.entries(data.concept_scores).map(([tag, score]) => {
          const pct = Math.round(score * 100);
          const isWeak = score < 0.60;
          return (
            <div key={tag} className="p-4 bg-slate-950/50 rounded-xl border border-slate-800 space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm font-semibold text-slate-200">{tag.replace(/_/g, " ")}</span>
                <span className={`text-xs font-mono font-bold ${isWeak ? "text-rose-400" : "text-emerald-400"}`}>
                  {pct}%
                </span>
              </div>
              <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full ${isWeak ? "bg-rose-500" : pct >= 75 ? "bg-emerald-500" : "bg-sky-500"}`}
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {/* Weak Areas & Diagnosed Misconceptions */}
      {data.weak_concepts.length > 0 && (
        <div className="space-y-3 pt-2">
          <h3 className="text-sm font-bold uppercase tracking-wider text-rose-400">Active Weak Areas & Misconceptions</h3>
          <div className="space-y-2">
            {data.weak_concepts.map((w) => (
              <div key={w.concept_tag} className="p-3 bg-rose-950/20 border border-rose-900/40 rounded-xl space-y-1">
                <div className="flex justify-between items-center text-xs">
                  <span className="font-semibold text-white">{w.concept_tag.replace(/_/g, " ")}</span>
                  <span className="text-rose-400 font-mono font-bold">{Math.round(w.mastery_score * 100)}%</span>
                </div>
                <p className="text-xs text-slate-300">{w.recommended_action}</p>
                <div className="flex flex-wrap gap-1 mt-1">
                  {w.active_misconceptions.map((m) => (
                    <span key={m} className="px-2 py-0.5 rounded text-[10px] font-mono bg-rose-500/20 text-rose-300 border border-rose-500/30">
                      ⚠️ {m}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
