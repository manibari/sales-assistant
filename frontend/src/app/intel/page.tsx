"use client";

import { useState, useEffect, useRef, useCallback, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  Loader2,
  Send,
  FileText,
  Camera,
  Mic,
  PanelLeftOpen,
  PanelLeftClose,
  Plus,
  Trash2,
  Briefcase,
  Calendar,
  Tag,
  ChevronDown,
  Sparkles,
  X,
} from "lucide-react";
import { nxApi, type NxIntel, type NxDeal } from "@/lib/nexus-api";
import { getIntelDisplayTitle } from "@/lib/intel-display";

interface ChatMessage {
  role: "user" | "assistant" | "system";
  text: string;
}

const INPUT_ICONS: Record<string, typeof FileText> = {
  text: FileText,
  photo: Camera,
  voice: Mic,
};

const FIELD_LABELS: Record<string, string> = {
  role: "角色", industry: "產業", pain_points: "痛點",
  nda_status: "NDA 狀態", mou_status: "MOU 狀態", budget: "預估預算",
  capabilities: "能力標籤", industry_exp: "產業經驗", team_size: "團隊規模",
  subsidy_partner: "合作夥伴", subsidy_deadline: "補助截止",
};

const VALUE_LABELS: Record<string, string> = {
  client: "客戶", partner: "夥伴", si: "SI", subsidy: "政府補貼", other: "其他",
  food: "食品業", petrochemical: "石化業", semiconductor: "半導體", manufacturing: "製造業",
  pending: "尚未開始", in_progress: "進行中", signed: "已簽署",
  not_required: "不需要", unknown: "未知",
};

function formatValue(value: string | string[]): string {
  if (Array.isArray(value)) return value.map((v) => VALUE_LABELS[v] || v).join("、");
  return VALUE_LABELS[value] || value;
}

export default function IntelPageWrapper() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center h-full text-slate-400 text-sm">載入中...</div>}>
      <IntelPage />
    </Suspense>
  );
}

function IntelPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialId = searchParams.get("id");
  const [intels, setIntels] = useState<NxIntel[]>([]);
  const [loadingList, setLoadingList] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // Current conversation
  const [activeIntel, setActiveIntel] = useState<NxIntel | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [parsed, setParsed] = useState<Record<string, string | string[]> | null>(null);
  const [inputText, setInputText] = useState("");
  const [sending, setSending] = useState(false);
  const [showInfo, setShowInfo] = useState(false);

  // Deal linking
  const [showLinkDeal, setShowLinkDeal] = useState(false);
  const [allDeals, setAllDeals] = useState<NxDeal[]>([]);
  const [linking, setLinking] = useState(false);

  // Audio transcription
  type TranscribeStage = "idle" | "uploading" | "transcribing" | "parsing" | "done" | "error";
  const [transcribeStage, setTranscribeStage] = useState<TranscribeStage>("idle");
  const [transcribeError, setTranscribeError] = useState<string | null>(null);
  const [transcribeSlow, setTranscribeSlow] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  // Load intel list + auto-select from URL
  useEffect(() => {
    nxApi.intel
      .list(undefined, 100)
      .then((list) => {
        setIntels(list);
        if (initialId) {
          const target = list.find((i) => i.id === Number(initialId));
          if (target) {
            setActiveIntel(target);
            loadConversation(target);
          }
        }
      })
      .catch(console.error)
      .finally(() => setLoadingList(false));
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Scroll on new messages
  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Build messages from intel data
  const loadConversation = useCallback((intel: NxIntel) => {
    const msgs: ChatMessage[] = [];

    // Chat history contains the full conversation including initial raw_input
    if (intel.chat_history) {
      try {
        const history = JSON.parse(intel.chat_history) as { role: string; text: string }[];
        for (const h of history) {
          // Normalize: "ai" (legacy) → "assistant"
          const role = h.role === "ai" ? "assistant" : h.role;
          msgs.push({ role: role as "user" | "assistant", text: h.text });
        }
      } catch { /* ignore */ }
    }

    // Fallback: if no chat history, show raw_input as first message
    if (msgs.length === 0) {
      msgs.push({ role: "user", text: intel.raw_input });
    }

    setMessages(msgs);

    // Parsed data
    if (intel.parsed_json) {
      try {
        setParsed(JSON.parse(intel.parsed_json));
      } catch {
        setParsed(null);
      }
    } else {
      setParsed(null);
    }
  }, []);

  const handleSelectIntel = useCallback(async (intel: NxIntel) => {
    setActiveIntel(intel);
    loadConversation(intel);
    setShowInfo(false);
    // On mobile, close sidebar
    if (window.innerWidth < 768) setSidebarOpen(false);
  }, [loadConversation]);

  // Create new conversation
  const handleNewChat = () => {
    setActiveIntel(null);
    setMessages([]);
    setParsed(null);
    setInputText("");
    setShowInfo(false);
    inputRef.current?.focus();
  };

  // Send message
  const handleSend = async () => {
    const text = inputText.trim();
    if (!text || sending) return;

    setInputText("");
    setSending(true);

    if (!activeIntel) {
      // Create new intel + parse
      setMessages([{ role: "user", text }]);
      try {
        const newIntel = await nxApi.intel.create({
          raw_input: text,
          input_type: "text",
        });
        setActiveIntel(newIntel);
        setIntels((prev) => [newIntel, ...prev]);

        // Auto-parse
        setMessages((prev) => [...prev, { role: "assistant", text: "分析中..." }]);
        const parseResult = await nxApi.intel.parse(newIntel.id);
        setMessages((prev) => [
          ...prev.slice(0, -1),
          { role: "assistant", text: parseResult.ai_reply },
        ]);
        if (parseResult.parsed) {
          setParsed(parseResult.parsed as Record<string, string | string[]>);
        }
        // Refresh intel data
        const updated = await nxApi.intel.get(newIntel.id);
        setActiveIntel(updated);
        setIntels((prev) => prev.map((i) => (i.id === updated.id ? updated : i)));
      } catch (err) {
        console.error(err);
        setMessages((prev) => [
          ...prev,
          { role: "assistant", text: "發生錯誤，請重試" },
        ]);
      }
    } else {
      // Continue chat
      setMessages((prev) => [...prev, { role: "user", text }]);
      setMessages((prev) => [...prev, { role: "assistant", text: "思考中..." }]);
      try {
        const result = await nxApi.intel.chat(
          activeIntel.id,
          text,
          parsed || {},
        );
        setMessages((prev) => [
          ...prev.slice(0, -1),
          { role: "assistant", text: result.ai_reply },
        ]);
        if (result.parsed) {
          setParsed(result.parsed as Record<string, string | string[]>);
        }
        // Refresh intel
        const updated = await nxApi.intel.get(activeIntel.id);
        setActiveIntel(updated);
        setIntels((prev) => prev.map((i) => (i.id === updated.id ? updated : i)));
      } catch (err) {
        console.error(err);
        setMessages((prev) => [
          ...prev.slice(0, -1),
          { role: "assistant", text: "發生錯誤，請重試" },
        ]);
      }
    }

    setSending(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleDelete = async (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    if (!confirm("確定要刪除這筆情報？")) return;
    try {
      await nxApi.intel.delete(id);
      setIntels((prev) => prev.filter((i) => i.id !== id));
      if (activeIntel?.id === id) handleNewChat();
    } catch (err) {
      console.error(err);
    }
  };

  const handleOpenLinkDeal = async () => {
    setShowLinkDeal(true);
    try {
      const deals = await nxApi.deals.list("urgency");
      setAllDeals(deals);
    } catch (err) {
      console.error(err);
    }
  };

  const handleLinkDeal = async (dealId: number) => {
    if (!activeIntel) return;
    setLinking(true);
    try {
      await nxApi.deals.linkIntel(dealId, activeIntel.id);
      const updated = await nxApi.intel.get(activeIntel.id);
      setActiveIntel(updated);
      setShowLinkDeal(false);
    } catch (err) {
      console.error(err);
    } finally {
      setLinking(false);
    }
  };

  const linkedDealIds = new Set((activeIntel?.linked_deals || []).map((d) => d.id));

  const handleAudioUpload = async (file: File) => {
    if (!activeIntel) return;

    setTranscribeStage("uploading");
    setTranscribeError(null);
    setTranscribeSlow(false);

    // Advance to transcribing after brief upload phase
    const stageTimer = setTimeout(
      () => setTranscribeStage((s) => (s === "uploading" ? "transcribing" : s)),
      1500,
    );
    // Show slow hint after 8s
    const slowTimer = setTimeout(() => setTranscribeSlow(true), 8000);

    try {
      const result = await nxApi.intel.transcribe(activeIntel.id, file);
      clearTimeout(stageTimer);
      clearTimeout(slowTimer);
      setTranscribeStage("parsing");

      setMessages([
        { role: "user", text: result.transcript },
        ...(result.ai_reply ? [{ role: "assistant" as const, text: result.ai_reply }] : []),
      ]);
      if (result.parsed && Object.keys(result.parsed).length > 0) {
        setParsed(result.parsed as Record<string, string | string[]>);
      }

      const updated = await nxApi.intel.get(activeIntel.id);
      setActiveIntel(updated);
      setIntels((prev) => prev.map((i) => (i.id === updated.id ? updated : i)));

      setTranscribeStage("done");
      setTimeout(() => setTranscribeStage("idle"), 2000);
    } catch (err) {
      clearTimeout(stageTimer);
      clearTimeout(slowTimer);
      setTranscribeError(err instanceof Error ? err.message : "轉錄失敗，請重試");
      setTranscribeStage("error");
    } finally {
      setTranscribeSlow(false);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    e.target.value = ""; // Allow re-selecting same file

    const ext = file.name.split(".").pop()?.toLowerCase() ?? "";
    if (!["m4a", "mp3", "mp4", "wav"].includes(ext)) {
      setTranscribeError("不支援此格式，請上傳 m4a / mp3 / mp4 / wav");
      setTranscribeStage("error");
      return;
    }
    if (file.size > 25 * 1024 * 1024) {
      setTranscribeError("檔案過大，請壓縮後再試（上限 25 MB）");
      setTranscribeStage("error");
      return;
    }

    handleAudioUpload(file);
  };

  return (
    <div className="flex h-full">
      {/* Sidebar */}
      <div
        className={`${
          sidebarOpen ? "w-72" : "w-0"
        } transition-all duration-200 overflow-hidden border-r border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex flex-col shrink-0`}
      >
        {/* Sidebar header */}
        <div className="h-14 px-3 flex items-center justify-between border-b border-slate-200 dark:border-slate-800 shrink-0">
          <span className="text-sm font-semibold text-slate-900 dark:text-slate-50">情報紀錄</span>
          <button
            onClick={handleNewChat}
            className="p-1.5 rounded-lg text-slate-400 hover:text-blue-500 hover:bg-blue-500/10 cursor-pointer transition-colors"
            title="新對話"
          >
            <Plus size={18} />
          </button>
        </div>

        {/* Conversation list */}
        <div className="flex-1 overflow-auto py-1">
          {loadingList ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 size={16} className="animate-spin text-slate-400" />
            </div>
          ) : intels.length === 0 ? (
            <p className="text-xs text-slate-400 text-center py-8">尚無情報</p>
          ) : (
            intels.map((intel) => {
              const Icon = INPUT_ICONS[intel.input_type] || FileText;
              const isActive = activeIntel?.id === intel.id;
              return (
                <div
                  key={intel.id}
                  onClick={() => handleSelectIntel(intel)}
                  className={`group flex items-center gap-2 px-3 py-2.5 mx-1 rounded-lg cursor-pointer transition-colors ${
                    isActive
                      ? "bg-blue-500/10 text-blue-600 dark:text-blue-400"
                      : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
                  }`}
                >
                  <Icon size={14} className="shrink-0 opacity-50" />
                  <div className="flex-1 min-w-0">
                    <p className="text-xs truncate">
                      {getIntelDisplayTitle(intel, 40)}
                    </p>
                    <p className="text-[10px] opacity-50 mt-0.5">
                      {new Date(intel.created_at).toLocaleDateString("zh-TW")}
                      {intel.status === "confirmed" && " · 已確認"}
                    </p>
                  </div>
                  <button
                    onClick={(e) => handleDelete(e, intel.id)}
                    className="p-1 rounded opacity-0 group-hover:opacity-100 text-slate-400 hover:text-red-500 transition-all"
                  >
                    <Trash2 size={12} />
                  </button>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Main chat area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Chat header */}
        <div className="h-14 px-4 flex items-center justify-between border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shrink-0">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer transition-colors"
            >
              {sidebarOpen ? <PanelLeftClose size={18} /> : <PanelLeftOpen size={18} />}
            </button>
            {activeIntel ? (
              <h1 className="text-sm font-semibold text-slate-900 dark:text-slate-50 truncate">
                {activeIntel.title || getIntelDisplayTitle(activeIntel, 50)}
              </h1>
            ) : (
              <h1 className="text-sm font-semibold text-slate-900 dark:text-slate-50">
                新情報
              </h1>
            )}
          </div>
          {activeIntel && (
            <div className="flex items-center gap-1">
              <button
                onClick={handleOpenLinkDeal}
                className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-[11px] text-slate-400 hover:text-blue-500 hover:bg-blue-500/10 cursor-pointer transition-colors"
              >
                <Briefcase size={13} />
                商機 ({activeIntel.linked_deals?.length || 0})
              </button>
              <button
                onClick={() => setShowInfo(!showInfo)}
                className={`flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-[11px] cursor-pointer transition-colors ${
                  showInfo
                    ? "text-blue-500 bg-blue-500/10"
                    : "text-slate-400 hover:text-blue-500 hover:bg-blue-500/10"
                }`}
              >
                <Tag size={13} />
                分類
              </button>
            </div>
          )}
        </div>

        {/* Info panel (parsed data) */}
        {showInfo && parsed && Object.keys(parsed).length > 0 && (
          <div className="px-4 py-3 bg-slate-50 dark:bg-slate-800/50 border-b border-slate-200 dark:border-slate-800 overflow-auto max-h-40">
            <div className="flex flex-wrap gap-x-6 gap-y-1.5 max-w-2xl mx-auto">
              {Object.entries(parsed).map(([key, value]) => (
                <div key={key} className="flex items-center gap-1.5 text-xs">
                  <span className="text-slate-400">{FIELD_LABELS[key] || key}:</span>
                  <span className="text-slate-700 dark:text-slate-300 font-medium">
                    {formatValue(value)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Messages area */}
        <div className="flex-1 overflow-auto">
          {!activeIntel && messages.length === 0 ? (
            /* Empty state */
            <div className="flex flex-col items-center justify-center h-full px-4">
              <div className="w-14 h-14 rounded-2xl bg-cyan-500/10 flex items-center justify-center mb-4">
                <Sparkles size={28} className="text-cyan-500" />
              </div>
              <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-50 mb-1">
                有什麼情報要回報？
              </h2>
              <p className="text-sm text-slate-400 text-center max-w-sm">
                直接輸入拜訪筆記、客戶資訊、會議紀錄，AI 會自動分類並提問
              </p>
            </div>
          ) : (
            /* Chat messages */
            <div className="max-w-2xl mx-auto px-4 py-4 space-y-4">
              {messages.map((msg, i) => (
                <div
                  key={i}
                  className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  <div
                    className={`max-w-[85%] px-4 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
                      msg.role === "user"
                        ? "bg-blue-500 text-white rounded-br-md"
                        : "bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-50 rounded-bl-md"
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

        {/* Input area */}
        <div className="px-4 py-3 border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shrink-0">
          <div className="max-w-2xl mx-auto space-y-2">

            {/* Transcription progress bar */}
            {transcribeStage !== "idle" && (
              <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 px-4 py-2.5">
                {transcribeStage === "error" ? (
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-xs text-red-500">{transcribeError}</p>
                    <button
                      onClick={() => { setTranscribeStage("idle"); setTranscribeError(null); fileInputRef.current?.click(); }}
                      className="text-[11px] text-blue-500 hover:underline cursor-pointer shrink-0"
                    >
                      重試
                    </button>
                  </div>
                ) : transcribeStage === "done" ? (
                  <p className="text-xs text-emerald-500">✓ 轉錄完成</p>
                ) : (
                  <div className="space-y-1.5">
                    <div className="flex items-center gap-3">
                      {(["uploading", "transcribing", "parsing", "done"] as const).map((step) => {
                        const labels = { uploading: "上傳", transcribing: "轉錄", parsing: "解析", done: "完成" };
                        const steps = ["uploading", "transcribing", "parsing", "done"];
                        const current = steps.indexOf(transcribeStage);
                        const idx = steps.indexOf(step);
                        const isPast = idx < current;
                        const isActive = idx === current;
                        return (
                          <div key={step} className="flex items-center gap-1">
                            <span className={`text-[11px] font-medium ${isActive ? "text-blue-500" : isPast ? "text-emerald-500" : "text-slate-400"}`}>
                              {isPast ? "✓" : isActive ? <Loader2 size={10} className="animate-spin inline" /> : "○"}{" "}
                              {labels[step]}
                            </span>
                            {idx < 3 && <span className="text-slate-300 dark:text-slate-600 text-[10px]">›</span>}
                          </div>
                        );
                      })}
                    </div>
                    {transcribeSlow && (
                      <p className="text-[11px] text-slate-400">錄音較長，請稍候...</p>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* Text input row */}
            <div className="relative flex items-end gap-2">
              {/* Hidden file input */}
              <input
                ref={fileInputRef}
                type="file"
                accept=".m4a,.mp3,.mp4,.wav"
                className="hidden"
                onChange={handleFileSelect}
              />
              {/* Mic button — only for existing intel */}
              {activeIntel && (
                <button
                  onClick={() => fileInputRef.current?.click()}
                  disabled={transcribeStage !== "idle" && transcribeStage !== "error"}
                  title="上傳錄音（.m4a / .mp3 / .mp4 / .wav，最大 25 MB）"
                  className="p-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-400 hover:text-blue-500 hover:border-blue-400 disabled:opacity-30 cursor-pointer disabled:cursor-not-allowed transition-colors shrink-0"
                >
                  <Mic size={16} />
                </button>
              )}
              <div className="relative flex-1">
                <textarea
                  ref={inputRef}
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={activeIntel ? "繼續補充情報或回答問題..." : "輸入情報，例如：今天拜訪了 XX 公司，他們在找 AOI 方案..."}
                  rows={1}
                  className="w-full resize-none bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-3 pr-12 text-sm text-slate-900 dark:text-slate-50 placeholder:text-slate-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none min-h-[44px] max-h-32"
                  style={{ height: "auto" }}
                  onInput={(e) => {
                    const target = e.target as HTMLTextAreaElement;
                    target.style.height = "auto";
                    target.style.height = Math.min(target.scrollHeight, 128) + "px";
                  }}
                />
                <button
                  onClick={handleSend}
                  disabled={!inputText.trim() || sending}
                  className="absolute right-2 bottom-2 p-2 rounded-lg bg-blue-500 text-white disabled:opacity-30 cursor-pointer hover:bg-blue-600 transition-colors disabled:cursor-not-allowed"
                >
                  {sending ? (
                    <Loader2 size={16} className="animate-spin" />
                  ) : (
                    <Send size={16} />
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Link deal modal */}
      {showLinkDeal && (
        <div className="fixed inset-0 bg-slate-950/50 flex items-end md:items-center justify-center z-50">
          <div className="bg-white dark:bg-slate-900 rounded-t-2xl md:rounded-xl p-6 w-full max-w-md mx-auto space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold text-slate-900 dark:text-slate-50">
                關聯到商機
              </h3>
              <button
                onClick={() => setShowLinkDeal(false)}
                className="p-1.5 text-slate-400 hover:text-slate-200 cursor-pointer transition-colors"
              >
                <X size={20} />
              </button>
            </div>
            <div className="max-h-72 overflow-auto divide-y divide-slate-100 dark:divide-slate-800">
              {allDeals.length === 0 ? (
                <p className="text-sm text-slate-400 py-4 text-center">載入中...</p>
              ) : (
                allDeals
                  .filter((d) => !linkedDealIds.has(d.id))
                  .map((d) => (
                    <button
                      key={d.id}
                      onClick={() => handleLinkDeal(d.id)}
                      disabled={linking}
                      className="w-full flex items-center justify-between py-3 px-1 hover:bg-slate-50 dark:hover:bg-slate-800/50 rounded transition-colors cursor-pointer disabled:opacity-50 text-left"
                    >
                      <div>
                        <span className="text-sm text-slate-900 dark:text-slate-50">{d.name}</span>
                        <span className="text-[11px] text-slate-400 ml-2">{d.client_name}</span>
                      </div>
                      <span className="text-[11px] px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400">
                        {d.stage}
                      </span>
                    </button>
                  ))
              )}
              {allDeals.length > 0 && allDeals.filter((d) => !linkedDealIds.has(d.id)).length === 0 && (
                <p className="text-sm text-slate-400 py-4 text-center">所有商機已關聯</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
