"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { TopBar } from "@/components/top-bar";
import {
  ChevronLeft,
  ChevronUp,
  ChevronDown,
  Check,
  X,
  AlertTriangle,
  Handshake,
  Zap,
  CircleDot,
  FileCheck,
  Calendar,
  Loader2,
} from "lucide-react";
import { nxApi, type NxDeal, type MeddicProgress } from "@/lib/nexus-api";
import Link from "next/link";

const STAGE_ORDER = ["L0", "L1", "L2", "L3", "L4"];
const STAGE_LABELS: Record<string, string> = {
  L0: "L0 潛在",
  L1: "L1 接觸中",
  L2: "L2 需求確認",
  L3: "L3 報價",
  L4: "L4 簽約",
  closed: "已關閉",
};

const MEDDIC_LABELS: Record<string, string> = {
  metrics: "Metrics (量化指標)",
  economic_buyer: "Economic Buyer (經濟決策者)",
  decision_criteria: "Decision Criteria (決策標準)",
  decision_process: "Decision Process (決策流程)",
  identify_pain: "Identify Pain (痛點辨識)",
  champion: "Champion (內部擁護者)",
};

const CLOSE_REASONS = [
  { label: "預算不足", value: "budget" },
  { label: "時程不合", value: "timing" },
  { label: "選擇競品", value: "competitor" },
  { label: "需求消失", value: "no_need" },
  { label: "其他", value: "other" },
];

