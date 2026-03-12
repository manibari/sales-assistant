"use client";

import { useState, useEffect, useRef, useCallback, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { TopBar } from "@/components/top-bar";
import {
  Check,
  Loader2,
  Send,
  Zap,
  User,
  Bot,
} from "lucide-react";
import { nxApi, type NxIntel, type MaterializeResult } from "@/lib/nexus-api";

interface ChatMsg {
  role: "user" | "ai" | "system";
  text: string;
}

function ChatFlow() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const intelId = Number(searchParams.get("id"));

  const [intel, setIntel] = useState<NxIntel | null>(null);
  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [parsed, setParsed] = useState<Record<string, unknown>>({});
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [initializing, setInitializing] = useState(true);
  const [confirming, setConfirming] = useState(false);
  const [done, setDone] = useState(false);
  const [matResult, setMatResult] = useState<MaterializeResult | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Initial load + AI parse
  useEffect(() => {
    if (!intelId) return;
    (async () => {
      try {
        const intelData = await nxApi.intel.get(intelId);
        setIntel(intelData);

        // Show raw input as first message
        setMessages([
          { role: "user", text: intelData.raw_input },
          { role: "system", text: "AI 正在分析..." },
        ]);

        // Run initial parse
        const result = await nxApi.intel.parse(intelId);
        setParsed(result.parsed);

        setMessages([
          { role: "user", text: intelData.raw_input },
          { role: "ai", text: result.ai_reply },
        ]);
      } catch (err) {
        console.error("Init failed:", err);
        setMessages([{ role: "system", text: "AI 解析失敗，請重試" }]);
      } finally {
        setInitializing(false);
        setTimeout(() => inputRef.current?.focus(), 100);
      }
    })();
  }, [intelId]);

  const handleSend = useCallback(async () => {
    const msg = input.trim();
    if (!msg || sending) return;

    setInput("");
    setSending(true);
    setMessages((prev) => [...prev, { role: "user", text: msg }]);

    try {
      const result = await nxApi.intel.chat(intelId, msg, parsed);
      setParsed(result.parsed);
      setMessages((prev) => [...prev, { role: "ai", text: result.ai_reply }]);
    } catch (err) {
      console.error("Chat failed:", err);
      setMessages((prev) => [...prev, { role: "system", text: "AI 回覆失敗，請重試" }]);
    } finally {
      setSending(false);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [input, sending, intelId, parsed]);

  const handleConfirm = async () => {
    setConfirming(true);
    try {
      await nxApi.intel.confirm(intelId, JSON.stringify(parsed));
      const mat = await nxApi.intel.materialize(intelId);
      setMatResult(mat);
      setDone(true);
    } catch (err) {
      console.error("Confirm failed:", err);
      setMessages((prev) => [...prev, { role: "system", text: "確認失敗，請重試" }]);
    } finally {
      setConfirming(false);
    }
  };

  // --- Render ---

  if (!intelId) {
    return (
      <div className="flex flex-col h-full">
        <TopBar title="情報對話" />
        <div className="flex-1 flex items-center justify-center text-slate-500">
          Missing intel ID
        </div>
      </div>
    );
  }

  if (done) {
    const client = matResult?.client;
    const partner = matResult?.partner;
    const contacts = matResult?.contacts || [];
    return (
      <div className="flex flex-col h-full">
        <TopBar title="完成" />
        <div className="flex-1 flex flex-col items-center justify-center gap-6 px-4">
          <div className="w-16 h-16 rounded-full bg-green-500/10 flex items-center justify-center">
            <Check size={32} className="text-green-500" />
          </div>
          <div className="text-center space-y-2">
            <h2 className="text-xl font-bold text-slate-900 dark:text-slate-50">
              情報 #{intelId} 已確認
            </h2>
            {client && (
              <p className="text-sm text-slate-600 dark:text-slate-300">
                🔗 {client.action === "created" ? "已建立" : "已匹配"}客戶「{client.name}」
              </p>
            )}
            {partner && (
              <p className="text-sm text-slate-600 dark:text-slate-300">
                🤝 {partner.action === "created" ? "已建立" : "已匹配"}夥伴「{partner.name}」
              </p>
            )}
            {contacts.map((c, i) => (
              <p key={i} className="text-sm text-slate-600 dark:text-slate-300">
                👤 {c.action === "created" ? "已建立" : "已匹配"}聯絡人「{c.name}」
              </p>
            ))}
          </div>
          <div className="flex gap-3 w-full max-w-xs">
            <button
              onClick={() => router.push("/capture")}
              className="flex-1 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-700 font-medium px-6 py-3 rounded-lg min-h-[44px] cursor-pointer transition-colors"
            >
              再加一筆
            </button>
            <button
              onClick={() => router.push("/intel")}
              className="flex-1 bg-blue-500 hover:bg-blue-600 text-white font-semibold px-6 py-3 rounded-lg min-h-[44px] cursor-pointer transition-all"
            >
              查看情報
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <TopBar title={`情報 #${intelId} 對話`}>
        <button
          onClick={handleConfirm}
          disabled={confirming || initializing}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-green-500 hover:bg-green-600 disabled:opacity-50 text-white text-sm font-medium rounded-lg cursor-pointer transition-colors"
        >
          {confirming ? <Loader2 size={14} className="animate-spin" /> : <Check size={14} />}
          確認
        </button>
      </TopBar>

      {/* Chat messages */}
      <div className="flex-1 overflow-auto px-4 py-4 space-y-3">
        {/* Parsed fields summary (collapsible) */}
        {Object.keys(parsed).length > 0 && (
          <div className="mx-auto max-w-2xl mb-2">
            <details className="bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 rounded-lg">
              <summary className="px-3 py-2 text-xs font-medium text-slate-500 dark:text-slate-400 cursor-pointer flex items-center gap-1.5">
                <Zap size={12} /> 已解析 {Object.keys(parsed).length} 個欄位
              </summary>
              <div className="px-3 pb-2 text-xs text-slate-600 dark:text-slate-300 space-y-0.5">
                {Object.entries(parsed).map(([k, v]) => (
                  <div key={k}>
                    <span className="text-slate-400">{k}:</span>{" "}
                    <span>{Array.isArray(v) ? (v as string[]).join(", ") : String(v)}</span>
                  </div>
                ))}
              </div>
            </details>
          </div>
        )}

        <div className="max-w-2xl mx-auto space-y-3">
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`flex gap-2 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              {msg.role !== "user" && (
                <div className="w-7 h-7 rounded-full bg-blue-500/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <Bot size={14} className="text-blue-500" />
                </div>
              )}
              <div
                className={`max-w-[80%] px-3.5 py-2.5 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
                  msg.role === "user"
                    ? "bg-blue-500 text-white rounded-br-md"
                    : msg.role === "system"
                      ? "bg-slate-200 dark:bg-slate-700 text-slate-500 dark:text-slate-400 italic"
                      : "bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-50 rounded-bl-md"
                }`}
              >
                {msg.text}
              </div>
              {msg.role === "user" && (
                <div className="w-7 h-7 rounded-full bg-slate-200 dark:bg-slate-700 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <User size={14} className="text-slate-500" />
                </div>
              )}
            </div>
          ))}

          {sending && (
            <div className="flex gap-2 justify-start">
              <div className="w-7 h-7 rounded-full bg-blue-500/10 flex items-center justify-center flex-shrink-0">
                <Bot size={14} className="text-blue-500" />
              </div>
              <div className="px-3.5 py-2.5 bg-slate-100 dark:bg-slate-800 rounded-2xl rounded-bl-md">
                <Loader2 size={16} className="animate-spin text-slate-400" />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input bar */}
      <div className="border-t border-slate-200 dark:border-slate-700 px-4 py-3 bg-white dark:bg-slate-900">
        <div className="max-w-2xl mx-auto flex gap-2">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.nativeEvent.isComposing) handleSend();
            }}
            placeholder="輸入補充資訊..."
            disabled={sending || initializing}
            className="flex-1 bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-full px-4 py-2.5 text-sm text-slate-900 dark:text-slate-50 placeholder:text-slate-400 focus:border-blue-500 focus:outline-none disabled:opacity-50 transition-colors"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || sending || initializing}
            className="w-10 h-10 flex items-center justify-center bg-blue-500 hover:bg-blue-600 disabled:opacity-30 text-white rounded-full cursor-pointer transition-colors"
          >
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}

export default function QaPage() {
  return (
    <Suspense
      fallback={
        <div className="flex items-center justify-center h-full">
          <Loader2 size={24} className="animate-spin text-blue-500" />
        </div>
      }
    >
      <ChatFlow />
    </Suspense>
  );
}
