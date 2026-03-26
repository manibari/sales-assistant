"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import {
  MessageCircle,
  X,
  Send,
  Loader2,
  Minimize2,
  ChevronDown,
  Sparkles,
} from "lucide-react";
import { nxApi } from "@/lib/nexus-api";

interface ChatMessage {
  role: "user" | "assistant";
  text: string;
  intent?: string;
  intel_id?: number | null;
}

function generateSessionId(): string {
  return `web:${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

export function AssistantChat() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState("");
  const [sending, setSending] = useState(false);
  const [sessionId, setSessionId] = useState(() => generateSessionId());

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  useEffect(() => {
    if (open) {
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [open]);

  const handleSend = async () => {
    const text = inputText.trim();
    if (!text || sending) return;

    setInputText("");
    setSending(true);

    // Add user message
    setMessages((prev) => [...prev, { role: "user", text }]);

    // Show thinking indicator
    setMessages((prev) => [
      ...prev,
      { role: "assistant", text: "思考中..." },
    ]);

    try {
      // Check if it's a command
      if (text.startsWith("/")) {
        const result = await nxApi.assistant.command(sessionId, text);
        setMessages((prev) => [
          ...prev.slice(0, -1),
          {
            role: "assistant",
            text: result.text,
            intent: result.intent,
            intel_id: result.intel_id,
          },
        ]);
        if (result.session_closed) {
          // Start fresh session for next conversation
          setSessionId(generateSessionId());
        }
      } else {
        const result = await nxApi.assistant.chat(sessionId, text);
        setMessages((prev) => [
          ...prev.slice(0, -1),
          {
            role: "assistant",
            text: result.text,
            intent: result.intent,
            intel_id: result.intel_id,
          },
        ]);
        if (result.session_closed) {
          setSessionId(generateSessionId());
        }
      }
    } catch (err) {
      console.error(err);
      setMessages((prev) => [
        ...prev.slice(0, -1),
        { role: "assistant", text: "⚠️ 發生錯誤，請重試" },
      ]);
    }

    setSending(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleNewConversation = () => {
    setMessages([]);
    setSessionId(generateSessionId());
    inputRef.current?.focus();
  };

  // Floating button when closed
  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="fixed bottom-24 md:bottom-6 right-4 md:right-6 z-50 w-14 h-14 rounded-full bg-blue-500 text-white shadow-lg shadow-blue-500/25 hover:bg-blue-600 hover:shadow-xl hover:shadow-blue-500/30 transition-all flex items-center justify-center cursor-pointer group"
      >
        <MessageCircle
          size={24}
          className="group-hover:scale-110 transition-transform"
        />
        {messages.length > 0 && (
          <span className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-red-500 text-white text-[10px] flex items-center justify-center font-medium">
            {messages.filter((m) => m.role === "assistant").length}
          </span>
        )}
      </button>
    );
  }

  return (
    <div className="fixed bottom-24 md:bottom-6 right-4 md:right-6 z-50 w-[calc(100vw-2rem)] md:w-[420px] h-[min(70vh,600px)] bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-800 flex flex-col overflow-hidden">
      {/* Header */}
      <div className="h-12 px-4 flex items-center justify-between border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50 shrink-0">
        <div className="flex items-center gap-2">
          <Sparkles size={16} className="text-blue-500" />
          <span className="text-sm font-semibold text-slate-900 dark:text-slate-50">
            助理
          </span>
        </div>
        <div className="flex items-center gap-1">
          {messages.length > 0 && (
            <button
              onClick={handleNewConversation}
              className="p-1.5 rounded-lg text-slate-400 hover:text-blue-500 hover:bg-blue-500/10 cursor-pointer transition-colors text-[11px] px-2"
              title="新對話"
            >
              新對話
            </button>
          )}
          <button
            onClick={() => setOpen(false)}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 cursor-pointer transition-colors"
          >
            <ChevronDown size={16} />
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-auto">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full px-6 text-center">
            <div className="w-12 h-12 rounded-2xl bg-blue-500/10 flex items-center justify-center mb-3">
              <MessageCircle size={24} className="text-blue-500" />
            </div>
            <p className="text-sm font-medium text-slate-900 dark:text-slate-50 mb-1">
              隨時回報情報
            </p>
            <p className="text-xs text-slate-400 leading-relaxed">
              直接打字就好 — 拜訪筆記、客戶資訊、會議紀錄
              <br />
              也可以查資料：「查 美珍香」「今天行程」
            </p>
          </div>
        ) : (
          <div className="px-3 py-3 space-y-3">
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`flex ${
                  msg.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                <div
                  className={`max-w-[85%] px-3 py-2 rounded-xl text-[13px] leading-relaxed whitespace-pre-wrap ${
                    msg.role === "user"
                      ? "bg-blue-500 text-white rounded-br-sm"
                      : "bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-50 rounded-bl-sm"
                  }`}
                >
                  {msg.text}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input */}
      <div className="px-3 py-2 border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shrink-0">
        <div className="relative">
          <textarea
            ref={inputRef}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="輸入情報或問問題..."
            rows={1}
            className="w-full resize-none bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-2.5 pr-10 text-[13px] text-slate-900 dark:text-slate-50 placeholder:text-slate-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none min-h-[40px] max-h-24"
            style={{ height: "auto" }}
            onInput={(e) => {
              const target = e.target as HTMLTextAreaElement;
              target.style.height = "auto";
              target.style.height =
                Math.min(target.scrollHeight, 96) + "px";
            }}
          />
          <button
            onClick={handleSend}
            disabled={!inputText.trim() || sending}
            className="absolute right-1.5 bottom-1.5 p-1.5 rounded-lg bg-blue-500 text-white disabled:opacity-30 cursor-pointer hover:bg-blue-600 transition-colors disabled:cursor-not-allowed"
          >
            {sending ? (
              <Loader2 size={14} className="animate-spin" />
            ) : (
              <Send size={14} />
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
