"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { TopBar } from "@/components/top-bar";
import {
  ChevronLeft,
  FileText,
  Camera,
  Mic,
  Tag,
  Loader2,
  Paperclip,
  Briefcase,
  Plus,
  X,
  ExternalLink,
  Download,
} from "lucide-react";
import { nxApi, type NxIntel, type NxDeal } from "@/lib/nexus-api";
import { getIntelDisplayTitle } from "@/lib/intel-display";

const INPUT_ICONS: Record<string, typeof FileText> = {
  text: FileText,
  photo: Camera,
  voice: Mic,
};

const INPUT_LABELS: Record<string, string> = {
  text: "文字輸入",
  photo: "拍照",
  voice: "語音",
};

const STAGE_LABELS: Record<string, string> = {
  L0: "L0 潛在",
  L1: "L1 接觸中",
  L2: "L2 需求確認",
  L3: "L3 報價",
  L4: "L4 簽約",
  closed: "已關閉",
};

/** Human-readable labels for parsed_json keys */
const FIELD_LABELS: Record<string, string> = {
  role: "角色",
  industry: "產業",
  pain_points: "痛點",
  nda_status: "NDA 狀態",
  mou_status: "MOU 狀態",
  budget: "預估預算",
  capabilities: "能力標籤",
  industry_exp: "產業經驗",
  team_size: "團隊規模",
  subsidy_partner: "預計合作夥伴",
  subsidy_deadline: "補助截止日期",
};

const VALUE_LABELS: Record<string, string> = {
  client: "客戶",
  partner: "夥伴",
  si: "SI",
  subsidy: "政府補貼",
  other: "其他",
  food: "食品業",
  petrochemical: "石化業",
  semiconductor: "半導體",
  manufacturing: "製造業",
  automation: "產線自動化",
  aoi: "品質檢測 (AOI)",
  energy: "能源管理",
  safety: "安全監控",
  erp: "ERP/系統整合",
  iot: "IoT 資料收集",
  vision: "影像辨識",
  auto_ctrl: "自動控制",
  security: "資安",
  ml_ai: "ML/AI",
  pending: "尚未開始",
  in_progress: "進行中",
  signed: "已簽署",
  not_required: "不需要",
  unknown: "未知",
};

function formatValue(value: string | string[]): string {
  if (Array.isArray(value)) {
    return value.map((v) => VALUE_LABELS[v] || v).join("、");
  }
  return VALUE_LABELS[value] || value;
}

