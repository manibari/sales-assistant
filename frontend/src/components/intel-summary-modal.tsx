"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { X, Loader2, Copy, Check, Merge } from "lucide-react";
import { nxApi } from "@/lib/nexus-api";

interface IntelSummaryModalProps {
  intelIds: number[];
  onClose: () => void;
  onMerged?: () => void;
  onSaveAsIntel?: (summary: string) => Promise<void>;
}

export function IntelSummaryModal({ intelIds, onClose, onMerged, onSaveAsIntel }: IntelSummaryModalProps) {
  const router = useRouter();
  const [summary, setSummary] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);
  const [merging, setMerging] = useState(false);
  const [title, setTitle] = useState("");

  useEffect(() => {
    nxApi.intel
      .summarize(intelIds)
      .then((res) => {
        setSummary(res.summary);
        // Extract first line as suggested title
        const firstLine = res.summary.split("\n")[0].replace(/^[#\-*\s]+/, "").slice(0, 60);
        setTitle(firstLine);
      })
      .catch((err) => setError(err.message || "AI 彙整失敗"))
      .finally(() => setLoading(false));
  }, [intelIds]);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(summary);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleMerge = async () => {
    if (merging) return;
    setMerging(true);
    try {
      if (onSaveAsIntel) {
        // Custom save logic (e.g. link to deal)
        await onSaveAsIntel(summary);
        onClose();
        return;
      }
      // 1. Create new merged intel
      const newIntel = await nxApi.intel.create({
        raw_input: summary,
        input_type: "text",
        title: title || "AI 彙整",
      });
      // 2. Delete original intels
      await nxApi.intel.bulkDelete(intelIds);
      // 3. Notify parent
      onMerged?.();
      onClose();
      // 4. Navigate to new intel detail page
      router.push(`/intel/${newIntel.id}`);
    } catch {
      setError("合併失敗");
      setMerging(false);
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
        <div className="flex-1 overflow-auto px-4 py-4 space-y-4">
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
            <>
              {/* Title input */}
              <div>
                <label className="text-[11px] font-medium text-slate-400 uppercase tracking-wide">
                  情報標題
                </label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="為合併後的情報命名"
                  className="mt-1 w-full px-3 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-50 focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
                />
              </div>

              {/* Summary preview */}
              <div>
                <label className="text-[11px] font-medium text-slate-400 uppercase tracking-wide">
                  彙整內容預覽
                </label>
                <div className="mt-1 p-3 rounded-lg bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 text-sm text-slate-700 dark:text-slate-300 whitespace-pre-wrap leading-relaxed max-h-60 overflow-auto">
                  {summary}
                </div>
              </div>

              {/* Info */}
              <p className="text-[11px] text-slate-400">
                確認合併後，原始 {intelIds.length} 筆情報將被刪除，並建立一筆新的彙整情報。
                你可以在詳情頁連結商機、編輯標題等。
              </p>
            </>
          )}
        </div>

        {/* Footer */}
        {!loading && !error && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-slate-200 dark:border-slate-700">
            <button
              onClick={handleCopy}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 cursor-pointer transition-colors"
            >
              {copied ? <Check size={13} className="text-green-500" /> : <Copy size={13} />}
              {copied ? "已複製" : "複製"}
            </button>
            <button
              onClick={handleMerge}
              disabled={merging || !title.trim()}
              className="flex items-center gap-1.5 px-4 py-2 text-xs font-medium rounded-lg bg-cyan-500 hover:bg-cyan-600 text-white cursor-pointer disabled:opacity-50 transition-colors"
            >
              <Merge size={13} />
              {merging ? "合併中..." : "確認合併"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
