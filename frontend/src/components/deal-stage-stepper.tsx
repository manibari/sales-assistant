"use client";

import { Trash2 } from "lucide-react";
import { STAGE_ORDER, STAGE_LABELS } from "@/lib/deal-constants";

export function DealStageStepper({
  currentStage,
  advancing,
  onStageClick,
  onClose,
  onHold,
  onDelete,
}: {
  currentStage: string;
  advancing: boolean;
  onStageClick: (stage: string) => void;
  onClose: () => void;
  onHold: () => void;
  onDelete: () => void;
}) {
  const currentIdx = STAGE_ORDER.indexOf(currentStage);

  return (
    <div className="mt-4 space-y-3">
      <div className="flex items-center gap-0.5 overflow-x-auto">
        {STAGE_ORDER.map((s, i) => {
          const isActive = i === currentIdx;
          const isPast = i < currentIdx;
          return (
            <button
              key={s}
              onClick={() => {
                if (i !== currentIdx && !advancing) onStageClick(s);
              }}
              disabled={advancing || i === currentIdx}
              className={`flex-1 min-w-0 py-2 text-[11px] font-medium rounded-lg cursor-pointer transition-all disabled:cursor-default ${
                isActive
                  ? "bg-blue-500 text-white"
                  : isPast
                  ? "bg-blue-500/10 text-blue-400 hover:bg-blue-500/20"
                  : "bg-slate-100 dark:bg-slate-800 text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700"
              }`}
            >
              {advancing ? "…" : STAGE_LABELS[s]?.split(" ")[0] || s}
            </button>
          );
        })}
      </div>
      <div className="flex gap-2">
        <button
          onClick={onClose}
          className="flex-1 px-4 py-2.5 rounded-lg text-sm font-medium bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 min-h-[44px] cursor-pointer transition-colors"
        >
          關閉案件
        </button>
        <button
          onClick={onHold}
          disabled={advancing}
          className="flex-1 px-4 py-2.5 rounded-lg text-sm font-medium bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 min-h-[44px] cursor-pointer transition-colors"
        >
          擱置案件
        </button>
      </div>
      <button
        onClick={onDelete}
        className="w-full px-4 py-2.5 rounded-lg text-sm font-medium text-red-500 hover:bg-red-500/10 border border-red-500/20 min-h-[44px] cursor-pointer transition-colors flex items-center justify-center gap-1.5"
      >
        <Trash2 size={14} />
        刪除商機
      </button>
    </div>
  );
}
