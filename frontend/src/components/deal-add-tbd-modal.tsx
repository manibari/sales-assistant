"use client";

import { useState } from "react";
import { X } from "lucide-react";
import { nxApi } from "@/lib/nexus-api";

interface DealAddTbdModalProps {
  dealId: number;
  onClose: () => void;
  onCreated: () => void;
}

export function DealAddTbdModal({ dealId, onClose, onCreated }: DealAddTbdModalProps) {
  const [tbdQuestion, setTbdQuestion] = useState("");

  return (
    <div className="fixed inset-0 bg-slate-950/50 flex items-end md:items-center justify-center z-50">
      <div className="bg-white dark:bg-slate-900 rounded-t-2xl md:rounded-xl p-6 w-full max-w-md mx-auto space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-bold text-slate-900 dark:text-slate-50">新增 TBD</h3>
          <button onClick={onClose} className="p-1.5 text-slate-400 hover:text-slate-200 cursor-pointer transition-colors">
            <X size={20} />
          </button>
        </div>
        <div>
          <label className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-1 block">待確認事項</label>
          <textarea
            value={tbdQuestion}
            onChange={(e) => setTbdQuestion(e.target.value)}
            placeholder="例：客戶預算是否含稅？"
            className="w-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-4 py-3 text-sm text-slate-900 dark:text-slate-50 placeholder:text-slate-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none resize-none h-24"
            autoFocus
          />
        </div>
        <div className="flex gap-2">
          <button
            onClick={onClose}
            className="flex-1 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-700 font-medium px-4 py-3 rounded-lg min-h-[44px] cursor-pointer transition-colors"
          >
            取消
          </button>
          <button
            onClick={async () => {
              if (!tbdQuestion.trim()) return;
              try {
                await nxApi.tbd.create({ question: tbdQuestion.trim(), linked_type: "deal", linked_id: dealId, source: "manual" });
                onClose();
                onCreated();
              } catch (err) { console.error(err); }
            }}
            disabled={!tbdQuestion.trim()}
            className="flex-1 bg-blue-500 hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold px-4 py-3 rounded-lg min-h-[44px] active:scale-[0.98] transition-all cursor-pointer"
          >
            建立
          </button>
        </div>
      </div>
    </div>
  );
}
