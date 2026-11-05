import React, { useEffect, useRef, useState } from "react";
import { VoiceSettings } from "./types";

interface NarrationPanelProps {
  narration: string;
  stepIndex: number;
  concept: string;
  onSpeechEnd?: () => void;
  className?: string;
}

export const NarrationPanel: React.FC<NarrationPanelProps> = ({
  narration,
  stepIndex,
  concept,
  onSpeechEnd,
  className = "",
}) => {
  const [voiceSettings, setVoiceSettings] = useState<VoiceSettings>({
    enabled: true,
    rate: 1.0,
    pitch: 1.0,
    volume: 1.0,
  });
  const [isSpeaking, setIsSpeaking] = useState<boolean>(false);
  const [isSupported, setIsSupported] = useState<boolean>(true);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);

  // Check speech synthesis support on mount
  useEffect(() => {
    if (typeof window !== "undefined" && !("speechSynthesis" in window)) {
      setIsSupported(false);
    }
  }, []);

  // Speak narration whenever step or narration text changes
  useEffect(() => {
    if (!isSupported || !voiceSettings.enabled || typeof window === "undefined") {
      return;
    }

    const synth = window.speechSynthesis;
    synth.cancel(); // Stop prior speech

    if (!narration.trim()) return;

    const utterance = new SpeechSynthesisUtterance(narration);
    utterance.rate = voiceSettings.rate;
    utterance.pitch = voiceSettings.pitch;
    utterance.volume = voiceSettings.volume;

    // Pick an expressive natural English voice if available
    const voices = synth.getVoices();
    const naturalVoice =
      voices.find((v) => v.lang.startsWith("en") && (v.name.includes("Natural") || v.name.includes("Google"))) ||
      voices.find((v) => v.lang.startsWith("en"));
    if (naturalVoice) {
      utterance.voice = naturalVoice;
    }

    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => {
      setIsSpeaking(false);
      onSpeechEnd?.();
    };
    utterance.onerror = (e) => {
      console.warn("Speech synthesis error:", e);
      setIsSpeaking(false);
    };

    utteranceRef.current = utterance;
    synth.speak(utterance);

    return () => {
      synth.cancel();
      setIsSpeaking(false);
    };
  }, [narration, stepIndex, voiceSettings.enabled, voiceSettings.rate, isSupported, onSpeechEnd]);

  const toggleVoice = () => {
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      if (voiceSettings.enabled) {
        window.speechSynthesis.cancel();
        setIsSpeaking(false);
      }
    }
    setVoiceSettings((prev) => ({ ...prev, enabled: !prev.enabled }));
  };

  const handleReplay = () => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) return;
    const synth = window.speechSynthesis;
    synth.cancel();

    if (!narration.trim()) return;

    const utterance = new SpeechSynthesisUtterance(narration);
    utterance.rate = voiceSettings.rate;
    utterance.pitch = voiceSettings.pitch;
    utterance.volume = voiceSettings.volume;

    const voices = synth.getVoices();
    const naturalVoice = voices.find((v) => v.lang.startsWith("en"));
    if (naturalVoice) utterance.voice = naturalVoice;

    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => {
      setIsSpeaking(false);
      onSpeechEnd?.();
    };
    utterance.onerror = () => setIsSpeaking(false);

    utteranceRef.current = utterance;
    synth.speak(utterance);
  };

  const cycleRate = () => {
    setVoiceSettings((prev) => {
      const rates = [0.85, 1.0, 1.2];
      const nextIdx = (rates.indexOf(prev.rate) + 1) % rates.length;
      return { ...prev, rate: rates[nextIdx] };
    });
  };

  return (
    <div
      className={`bg-slate-900/95 border border-slate-800 rounded-2xl p-5 shadow-xl backdrop-blur transition-all duration-300 ${className}`}
    >
      {/* Header with Persona & Audio Controls */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-3">
        <div className="flex items-center space-x-3">
          {/* Animated Teacher Avatar */}
          <div className="relative">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-500 to-indigo-600 flex items-center justify-center text-white font-bold text-sm shadow-lg shadow-sky-500/20">
              AI
            </div>
            {isSpeaking && (
              <span className="absolute -bottom-1 -right-1 w-3.5 h-3.5 rounded-full bg-emerald-500 border-2 border-slate-900 animate-ping" />
            )}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold text-slate-100">Virtual Teacher</span>
              <span className="text-[11px] font-mono text-sky-400 bg-sky-950/80 px-2 py-0.5 rounded border border-sky-800/50">
                {concept}
              </span>
            </div>
            <p className="text-[11px] text-slate-400">Step {stepIndex + 1} Spoken Explanation</p>
          </div>
        </div>

        {/* Audio Controls */}
        <div className="flex items-center space-x-2">
          {/* Animated Sound Wave Indicator */}
          {isSpeaking && (
            <div className="flex items-center gap-0.5 h-4 px-2 bg-emerald-950/60 rounded border border-emerald-800/50">
              <span className="w-0.5 h-2 bg-emerald-400 animate-pulse" />
              <span className="w-0.5 h-3.5 bg-emerald-400 animate-bounce" />
              <span className="w-0.5 h-1.5 bg-emerald-400 animate-pulse" />
              <span className="w-0.5 h-3 bg-emerald-400 animate-bounce" />
            </div>
          )}

          {/* Voice Speed Toggle */}
          <button
            onClick={cycleRate}
            title="Speech Speed"
            className="text-xs font-mono px-2 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg border border-slate-700 transition"
          >
            {voiceSettings.rate}x
          </button>

          {/* Replay Speech Button */}
          <button
            onClick={handleReplay}
            title="Replay Voice Narration"
            className="p-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white rounded-lg border border-slate-700 transition"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
          </button>

          {/* Mute/Unmute Toggle Button */}
          <button
            onClick={toggleVoice}
            title={voiceSettings.enabled ? "Mute Voice Narration" : "Enable Voice Narration"}
            className={`p-1.5 rounded-lg border transition ${
              voiceSettings.enabled
                ? "bg-sky-950/80 text-sky-400 border-sky-800 hover:bg-sky-900"
                : "bg-slate-800 text-slate-500 border-slate-700 hover:text-slate-300"
            }`}
          >
            {voiceSettings.enabled ? (
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z"
                />
              </svg>
            ) : (
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2"
                />
              </svg>
            )}
          </button>
        </div>
      </div>

      {/* Narration Body Caption */}
      <div className="relative">
        <p className="text-sm text-slate-200 leading-relaxed font-normal selection:bg-sky-500 selection:text-white">
          {narration}
        </p>
      </div>
    </div>
  );
};
