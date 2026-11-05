import React from "react";

interface ControlsBarProps {
  currentStep: number;
  totalSteps: number;
  isPlaying: boolean;
  onPlayPause: () => void;
  onNext: () => void;
  onPrev: () => void;
  onStepSelect: (index: number) => void;
  onDontUnderstand: () => void;
  isDontUnderstandLoading?: boolean;
  className?: string;
}

export const ControlsBar: React.FC<ControlsBarProps> = ({
  currentStep,
  totalSteps,
  isPlaying,
  onPlayPause,
  onNext,
  onPrev,
  onStepSelect,
  onDontUnderstand,
  isDontUnderstandLoading = false,
  className = "",
}) => {
  return (
    <div
      className={`bg-slate-900/95 border border-slate-800 rounded-2xl p-4 shadow-xl backdrop-blur flex flex-col sm:flex-row items-center justify-between gap-4 ${className}`}
    >
      {/* Step Indicators / Stepper */}
      <div className="flex items-center space-x-2">
        <span className="text-xs font-semibold text-slate-400 mr-2">Steps:</span>
        <div className="flex items-center space-x-1.5">
          {Array.from({ length: totalSteps }).map((_, idx) => {
            const isCurrent = idx === currentStep;
            const isCompleted = idx < currentStep;

            return (
              <button
                key={idx}
                onClick={() => onStepSelect(idx)}
                className={`w-7 h-7 rounded-lg text-xs font-semibold font-mono flex items-center justify-center transition-all ${
                  isCurrent
                    ? "bg-sky-500 text-white shadow-lg shadow-sky-500/30 scale-105 border border-sky-400"
                    : isCompleted
                    ? "bg-emerald-950/80 text-emerald-400 border border-emerald-800/80 hover:bg-emerald-900"
                    : "bg-slate-800 text-slate-400 border border-slate-700/60 hover:bg-slate-750 hover:text-slate-200"
                }`}
                title={`Jump to step ${idx + 1}`}
              >
                {idx + 1}
              </button>
            );
          })}
        </div>
      </div>

      {/* Main Playback Buttons */}
      <div className="flex items-center space-x-3">
        {/* Previous Step */}
        <button
          onClick={onPrev}
          disabled={currentStep === 0}
          className="p-2 bg-slate-800 hover:bg-slate-700 disabled:opacity-40 disabled:hover:bg-slate-800 text-slate-200 rounded-xl border border-slate-700 transition"
          title="Previous Step"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>

        {/* Play / Pause Toggle */}
        <button
          onClick={onPlayPause}
          className="px-4 py-2 bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white font-medium rounded-xl shadow-lg shadow-sky-500/25 flex items-center gap-2 transition"
          title={isPlaying ? "Pause Step Auto-Advance" : "Play Step Auto-Advance"}
        >
          {isPlaying ? (
            <>
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              <span className="text-xs">Pause</span>
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
              </svg>
              <span className="text-xs">Play</span>
            </>
          )}
        </button>

        {/* Next Step */}
        <button
          onClick={onNext}
          disabled={currentStep >= totalSteps - 1}
          className="p-2 bg-slate-800 hover:bg-slate-700 disabled:opacity-40 disabled:hover:bg-slate-800 text-slate-200 rounded-xl border border-slate-700 transition"
          title="Next Step"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>

      {/* Adaptive "I don't understand" Button */}
      <div>
        <button
          onClick={onDontUnderstand}
          disabled={isDontUnderstandLoading}
          className="px-3.5 py-2 bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 hover:text-amber-200 border border-amber-500/30 rounded-xl text-xs font-semibold flex items-center gap-2 transition shadow-sm group"
          title="Ask Teacher to explain this step more simply"
        >
          <span className="w-2 h-2 rounded-full bg-amber-400 group-hover:animate-ping" />
          {isDontUnderstandLoading ? (
            <span className="flex items-center gap-1.5">
              <svg className="animate-spin w-3.5 h-3.5" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              Adapting...
            </span>
          ) : (
            "I don't understand"
          )}
        </button>
      </div>
    </div>
  );
};
