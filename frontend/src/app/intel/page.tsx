"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { TopBar } from "@/components/top-bar";
import { nxApi, type NxIntel } from "@/lib/nexus-api";
import { getIntelDisplayTitle } from "@/lib/intel-display";
import { FileText, Camera, Mic, ChevronRight, Paperclip, Trash2, CheckSquare, Square, X, Sparkles } from "lucide-react";
import { IntelSummaryModal } from "@/components/intel-summary-modal";

const INPUT_ICONS: Record<string, typeof FileText> = {
  text: FileText,
  photo: Camera,
  voice: Mic,
};

export default function IntelPage() {
  const [intels, setIntels] = useState<NxIntel[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectMode, setSelectMode] = useState(false);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [deleting, setDeleting] = useState(false);
  const [showSummary, setShowSummary] = useState(false);

  useEffect(() => {
    nxApi.intel
      .list()
      .then(setIntels)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const handleDelete = async (e: React.MouseEvent, id: number) => {
    e.preventDefault();
    e.stopPropagation();
    if (!confirm("確定要刪除這筆情報？")) return;
    try {
      await nxApi.intel.delete(id);
      setIntels((prev) => prev.filter((i) => i.id !== id));
    } catch (err) {
      console.error(err);
      alert("刪除失敗");
    }
  };

  const toggleSelect = (e: React.MouseEvent, id: number) => {
    e.preventDefault();
    e.stopPropagation();
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleSelectAll = () => {
    if (selected.size === intels.length) {
      setSelected(new Set());
    } else {
      setSelected(new Set(intels.map((i) => i.id)));
    }
  };

  const handleBulkDelete = async () => {
    if (selected.size === 0) return;
    if (!confirm(`確定要刪除 ${selected.size} 筆情報？`)) return;
    setDeleting(true);
    try {
      await nxApi.intel.bulkDelete(Array.from(selected));
      setIntels((prev) => prev.filter((i) => !selected.has(i.id)));
      setSelected(new Set());
      setSelectMode(false);
    } catch (err) {
      console.error(err);
      alert("批次刪除失敗");
    } finally {
      setDeleting(false);
    }
  };

  const exitSelectMode = () => {
    setSelectMode(false);
    setSelected(new Set());
  };

  return (
    <div className="flex flex-col h-full">
      <TopBar title="情報 Feed" />
      <div className="flex-1 px-4 py-4 overflow-auto">
        {loading ? (
          <div className="flex items-center justify-center py-20 text-slate-400">
            載入中...
          </div>
        ) : intels.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-slate-400 dark:text-slate-500">
            <p className="text-sm">尚無情報</p>
            <p className="text-xs mt-1">點擊 ＋ 新增第一筆情報</p>
          </div>
        ) : (
          <div className="max-w-2xl lg:max-w-4xl mx-auto">
            {/* Select mode toolbar */}
            <div className="flex items-center justify-between mb-3">
              {selectMode ? (
                <>
                  <div className="flex items-center gap-3">
                    <button
                      onClick={exitSelectMode}
                      className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                      title="取消選取"
                    >
                      <X size={16} />
                    </button>
                    <button
                      onClick={toggleSelectAll}
                      className="text-xs text-cyan-500 hover:text-cyan-400 transition-colors"
                    >
                      {selected.size === intels.length ? "取消全選" : "全選"}
                    </button>
                    <span className="text-xs text-slate-400">
                      已選 {selected.size} / {intels.length}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setShowSummary(true)}
                      disabled={selected.size < 2}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-cyan-500/10 text-cyan-500 hover:bg-cyan-500/20 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                      <Sparkles size={13} />
                      彙整 ({selected.size})
                    </button>
                    <button
                      onClick={handleBulkDelete}
                      disabled={selected.size === 0 || deleting}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-red-500/10 text-red-500 hover:bg-red-500/20 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                      <Trash2 size={13} />
                      {deleting ? "刪除中..." : `刪除 (${selected.size})`}
                    </button>
                  </div>
                </>
              ) : (
                <div className="flex items-center gap-2 ml-auto">
                  <button
                    onClick={() => setSelectMode(true)}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                  >
                    <CheckSquare size={13} />
                    選取
                  </button>
                </div>
              )}
            </div>

            {/* Intel list */}
            <div className="space-y-3">
              {intels.map((intel) => {
                const Icon = INPUT_ICONS[intel.input_type] || FileText;
                const isConfirmed = intel.status === "confirmed";
                const isSelected = selected.has(intel.id);

                const card = (
                  <div className="flex items-start gap-3">
                    {selectMode && (
                      <button
                        onClick={(e) => toggleSelect(e, intel.id)}
                        className="flex-shrink-0 mt-1 text-slate-400 hover:text-cyan-500 transition-colors"
                      >
                        {isSelected ? (
                          <CheckSquare size={18} className="text-cyan-500" />
                        ) : (
                          <Square size={18} />
                        )}
                      </button>
                    )}
                    <div className="w-8 h-8 rounded-lg bg-cyan-500/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                      <Icon size={16} className="text-cyan-500" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-slate-900 dark:text-slate-50 line-clamp-2">
                        {getIntelDisplayTitle(intel, 80)}
                      </p>
                      <div className="flex items-center gap-2 mt-2">
                        <span
                          className={`text-[11px] px-2 py-0.5 rounded-full font-medium ${
                            isConfirmed
                              ? "bg-green-500/10 text-green-400"
                              : "bg-amber-500/10 text-amber-400"
                          }`}
                        >
                          {isConfirmed ? "已確認" : "草稿"}
                        </span>
                        {intel.file_count && intel.file_count > 0 ? (
                          <span className="text-[11px] text-slate-400 flex items-center gap-0.5">
                            <Paperclip size={10} />
                            {intel.file_count}
                          </span>
                        ) : null}
                        <span className="text-[11px] text-slate-400 dark:text-slate-500">
                          {new Date(intel.created_at).toLocaleDateString("zh-TW")}
                        </span>
                      </div>
                    </div>
                    {!selectMode && (
                      <>
                        <button
                          onClick={(e) => handleDelete(e, intel.id)}
                          className="p-1.5 rounded-lg text-slate-400 hover:text-red-500 hover:bg-red-500/10 transition-colors flex-shrink-0 mt-1"
                          title="刪除情報"
                        >
                          <Trash2 size={14} />
                        </button>
                        <ChevronRight size={16} className="text-slate-400 flex-shrink-0 mt-2" />
                      </>
                    )}
                  </div>
                );

                return selectMode ? (
                  <div
                    key={intel.id}
                    onClick={(e) => toggleSelect(e, intel.id)}
                    className={`block bg-white dark:bg-slate-900 border rounded-xl p-4 transition-colors duration-200 cursor-pointer ${
                      isSelected
                        ? "border-cyan-500/50 bg-cyan-500/5 dark:bg-cyan-500/5"
                        : "border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600"
                    }`}
                  >
                    {card}
                  </div>
                ) : (
                  <Link
                    key={intel.id}
                    href={`/intel/${intel.id}`}
                    className="block bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4 transition-colors duration-200 cursor-pointer hover:border-slate-300 dark:hover:border-slate-600"
                  >
                    {card}
                  </Link>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {showSummary && (
        <IntelSummaryModal
          intelIds={Array.from(selected)}
          onClose={() => setShowSummary(false)}
          onMerged={() => {
            setSelected(new Set());
            setSelectMode(false);
          }}
        />
      )}
    </div>
  );
}
