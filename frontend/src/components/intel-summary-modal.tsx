"use client";

import { useState, useEffect } from "react";
import { X, Loader2, Copy, Check, Save } from "lucide-react";
import { nxApi } from "@/lib/nexus-api";

interface IntelSummaryModalProps {
  intelIds: number[];
  onClose: () => void;
  onSaveAsIntel?: (summary: string) => void;
}

export function IntelSummaryModal({ intelIds, onClose, onSaveAsIntel }: IntelSummaryModalProps) {
  const [summary, setSummary] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    nxApi.intel
      .summarize(intelIds)
      .then((res) => setSummary(res.summary))
      .catch((err) => setError(err.message || "AI 彙整失敗"))
      .finally(() => setLoading(false));
  }, [intelIds]);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(summary);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSave = async () => {
    if (!onSaveAsIntel || saving) return;
    setSaving(true);
    try {
      await onSaveAsIntel(summary);
      onClose();
    } catch {
      setError("儲存失敗");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white dark:bg-slate-900 rounded-xl w-full max-w-2xl max-h-[80vh] flex flex-col shadow-xl">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-slate-200 dark:border-slate-700">
          <div>
            <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-50">
              情報彙整
            </h3>
            <p className="text-[11px] text-slate-400 mt-0.5">
              {loading ? "AI 分析中..." : `已彙整 ${intelIds.length} 筆情報`}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-auto px-4 py-4">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-12 gap-3">
              <Loader2 size={24} className="animate-spin text-cyan-500" />
              <p className="text-sm text-slate-400">AI 正在分析 {intelIds.length} 筆情報...</p>
            </div>
          ) : error ? (
            <div className="text-center py-12">
              <p className="text-sm text-red-400">{error}</p>
            </div>
          ) : (
            <div className="text-sm text-slate-700 dark:text-slate-300 whitespace-pre-wrap leading-relaxed">
              {summary}
            </div>
          )}
        </div>

        {/* Footer */}
        {!loading && !error && (
          <div className="flex items-center justify-end gap-2 px-4 py-3 border-t border-slate-200 dark:border-slate-700">
            <button
              onClick={handleCopy}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 cursor-pointer transition-colors"
            >
              {copied ? <Check size={13} className="text-green-500" /> : <Copy size={13} />}
              {copied ? "已複製" : "複製"}
            </button>
            {onSaveAsIntel && (
              <button
                onClick={handleSave}
                disabled={saving}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-cyan-500 hover:bg-cyan-600 text-white cursor-pointer disabled:opacity-50 transition-colors"
              >
                <Save size={13} />
                {saving ? "儲存中..." : "儲存為新情報"}
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
