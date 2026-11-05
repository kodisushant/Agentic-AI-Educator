import React, { useState } from "react";
import { ChatItem, ChatMessageResponse, BoardCommand } from "./types";

interface TeacherChatProps {
  concept: string;
  currentStepIndex: number;
  studentId?: string;
  onApplyBoardCommands?: (commands: BoardCommand[]) => void;
  className?: string;
}

export const TeacherChat: React.FC<TeacherChatProps> = ({
  concept,
  currentStepIndex,
  studentId = "demo_student",
  onApplyBoardCommands,
  className = "",
}) => {
  const [messages, setMessages] = useState<ChatItem[]>([
    {
      id: "msg_init",
      sender: "teacher",
      text: `Hello! I'm your AI Teacher for ${concept}. Ask me anything about the intuition, formulas, or code!`,
      timestamp: "Just now",
      agent_thoughts: "Welcoming student and inviting concept questions.",
    },
  ]);
  const [inputText, setInputText] = useState<string>("");
  const [isSending, setIsSending] = useState<boolean>(false);

  const quickQuestions = [
    "Why must the array be sorted?",
    "Why low + (high - low) // 2?",
    "What is the worst-case complexity?",
  ];

  const handleSendMessage = async (textToSend?: string) => {
    const text = (textToSend || inputText).trim();
    if (!text || isSending) return;

    const studentMsg: ChatItem = {
      id: `msg_s_${Date.now()}`,
      sender: "student",
      text,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, studentMsg]);
    setInputText("");
    setIsSending(true);

    try {
      const response = await fetch("http://localhost:8000/agent/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          student_id: studentId,
          concept,
          message: text,
          current_step_index: currentStepIndex,
        }),
      });

      let data: ChatMessageResponse;
      if (response.ok) {
        data = await response.json();
      } else {
        // Fallback local teacher response
        data = {
          reply: `Great question regarding ${concept}! In Binary Search, each comparison cuts the search space in half. If the array wasn't sorted, we wouldn't know which half could contain the target.`,
          suggested_board_commands: [
            {
              type: "text",
              id: "chat_note",
              content: "Key Principle: Halving search space requires sorted order!",
              x: 60.0,
              y: 390.0,
              size: 16,
              color: "#0284c7",
            },
          ],
          agent_thoughts: "Explaining divide-and-conquer precondition.",
        };
      }

      const teacherMsg: ChatItem = {
        id: `msg_t_${Date.now()}`,
        sender: "teacher",
        text: data.reply,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        agent_thoughts: data.agent_thoughts,
      };

      setMessages((prev) => [...prev, teacherMsg]);

      if (data.suggested_board_commands && data.suggested_board_commands.length > 0) {
        onApplyBoardCommands?.(data.suggested_board_commands);
      }
    } catch (err) {
      console.warn("Agent chat request failed, using offline fallback:", err);
      const teacherMsg: ChatItem = {
        id: `msg_t_${Date.now()}`,
        sender: "teacher",
        text: `In Binary Search, because elements are ordered, comparing our target against the middle item allows us to safely eliminate half the elements in one step!`,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        agent_thoughts: "Fallback cognitive explanation delivered.",
      };
      setMessages((prev) => [...prev, teacherMsg]);
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div
      className={`bg-slate-900/95 border border-slate-800 rounded-2xl p-4 shadow-2xl backdrop-blur flex flex-col h-[520px] ${className}`}
    >
      {/* Chat Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <div className="flex items-center space-x-2.5">
          <div className="w-7 h-7 rounded-lg bg-sky-500/20 text-sky-400 border border-sky-500/30 flex items-center justify-center">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
              />
            </svg>
          </div>
          <div>
            <h3 className="text-xs font-semibold text-slate-100">Live Teacher Chat</h3>
            <p className="text-[10px] text-slate-400">Ask clarifying questions anytime</p>
          </div>
        </div>
        <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
      </div>

      {/* Quick Prompt Pills */}
      <div className="flex gap-1.5 py-2 overflow-x-auto no-scrollbar border-b border-slate-800/60">
        {quickQuestions.map((q, idx) => (
          <button
            key={idx}
            onClick={() => handleSendMessage(q)}
            className="text-[10px] whitespace-nowrap bg-slate-800/80 hover:bg-slate-700/80 text-sky-300 px-2.5 py-1 rounded-full border border-slate-700/60 transition flex-shrink-0"
          >
            {q}
          </button>
        ))}
      </div>

      {/* Message History */}
      <div className="flex-1 overflow-y-auto py-3 space-y-3 pr-1 text-xs">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex flex-col ${msg.sender === "student" ? "items-end" : "items-start"}`}
          >
            <div
              className={`max-w-[85%] rounded-2xl p-3 shadow-md leading-relaxed ${
                msg.sender === "student"
                  ? "bg-sky-600 text-white rounded-br-sm"
                  : "bg-slate-800 text-slate-200 border border-slate-700/80 rounded-bl-sm"
              }`}
            >
              <p>{msg.text}</p>

              {msg.agent_thoughts && (
                <div className="mt-2 pt-2 border-t border-slate-700/60 text-[10px] font-mono text-indigo-300">
                  <span className="text-slate-400 font-semibold block mb-0.5">Teacher Reasoning:</span>
                  {msg.agent_thoughts}
                </div>
              )}
            </div>
            <span className="text-[9px] text-slate-500 mt-1 px-1">{msg.timestamp}</span>
          </div>
        ))}

        {isSending && (
          <div className="flex items-center space-x-2 text-slate-400 text-xs py-2">
            <div className="w-2 h-2 rounded-full bg-sky-400 animate-bounce" />
            <div className="w-2 h-2 rounded-full bg-sky-400 animate-bounce [animation-delay:0.2s]" />
            <div className="w-2 h-2 rounded-full bg-sky-400 animate-bounce [animation-delay:0.4s]" />
            <span className="text-[11px] text-slate-400 font-mono">Teacher is typing...</span>
          </div>
        )}
      </div>

      {/* Input Box */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSendMessage();
        }}
        className="pt-2 border-t border-slate-800 flex items-center gap-2"
      >
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="Ask your teacher a question..."
          className="flex-1 bg-slate-800/80 border border-slate-700/80 rounded-xl px-3 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500 transition"
        />
        <button
          type="submit"
          disabled={!inputText.trim() || isSending}
          className="p-2 bg-sky-500 hover:bg-sky-400 disabled:opacity-40 text-white rounded-xl transition shadow-md shadow-sky-500/20"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
          </svg>
        </button>
      </form>
    </div>
  );
};
