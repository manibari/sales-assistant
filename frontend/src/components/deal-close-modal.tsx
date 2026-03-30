"use client";

import { useState } from "react";
import { CLOSE_REASONS } from "@/lib/deal-constants";

export function DealCloseModal({
  onClose,
  onConfirm,
}: {
  onClose: () => void;
  onConfirm: (reason: string, notes?: string) => void;
}) {
  const [reason, setReason] = useState("");
  const [notes, setNotes] = useState("");

  return (
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
              onClick={() => setReason(r.value)}
              className={`min-h-[44px] px-3 py-2 text-sm font-medium rounded-lg border transition-colors cursor-pointer ${
                reason === r.value
                  ? "border-red-500 bg-red-500/10 text-red-400"
                  : "bg-slate-100 dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200"
              }`}
            >
              {r.label}
            </button>
          ))}
        </div>
        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="備註 (optional)"
          className="w-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-4 py-3 text-sm text-slate-900 dark:text-slate-50 placeholder:text-slate-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none resize-none h-20"
        />
        <div className="flex gap-2">
          <button
            onClick={onClose}
            className="flex-1 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-700 font-medium px-4 py-3 rounded-lg min-h-[44px] cursor-pointer transition-colors"
          >
            取消
          </button>
          <button
            onClick={() => { if (reason) onConfirm(reason, notes || undefined); }}
            disabled={!reason}
            className="flex-1 bg-red-500 hover:bg-red-600 disabled:opacity-50 text-white font-semibold px-4 py-3 rounded-lg min-h-[44px] cursor-pointer transition-all"
          >
            確定關閉
          </button>
        </div>
      </div>
    </div>
  );
}