export default function IntelDetailPage() {
  const params = useParams();
  const intelId = Number(params.id);
  const [intel, setIntel] = useState<NxIntel | null>(null);
  const [loading, setLoading] = useState(true);
  const [titleDraft, setTitleDraft] = useState("");
  const [savingTitle, setSavingTitle] = useState(false);
  const [showLinkDeal, setShowLinkDeal] = useState(false);
  const [allDeals, setAllDeals] = useState<NxDeal[]>([]);
  const [linking, setLinking] = useState(false);

  const loadIntel = useCallback(() => {
    nxApi.intel
      .get(intelId)
      .then((data) => {
        setIntel(data);
        setTitleDraft(data.title || "");
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [intelId]);

  useEffect(() => {
    loadIntel();
  }, [loadIntel]);

  const handleOpenLinkDeal = async () => {
    setShowLinkDeal(true);
    try {
      const deals = await nxApi.deals.list("urgency");
      setAllDeals(deals);
    } catch (err) {
      console.error("Failed to load deals:", err);
    }
  };

  const handleLinkDeal = async (dealId: number) => {
    setLinking(true);
    try {
      await nxApi.deals.linkIntel(dealId, intelId);
      setShowLinkDeal(false);
      loadIntel();
    } catch (err) {
      console.error("Failed to link deal:", err);
    } finally {
      setLinking(false);
    }
  };

  const handleSaveTitle = async () => {
    setSavingTitle(true);
    try {
      const updated = await nxApi.intel.update(intelId, {
        title: titleDraft.trim() || null,
      });
      setIntel(updated);
      setTitleDraft(updated.title || "");
    } catch (err) {
      console.error("Failed to save intel title:", err);
      alert("標題儲存失敗");
    } finally {
      setSavingTitle(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 size={24} className="animate-spin text-blue-500" />
      </div>
    );
  }

  if (!intel) {
    return (
      <div className="flex flex-col h-full">
        <TopBar title="情報詳情">
          <Link
            href="/intel"
            className="p-2 rounded-lg text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer transition-colors"
          >
            <ChevronLeft size={20} />
          </Link>
        </TopBar>
        <div className="flex-1 flex items-center justify-center text-slate-400 text-sm">
          找不到這筆情報
        </div>
      </div>
    );
  }

  const Icon = INPUT_ICONS[intel.input_type] || FileText;
  const isConfirmed = intel.status === "confirmed";

  let parsed: Record<string, string | string[]> | null = null;
  if (intel.parsed_json) {
    try {
      parsed = JSON.parse(intel.parsed_json);
    } catch {
      // ignore
    }
  }

  const linkedDealIds = new Set((intel.linked_deals || []).map((d) => d.id));
  const savedTitle = intel.title?.trim() || "";
  const titleChanged = titleDraft.trim() !== savedTitle;

  return (
    <div className="flex flex-col h-full">
      <TopBar title="情報詳情">
        <Link
          href="/intel"
          className="p-2 rounded-lg text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer transition-colors"
        >
          <ChevronLeft size={20} />
        </Link>
      </TopBar>

      <div className="flex-1 px-4 py-4 overflow-auto max-w-2xl lg:max-w-4xl mx-auto w-full space-y-4">
        {/* Meta info */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-cyan-500/10 flex items-center justify-center flex-shrink-0">
            <Icon size={16} className="text-cyan-500" />
          </div>
          <div className="flex items-center gap-2 flex-1">
            <span className="text-xs text-slate-400">
              {INPUT_LABELS[intel.input_type] || intel.input_type}
            </span>
            <span className="text-xs text-slate-400">·</span>
            <span className="text-xs text-slate-400">
              {new Date(intel.created_at).toLocaleString("zh-TW")}
            </span>
          </div>
          <span
            className={`text-[11px] px-2 py-0.5 rounded-full font-medium ${
              isConfirmed
                ? "bg-green-500/10 text-green-400"
                : "bg-amber-500/10 text-amber-400"
            }`}
          >
            {isConfirmed ? "已確認" : "草稿"}
          </span>
        </div>

        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4">
          <div className="flex items-center justify-between gap-3 mb-2">
            <div>
              <p className="text-xs font-medium text-slate-400">情報標題</p>
              <p className="text-[11px] text-slate-400 mt-1">
                留空則沿用原始輸入。相關情報、搜尋與商機關聯會優先顯示這個標題。
              </p>
            </div>
            <button
              onClick={handleSaveTitle}
              disabled={!titleChanged || savingTitle}
              className="px-3 py-1.5 rounded-lg bg-blue-500 text-white text-xs font-medium disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
            >
              {savingTitle ? "儲存中..." : "儲存"}
            </button>
          </div>
          <input
            type="text"
            value={titleDraft}
            onChange={(e) => setTitleDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && titleChanged && !savingTitle) {
                e.preventDefault();
                void handleSaveTitle();
              }
            }}
            placeholder={getIntelDisplayTitle(intel, 80)}
            className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-3 py-2.5 text-sm text-slate-900 dark:text-slate-50 placeholder:text-slate-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
          />
        </div>

        {/* Raw input */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4">
          <p className="text-xs font-medium text-slate-400 mb-2">原始輸入</p>
          <p className="text-sm text-slate-900 dark:text-slate-50 whitespace-pre-wrap leading-relaxed">
            {intel.raw_input}
          </p>
        </div>

        {/* Attached files */}
        {intel.files && intel.files.length > 0 && (
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-3">
              <Paperclip size={16} className="text-blue-500" />
              <span className="text-sm font-semibold text-slate-900 dark:text-slate-50">
                附件
              </span>
              <span className="text-xs text-slate-400">({intel.files.length})</span>
            </div>
            <div className="divide-y divide-slate-100 dark:divide-slate-800">
              {intel.files.map((f) => {
                const isExternal = !!f.source_url;
                const isLocal = !isExternal && f.file_path && !f.file_path.startsWith("link://");
                const statusBadge = f.parse_status === "parsed"
                  ? { label: "已解析", cls: "bg-green-500/10 text-green-400" }
                  : f.parse_status === "failed"
                    ? { label: "解析失敗", cls: "bg-red-500/10 text-red-400" }
                    : isExternal
                      ? { label: "外部連結", cls: "bg-blue-500/10 text-blue-400" }
                      : { label: "已上傳", cls: "bg-slate-500/10 text-slate-400" };
                const href = isExternal
                  ? f.source_url!
                  : `/api/nx/documents/files/${f.id}/download`;
                return (
                  <div key={f.id} className="flex items-center justify-between py-2">
                    <div className="flex-1 min-w-0">
                      <a
                        href={href}
                        target={isExternal ? "_blank" : "_self"}
                        rel={isExternal ? "noopener noreferrer" : undefined}
                        className="text-sm text-blue-500 hover:text-blue-400 hover:underline truncate flex items-center gap-1"
                      >
                        {f.file_name}
                        {isExternal ? <ExternalLink size={12} /> : isLocal ? <Download size={12} /> : null}
                      </a>
                      {f.file_size && (
                        <span className="text-[11px] text-slate-400">
                          {(f.file_size / 1024 / 1024).toFixed(1)} MB
                        </span>
                      )}
                    </div>
                    <span className={`text-[11px] px-2 py-0.5 rounded-full ${statusBadge.cls}`}>
                      {statusBadge.label}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Parsed classification */}
        {parsed && Object.keys(parsed).length > 0 ? (
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-3">
              <Tag size={16} className="text-blue-500" />
              <span className="text-sm font-semibold text-slate-900 dark:text-slate-50">
                分類結果
              </span>
            </div>
            <div className="space-y-2">
              {Object.entries(parsed).map(([key, value]) => (
                <div key={key} className="flex items-start gap-3 py-1">
                  <span className="text-xs text-slate-400 w-24 flex-shrink-0 pt-0.5 text-right">
                    {FIELD_LABELS[key] || key}
                  </span>
                  <span className="text-sm text-slate-700 dark:text-slate-300">
                    {formatValue(value)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <Tag size={16} className="text-slate-400" />
              <span className="text-sm font-semibold text-slate-900 dark:text-slate-50">
                分類結果
              </span>
            </div>
            <p className="text-xs text-slate-400">
              尚未分類 — 從情報 Feed 進入問答流程即可分類
            </p>
          </div>
        )}

        {/* Chat history */}
        {intel.chat_history && (() => {
          let chatMsgs: { role: string; text: string }[] = [];
          try {
            chatMsgs = JSON.parse(intel.chat_history);
          } catch { /* ignore */ }
          return chatMsgs.length > 0 ? (
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4">
              <details>
                <summary className="flex items-center gap-2 cursor-pointer">
                  <FileText size={16} className="text-cyan-500" />
                  <span className="text-sm font-semibold text-slate-900 dark:text-slate-50">
                    對話記錄
                  </span>
                  <span className="text-xs text-slate-400">({chatMsgs.length} 則)</span>
                </summary>
                <div className="mt-3 space-y-2.5 max-h-80 overflow-auto">
                  {chatMsgs.map((msg, idx) => (
                    <div
                      key={idx}
                      className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                    >
                      <div
                        className={`max-w-[85%] px-3 py-2 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
                          msg.role === "user"
                            ? "bg-blue-500 text-white rounded-br-md"
                            : "bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-50 rounded-bl-md"
                        }`}
                      >
                        {msg.text}
                      </div>
                    </div>
                  ))}
                </div>
              </details>
            </div>
          ) : null;
        })()}

        {/* Linked deals */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Briefcase size={16} className="text-blue-500" />
              <span className="text-sm font-semibold text-slate-900 dark:text-slate-50">
                關聯商機
              </span>
              <span className="text-xs text-slate-400">
                ({intel.linked_deals?.length || 0})
              </span>
            </div>
            <button
              onClick={handleOpenLinkDeal}
              className="text-xs text-blue-500 cursor-pointer flex items-center gap-0.5"
            >
              <Plus size={12} /> 關聯
            </button>
          </div>
          <div className="divide-y divide-slate-100 dark:divide-slate-800">
            {intel.linked_deals && intel.linked_deals.length > 0 ? (
              intel.linked_deals.map((d) => (
                <Link
                  key={d.id}
                  href={`/deals/${d.id}`}
                  className="flex items-center justify-between py-2 hover:bg-slate-50 dark:hover:bg-slate-800/50 -mx-1 px-1 rounded transition-colors"
                >
                  <div>
                    <span className="text-sm text-slate-700 dark:text-slate-300">
                      {d.name}
                    </span>
                    <span className="text-[11px] text-slate-400 ml-2">
                      {d.client_name}
                    </span>
                  </div>
                  <span
                    className={`text-[11px] px-2 py-0.5 rounded-full font-medium ${
                      d.status === "closed"
                        ? "bg-slate-700 text-slate-400"
                        : "bg-blue-500/10 text-blue-400"
                    }`}
                  >
                    {STAGE_LABELS[d.stage] || d.stage}
                  </span>
                </Link>
              ))
            ) : (
              <p className="text-xs text-slate-400 py-2">
                尚未關聯任何商機
              </p>
            )}
          </div>
        </div>

        {/* Action: go to Q&A if not confirmed */}
        {!isConfirmed && (
          <Link
            href={`/capture/qa?id=${intel.id}`}
            className="block w-full bg-blue-500 hover:bg-blue-600 text-white font-semibold px-6 py-3 rounded-lg min-h-[44px] text-center active:scale-[0.98] transition-all cursor-pointer"
          >
            開始分類問答
          </Link>
        )}
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
                        <span className="text-sm text-slate-900 dark:text-slate-50">
                          {d.name}
                        </span>
                        <span className="text-[11px] text-slate-400 ml-2">
                          {d.client_name}
                        </span>
                      </div>
                      <span className="text-[11px] px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400">
                        {STAGE_LABELS[d.stage] || d.stage}
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