export default function DealDetailPage() {
  const params = useParams();
  const router = useRouter();
  const dealId = Number(params.id);

  const [deal, setDeal] = useState<NxDeal | null>(null);
  const [loading, setLoading] = useState(true);
  const [meddicOpen, setMeddicOpen] = useState(false);
  const [editingMeddic, setEditingMeddic] = useState<string | null>(null);
  const [meddicValue, setMeddicValue] = useState("");
  const [showCloseModal, setShowCloseModal] = useState(false);
  const [closeReason, setCloseReason] = useState("");
  const [closeNotes, setCloseNotes] = useState("");
  const [advancing, setAdvancing] = useState(false);

  const loadDeal = useCallback(() => {
    nxApi.deals
      .get(dealId)
      .then(setDeal)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [dealId]);

  useEffect(() => {
    loadDeal();
  }, [loadDeal]);

  const handleAdvance = async () => {
    if (!deal) return;
    const currentIdx = STAGE_ORDER.indexOf(deal.stage);
    if (currentIdx < 0 || currentIdx >= STAGE_ORDER.length - 1) return;

    // Check MEDDIC gate
    const progress = deal.meddic_progress;
    if (progress && progress.missing.length > 0 && currentIdx >= 1) {
      alert(`需先完成 MEDDIC：${progress.missing.join(", ")}`);
      setMeddicOpen(true);
      return;
    }

    setAdvancing(true);
    try {
      const nextStage = STAGE_ORDER[currentIdx + 1];
      await nxApi.deals.advance(dealId, nextStage);
      loadDeal();
    } catch (err) {
      console.error("Failed to advance:", err);
    } finally {
      setAdvancing(false);
    }
  };

  const handleClose = async () => {
    if (!closeReason) return;
    try {
      await nxApi.deals.close(dealId, closeReason, closeNotes || undefined);
      setShowCloseModal(false);
      loadDeal();
    } catch (err) {
      console.error("Failed to close:", err);
    }
  };

  const handleMeddicSave = async (key: string) => {
    if (!deal) return;
    const current = deal.meddic_json ? JSON.parse(deal.meddic_json) : {};
    current[key] = meddicValue;
    try {
      await nxApi.deals.update(dealId, { meddic_json: JSON.stringify(current) } as Partial<NxDeal>);
      setEditingMeddic(null);
      setMeddicValue("");
      loadDeal();
    } catch (err) {
      console.error("Failed to save MEDDIC:", err);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 size={24} className="animate-spin text-blue-500" />
      </div>
    );
  }

  if (!deal) {
    return (
      <div className="flex flex-col h-full">
        <TopBar title="商機詳情" />
        <div className="flex-1 flex items-center justify-center text-slate-500">找不到此商機</div>
      </div>
    );
  }

  const meddic: Record<string, string | null> = deal.meddic_json
    ? JSON.parse(deal.meddic_json)
    : {};
  const progress: MeddicProgress = deal.meddic_progress || {
    completed: 0,
    total: 6,
    missing: [],
  };
  const isClosed = deal.status === "closed";

  return (
    <div className="flex flex-col h-full">
      <TopBar title={deal.name}>
        <Link
          href="/deals"
          className="p-2 rounded-lg text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer transition-colors"
        >
          <ChevronLeft size={20} />
        </Link>
      </TopBar>

      <div className="flex-1 px-4 py-4 overflow-auto max-w-2xl mx-auto w-full space-y-4">
        {/* Header card */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-5">
          <div className="flex items-center justify-between mb-3">
            <span
              className={`text-xs px-2.5 py-1 rounded-full font-medium ${
                isClosed
                  ? "bg-slate-700 text-slate-400"
                  : "bg-blue-500/10 text-blue-400"
              }`}
            >
              {STAGE_LABELS[deal.stage] || deal.stage}
            </span>
            {deal.idle_days !== undefined && deal.idle_days > 0 && !isClosed && (
              <span
                className={`text-[11px] flex items-center gap-1 ${
                  deal.idle_days > 14 ? "text-red-400" : "text-slate-400"
                }`}
              >
                {deal.idle_days > 14 && <AlertTriangle size={12} />}
                {deal.idle_days} 天未動
              </span>
            )}
          </div>
          <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-50">
            {deal.name}
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            {deal.client_name} · {deal.client_industry || "—"}
          </p>
          <div className="flex gap-4 mt-3 text-xs text-slate-400 dark:text-slate-500">
            {deal.budget_range && <span>預算: {deal.budget_range}</span>}
            {deal.timeline && <span>時程: {deal.timeline}</span>}
          </div>

          {/* Stage actions */}
          {!isClosed && (
            <div className="flex gap-2 mt-4">
              <button
                onClick={handleAdvance}
                disabled={advancing}
                className="flex-1 bg-blue-500 hover:bg-blue-600 text-white font-semibold px-4 py-2.5 rounded-lg text-sm min-h-[44px] active:scale-[0.98] transition-all cursor-pointer disabled:opacity-50"
              >
                {advancing ? "推進中..." : "推進階段"}
              </button>
              <button
                onClick={() => setShowCloseModal(true)}
                className="px-4 py-2.5 rounded-lg text-sm font-medium bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 min-h-[44px] cursor-pointer transition-colors"
              >
                關閉
              </button>
            </div>
          )}
        </div>

        {/* MEDDIC Progress */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl overflow-hidden">
          <button
            onClick={() => setMeddicOpen(!meddicOpen)}
            className="w-full flex items-center justify-between p-4 cursor-pointer"
          >
            <div className="flex items-center gap-3">
              <span className="text-sm font-semibold text-slate-900 dark:text-slate-50">
                MEDDIC 進度
              </span>
              <span className="text-xs text-slate-400">
                {progress.completed}/{progress.total}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-20 h-1.5 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-green-500 rounded-full transition-all"
                  style={{
                    width: `${(progress.completed / progress.total) * 100}%`,
                  }}
                />
              </div>
              {meddicOpen ? (
                <ChevronUp size={16} className="text-slate-400" />
              ) : (
                <ChevronDown size={16} className="text-slate-400" />
              )}
            </div>
          </button>
          {meddicOpen && (
            <div className="border-t border-slate-200 dark:border-slate-700 divide-y divide-slate-200 dark:divide-slate-700">
              {Object.entries(MEDDIC_LABELS).map(([key, label]) => {
                const value = meddic[key];
                const isEditing = editingMeddic === key;
                return (
                  <div key={key} className="px-4 py-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {value ? (
                          <Check size={14} className="text-green-500" />
                        ) : (
                          <CircleDot size={14} className="text-slate-400" />
                        )}
                        <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
                          {label}
                        </span>
                      </div>
                      {!isEditing && !isClosed && (
                        <button
                          onClick={() => {
                            setEditingMeddic(key);
                            setMeddicValue(value || "");
                          }}
                          className="text-xs text-blue-500 cursor-pointer"
                        >
                          {value ? "編輯" : "填寫"}
                        </button>
                      )}
                    </div>
                    {value && !isEditing && (
                      <p className="text-sm text-slate-700 dark:text-slate-300 mt-1 ml-6">
                        {value}
                      </p>
                    )}
                    {isEditing && (
                      <div className="mt-2 ml-6 flex gap-2">
                        <input
                          type="text"
                          value={meddicValue}
                          onChange={(e) => setMeddicValue(e.target.value)}
                          className="flex-1 bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-900 dark:text-slate-50 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
                          placeholder="輸入內容..."
                          autoFocus
                        />
                        <button
                          onClick={() => handleMeddicSave(key)}
                          className="p-2 bg-blue-500 text-white rounded-lg cursor-pointer"
                        >
                          <Check size={16} />
                        </button>
                        <button
                          onClick={() => setEditingMeddic(null)}
                          className="p-2 bg-slate-200 dark:bg-slate-700 rounded-lg cursor-pointer"
                        >
                          <X size={16} />
                        </button>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Partners */}
        <Section
          title="搭配夥伴"
          icon={<Handshake size={16} className="text-green-500" />}
          count={deal.partners?.length}
        >
          {deal.partners && deal.partners.length > 0 ? (
            deal.partners.map((p) => (
              <div
                key={p.id}
                className="flex items-center justify-between py-2"
              >
                <div>
                  <span className="text-sm text-slate-900 dark:text-slate-50">
                    {p.partner_name}
                  </span>
                  {p.role && (
                    <span className="text-xs text-slate-400 ml-2">({p.role})</span>
                  )}
                </div>
                <span className="text-[11px] px-2 py-0.5 rounded-full bg-green-500/10 text-green-400">
                  {p.trust_level}
                </span>
              </div>
            ))
          ) : (
            <p className="text-xs text-slate-400">尚無配對夥伴</p>
          )}
        </Section>

        {/* Related Intel */}
        <Section
          title="相關情報"
          icon={<Zap size={16} className="text-cyan-500" />}
          count={deal.intel?.length}
        >
          {deal.intel && deal.intel.length > 0 ? (
            deal.intel.map((i: { id: number; raw_input: string; intel_created_at?: string }) => (
              <div key={i.id} className="py-2">
                <p className="text-sm text-slate-700 dark:text-slate-300 line-clamp-2">
                  {i.raw_input}
                </p>
                <span className="text-[11px] text-slate-400 mt-1">
                  {i.intel_created_at
                    ? new Date(i.intel_created_at).toLocaleDateString("zh-TW")
                    : ""}
                </span>
              </div>
            ))
          ) : (
            <p className="text-xs text-slate-400">尚無關聯情報</p>
          )}
        </Section>

        {/* TBDs */}
        <Section
          title="TBD 清單"
          icon={<CircleDot size={16} className="text-amber-500" />}
          count={deal.tbds?.length}
        >
          {deal.tbds && deal.tbds.length > 0 ? (
            deal.tbds.map((t) => (
              <div
                key={t.id}
                className="flex items-center justify-between py-2"
              >
                <span className="text-sm text-slate-700 dark:text-slate-300">
                  {t.question}
                </span>
                <button
                  onClick={async () => {
                    await nxApi.tbd.resolve(t.id);
                    loadDeal();
                  }}
                  className="text-xs text-green-500 cursor-pointer"
                >
                  解決
                </button>
              </div>
            ))
          ) : (
            <p className="text-xs text-slate-400">無待確認事項</p>
          )}
        </Section>

        {/* Files */}
        <Section
          title="文件"
          icon={<FileCheck size={16} className="text-blue-500" />}
          count={deal.files?.length}
        >
          {deal.files && deal.files.length > 0 ? (
            deal.files.map((f) => (
              <div
                key={f.id}
                className="flex items-center justify-between py-2"
              >
                <span className="text-sm text-slate-700 dark:text-slate-300">
                  {f.file_name}
                </span>
                <span
                  className={`text-[11px] px-2 py-0.5 rounded-full ${
                    f.parse_status === "parsed"
                      ? "bg-green-500/10 text-green-400"
                      : "bg-slate-700 text-slate-400"
                  }`}
                >
                  {f.parse_status === "parsed" ? "已解析" : f.parse_status}
                </span>
              </div>
            ))
          ) : (
            <p className="text-xs text-slate-400">尚無文件</p>
          )}
        </Section>

        {/* Next action */}
        {!isClosed && (
          <Link
            href={`/calendar`}
            className="flex items-center gap-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4 cursor-pointer hover:border-slate-300 dark:hover:border-slate-600 transition-colors"
          >
            <Calendar size={20} className="text-blue-500" />
            <span className="text-sm font-medium text-slate-900 dark:text-slate-50">
              排下次會議
            </span>
          </Link>
        )}
      </div>

      {/* Close modal */}
      {showCloseModal && (
        <div className="fixed inset-0 bg-slate-950/50 flex items-end md:items-center justify-center z-50">
          <div className="bg-white dark:bg-slate-900 rounded-t-2xl md:rounded-xl p-6 w-full max-w-md mx-auto space-y-4">
            <h3 className="text-lg font-bold text-slate-900 dark:text-slate-50">
              關閉商機
            </h3>
            <p className="text-sm text-slate-500">選擇關閉原因：</p>
            <div className="grid grid-cols-2 gap-2">
              {CLOSE_REASONS.map((r) => (
                <button
                  key={r.value}
                  onClick={() => setCloseReason(r.value)}
                  className={`min-h-[44px] px-3 py-2 text-sm font-medium rounded-lg border transition-colors cursor-pointer ${
                    closeReason === r.value
                      ? "border-red-500 bg-red-500/10 text-red-400"
                      : "bg-slate-100 dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200"
                  }`}
                >
                  {r.label}
                </button>
              ))}
            </div>
            <textarea
              value={closeNotes}
              onChange={(e) => setCloseNotes(e.target.value)}
              placeholder="備註 (optional)"
              className="w-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-4 py-3 text-sm text-slate-900 dark:text-slate-50 placeholder:text-slate-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none resize-none h-20"
            />
            <div className="flex gap-2">
              <button
                onClick={() => setShowCloseModal(false)}
                className="flex-1 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-700 font-medium px-4 py-3 rounded-lg min-h-[44px] cursor-pointer transition-colors"
              >
                取消
              </button>
              <button
                onClick={handleClose}
                disabled={!closeReason}
                className="flex-1 bg-red-500 hover:bg-red-600 disabled:opacity-50 text-white font-semibold px-4 py-3 rounded-lg min-h-[44px] cursor-pointer transition-all"
              >
                確定關閉
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function Section({
  title,
  icon,
  count,
  children,
}: {
  title: string;
  icon: React.ReactNode;
  count?: number;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4">
      <div className="flex items-center gap-2 mb-3">
        {icon}
        <span className="text-sm font-semibold text-slate-900 dark:text-slate-50">
          {title}
        </span>
        {count !== undefined && (
          <span className="text-xs text-slate-400">({count})</span>
        )}
      </div>
      <div className="divide-y divide-slate-100 dark:divide-slate-800">
        {children}
      </div>
    </div>
  );
}
