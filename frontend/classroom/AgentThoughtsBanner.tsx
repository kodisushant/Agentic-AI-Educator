import React, { useState } from "react";

interface AgentThoughtsBannerProps {
  agentThoughts?: string | null;
  detectedMisconception?: string | null;
  remediation?: string | null;
  providerMetadata?: Record<string, any> | null;
  className?: string;
}

export const AgentThoughtsBanner: React.FC<AgentThoughtsBannerProps> = ({
  agentThoughts,
  detectedMisconception,
  remediation,
  providerMetadata,
  className = "",
}) => {
  const [isExpanded, setIsExpanded] = useState<boolean>(true);

  if (!agentThoughts && !detectedMisconception && !remediation) {
    return null;
  }

  return (
    <div
      className={`rounded-2xl border transition-all duration-300 overflow-hidden shadow-lg ${
        detectedMisconception
          ? "bg-rose-950/40 border-rose-800/60"
          : "bg-slate-900/90 border-slate-800/80"
      } ${className}`}
    >
      {/* Banner Header */}
      <div
        onClick={() => setIsExpanded(!isExpanded)}
        className="px-4 py-2.5 flex items-center justify-between cursor-pointer hover:bg-slate-800/40 transition select-none"
      >
        <div className="flex items-center space-x-2.5">
          <div
            className={`w-6 h-6 rounded-lg flex items-center justify-center ${
              detectedMisconception ? "bg-rose-600/30 text-rose-300" : "bg-indigo-600/30 text-indigo-300"
            }`}
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
              />
            </svg>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-slate-200">
                {detectedMisconception ? "Misconception Diagnosed" : "Agent Reasoning Trace"}
              </span>
              {providerMetadata?.provider && (
                <span className="text-[10px] font-mono bg-slate-800 text-sky-400 px-1.5 py-0.5 rounded border border-slate-700">
                  {providerMetadata.provider}{" "}
                  {providerMetadata.latency_ms ? `(${providerMetadata.latency_ms}ms)` : ""}
                </span>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {detectedMisconception && (
            <span className="text-[11px] font-mono text-rose-300 bg-rose-950/80 px-2 py-0.5 rounded border border-rose-800">
              {detectedMisconception}
            </span>
          )}
          <svg
            className={`w-4 h-4 text-slate-400 transform transition-transform ${
              isExpanded ? "rotate-180" : ""
            }`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </div>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="px-4 pb-3.5 pt-1 space-y-2.5 text-xs text-slate-300 border-t border-slate-800/60">
          {agentThoughts && (
            <div className="bg-slate-950/60 p-2.5 rounded-xl border border-slate-800/80 font-mono text-[11px] leading-relaxed text-indigo-300">
              <span className="text-slate-500 font-semibold uppercase tracking-wider block mb-1 text-[10px]">
                Agent Cognitive Thought:
              </span>
              {agentThoughts}
            </div>
          )}

          {remediation && (
            <div className="bg-rose-950/40 p-2.5 rounded-xl border border-rose-800/60 text-[11px] leading-relaxed text-rose-200">
              <span className="text-rose-400 font-semibold uppercase tracking-wider block mb-1 text-[10px] flex items-center gap-1">
                <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                    clipRule="evenodd"
                  />
                </svg>
                Pedagogical Remediation Plan:
              </span>
              {remediation}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
