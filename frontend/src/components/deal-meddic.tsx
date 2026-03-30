"use client";

import { useState } from "react";
import { ChevronUp, ChevronDown, Check, X, CircleDot } from "lucide-react";
import { MEDDIC_LABELS } from "@/lib/deal-constants";
import { nxApi } from "@/lib/nexus-api";
import type { MeddicProgress } from "@/lib/nexus-api";

export function DealMeddic({
  dealId,
  meddicJson,
  progress,
  isClosed,
  onUpdated,
}: {
  dealId: number;
  meddicJson?: string | Record<string, string | null> | null;
  progress: MeddicProgress;
  isClosed: boolean;
  onUpdated: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [editingKey, setEditingKey] = useState<string | null>(null);
  const [value, setValue] = useState("");

  const meddic: Record<string, string | null> = meddicJson
    ? typeof meddicJson === "string"
      ? JSON.parse(meddicJson)
      : meddicJson
    : {};

  const handleSave = async (key: string) => {
    const current = { ...meddic };
    current[key] = value;
    try {
      await nxApi.deals.update(dealId, { meddic_json: JSON.stringify(current) } as Parameters<typeof nxApi.deals.update>[1]);
      setEditingKey(null);
      setValue("");
      onUpdated();
    } catch (err) {
      console.error("Failed to save MEDDIC:", err);
    }
  };

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
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
          {open ? (
            <ChevronUp size={16} className="text-slate-400" />
          ) : (
            <ChevronDown size={16} className="text-slate-400" />
          )}
        </div>
      </button>
      {open && (
        <div className="border-t border-slate-200 dark:border-slate-700 divide-y divide-slate-200 dark:divide-slate-700">
          {progress.missing.length > 0 && !isClosed && (
            <div className="px-4 py-2 bg-slate-50 dark:bg-slate-800/50">
              <button
                onClick={async () => {
                  try {
                    const res = await nxApi.deals.aiFillMeddic(dealId);
                    if (res.ai_filled.length > 0) {
                      onUpdated();
                    } else {
                      alert("AI 未找到新的 MEDDIC 線索");
                    }
                  } catch (err) {
                    console.error("AI MEDDIC fill failed:", err);
                    alert("AI 分析失敗，請確認有關聯情報");
                  }
                }}
                className="text-xs text-cyan-500 hover:text-cyan-400 font-medium cursor-pointer transition-colors"
              >
                ✨ AI 從情報自動填寫（{progress.missing.length} 項未填）
              </button>
            </div>
          )}
          {Object.entries(MEDDIC_LABELS).map(([key, label]) => {
            const val = meddic[key];
            const isEditing = editingKey === key;
            return (
              <div key={key} className="px-4 py-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {val ? (
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
                        setEditingKey(key);
                        setValue(val || "");
                      }}
                      className="text-xs text-blue-500 cursor-pointer"
                    >
                      {val ? "編輯" : "填寫"}
                    </button>
                  )}
                </div>
                {val && !isEditing && (
                  <p className="text-sm text-slate-700 dark:text-slate-300 mt-1 ml-6">
                    {val}
                  </p>
                )}
                {isEditing && (
                  <div className="mt-2 ml-6 flex gap-2">
                    <input
                      type="text"
                      value={value}
                      onChange={(e) => setValue(e.target.value)}
                      className="flex-1 bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-900 dark:text-slate-50 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
                      placeholder="輸入內容..."
                      autoFocus
                    />
                    <button
                      onClick={() => handleSave(key)}
                      className="p-2 bg-blue-500 text-white rounded-lg cursor-pointer"
                    >
                      <Check size={16} />
                    </button>
                    <button
                      onClick={() => setEditingKey(null)}
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
  );
}
