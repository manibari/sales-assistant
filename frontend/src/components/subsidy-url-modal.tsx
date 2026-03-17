"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Globe, Loader2, X, Check, AlertCircle } from "lucide-react";
import { nxApi } from "@/lib/nexus-api";

interface ParsedSubsidy {
  name: string;
  agency: string;
  deadline: string;
  deadline_date: string | null;
  funding_amount: string;
  eligibility: string;
  scope: string;
  reference_url: string;
}

export function SubsidyUrlModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const router = useRouter();
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [parsed, setParsed] = useState<ParsedSubsidy | null>(null);
  const [saving, setSaving] = useState(false);

  const handleParse = async () => {
    if (!url.trim()) return;
    setLoading(true);
    setError("");
    setParsed(null);
    try {
      const result = await nxApi.subsidies.parseUrl(url.trim());
      if (!result.name) {
        setError("無法從網頁中擷取補助計畫名稱，請改用手動新增。");
        return;
      }
      setParsed(result);
    } catch {
      setError("網頁擷取失敗，可能被封鎖或格式不支援。");
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    if (!parsed) return;
    setSaving(true);
    try {
      const subsidy = await nxApi.subsidies.create({
        name: parsed.name,
        program_type: "other",
        agency: parsed.agency || undefined,
        deadline: parsed.deadline || undefined,
        funding_amount: parsed.funding_amount || undefined,
        eligibility: parsed.eligibility || undefined,
        scope: parsed.scope || undefined,
        reference_url: parsed.reference_url || undefined,
      });
      onClose();
      router.push(`/subsidies/${subsidy.id}`);
    } catch {
      setError("建立失敗");
      setSaving(false);
    }
  };

  const handleClose = () => {
    setUrl("");
    setParsed(null);
    setError("");
    setLoading(false);
    onClose();
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center">
      <div className="absolute inset-0 bg-black/40" onClick={handleClose} />
      <div className="relative w-full sm:max-w-lg bg-white dark:bg-slate-900 rounded-t-2xl sm:rounded-2xl border border-slate-200 dark:border-slate-700 shadow-xl max-h-[85vh] overflow-auto">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-200 dark:border-slate-700">
          <div className="flex items-center gap-2">
            <Globe size={18} className="text-blue-500" />
            <h2 className="text-base font-semibold text-slate-900 dark:text-slate-50">從網址匯入補助案</h2>
          </div>
          <button onClick={handleClose} className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer transition-colors">
            <X size={18} className="text-slate-400" />
          </button>
        </div>

        <div className="px-5 py-4 space-y-4">
          {/* URL input */}
          <div className="flex gap-2">
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleParse()}
              placeholder="貼上補助計畫網址..."
              autoFocus
              className="flex-1 bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-4 py-2.5 text-sm text-slate-900 dark:text-slate-50 placeholder:text-slate-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none transition-colors"
            />
            <button
              onClick={handleParse}
              disabled={!url.trim() || loading}
              className="px-4 py-2.5 bg-blue-500 hover:bg-blue-600 disabled:opacity-50 text-white text-sm font-medium rounded-lg transition-colors cursor-pointer disabled:cursor-not-allowed flex items-center gap-1.5"
            >
              {loading ? <Loader2 size={16} className="animate-spin" /> : "擷取"}
            </button>
          </div>

          {/* Error */}
          {error && (
            <div className="flex items-center gap-2 text-sm text-red-500 bg-red-500/10 rounded-lg px-3 py-2">
              <AlertCircle size={16} />
              {error}
            </div>
          )}

          {/* Preview */}
          {parsed && (
            <div className="space-y-3">
              <div className="bg-slate-50 dark:bg-slate-800/50 rounded-xl p-4 space-y-2.5 border border-slate-200 dark:border-slate-700">
                <PreviewField label="計畫名稱" value={parsed.name} highlight />
                <PreviewField label="主辦機關" value={parsed.agency} />
                <PreviewField label="申請截止" value={parsed.deadline || parsed.deadline_date || ""} />
                <PreviewField label="補助額度" value={parsed.funding_amount} />
                <PreviewField label="申請資格" value={parsed.eligibility} />
                <PreviewField label="補助範圍" value={parsed.scope} />
              </div>

              <p className="text-xs text-slate-400">
                自動擷取結果可能不完整，建立後可手動編輯補充。
              </p>

              <button
                onClick={handleCreate}
                disabled={saving}
                className="w-full flex items-center justify-center gap-2 bg-blue-500 hover:bg-blue-600 disabled:opacity-50 text-white font-semibold px-6 py-3 rounded-lg active:scale-[0.98] transition-all cursor-pointer"
              >
                {saving ? <Loader2 size={18} className="animate-spin" /> : <><Check size={18} />建立補助案</>}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function PreviewField({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  if (!value) return null;
  return (
    <div>
      <span className="text-[11px] font-medium text-slate-400 dark:text-slate-500">{label}</span>
      <p className={`text-sm mt-0.5 ${highlight ? "font-semibold text-slate-900 dark:text-slate-50" : "text-slate-700 dark:text-slate-300"} line-clamp-3`}>
        {value}
      </p>
    </div>
  );
}
