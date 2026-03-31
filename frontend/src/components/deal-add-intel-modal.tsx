"use client";

import { X } from "lucide-react";
import { nxApi, type NxDeal, type NxIntel } from "@/lib/nexus-api";
import { getIntelDisplayTitle } from "@/lib/intel-display";

interface DealAddIntelModalProps {
  dealId: number;
  deal: NxDeal;
  allIntels: NxIntel[];
  onClose: () => void;
  onLinked: () => void;
}

export function DealAddIntelModal({ dealId, deal, allIntels, onClose, onLinked }: DealAddIntelModalProps) {
  const linked = deal.intel || [];
  const available = allIntels.filter(
    (i) => !linked.some((di: { id: number; intel_id?: number }) => (di.intel_id ?? di.id) === i.id)
  );

  return (
    <div className="fixed inset-0 bg-slate-950/50 flex items-end md:items-center justify-center z-50">
      <div className="bg-white dark:bg-slate-900 rounded-t-2xl md:rounded-xl p-6 w-full max-w-md mx-auto space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-bold text-slate-900 dark:text-slate-50">關聯情報</h3>
          <button onClick={onClose} className="p-1.5 text-slate-400 hover:text-slate-200 cursor-pointer transition-colors">
            <X size={20} />
          </button>
        </div>
        <div className="max-h-72 overflow-auto divide-y divide-slate-100 dark:divide-slate-800">
          {allIntels.length === 0 ? (
            <p className="text-sm text-slate-400 py-4 text-center">載入中...</p>
          ) : (
            available.map((i) => (
              <button
                key={i.id}
                onClick={async () => {
                  try {
                    await nxApi.deals.linkIntel(dealId, i.id);
                    onClose();
                    onLinked();
                  } catch (err) { console.error(err); }
                }}
                className="w-full py-3 px-1 hover:bg-slate-50 dark:hover:bg-slate-800/50 rounded transition-colors cursor-pointer text-left"
              >
                <p className="text-sm text-slate-900 dark:text-slate-50 line-clamp-2">{getIntelDisplayTitle(i, 80)}</p>
                <div className="flex items-center gap-2 mt-1">
                  <span className={`text-[11px] px-2 py-0.5 rounded-full font-medium ${i.status === "confirmed" ? "bg-green-500/10 text-green-400" : "bg-amber-500/10 text-amber-400"}`}>
                    {i.status === "confirmed" ? "已確認" : "草稿"}
                  </span>
                  <span className="text-[11px] text-slate-400">{new Date(i.created_at).toLocaleDateString("zh-TW")}</span>
                </div>
              </button>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
