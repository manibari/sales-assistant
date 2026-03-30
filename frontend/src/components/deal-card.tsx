import Link from "next/link";
import { AlertTriangle } from "lucide-react";
import { STAGE_LABELS } from "@/lib/deal-constants";
import { formatBudget } from "@/lib/options";
import type { NxDeal } from "@/lib/nexus-api";

export function DealCard({ deal }: { deal: NxDeal }) {
  const idleDays = deal.idle_days ?? 0;
  const needsPush = idleDays > 14;

  const borderColor = needsPush
    ? "border-l-red-500"
    : idleDays > 7
      ? "border-l-amber-500"
      : "border-l-green-500";

  return (
    <Link
      href={`/deals/${deal.id}`}
      className={`block bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4 transition-colors duration-200 cursor-pointer hover:border-slate-300 dark:hover:border-slate-600 active:bg-slate-50 dark:active:bg-slate-800 border-l-4 ${borderColor}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <h3 className="text-base font-semibold text-slate-900 dark:text-slate-50 truncate">
            {deal.name}
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            {deal.client_name} · {deal.client_industry || "—"}
          </p>
        </div>
        <div className="flex flex-col items-end gap-1">
          <span className="text-[11px] px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 font-medium">
            {STAGE_LABELS[deal.stage] || deal.stage}
          </span>
          {needsPush && (
            <span className="flex items-center gap-1 text-[11px] text-red-400">
              <AlertTriangle size={12} />
              {idleDays}天未動
            </span>
          )}
        </div>
      </div>
      <div className="flex gap-3 mt-3 text-[11px] text-slate-400 dark:text-slate-500">
        {deal.budget_amount ? <span>預算: {formatBudget(deal.budget_amount)}</span> : null}
        {deal.timeline && <span>時程: {deal.timeline}</span>}
      </div>
    </Link>
  );
}
