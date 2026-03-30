import { useMemo } from "react";
import Link from "next/link";
import { AlertTriangle } from "lucide-react";
import { STAGE_LABELS, STAGE_INDEX, STAGE_BAR_COLORS } from "@/lib/deal-constants";
import type { NxDeal } from "@/lib/nexus-api";

export function TimelineView({ deals }: { deals: NxDeal[] }) {
  const now = Date.now();

  const { maxDays, sortedDeals } = useMemo(() => {
    const withAge = deals.map((d) => {
      const created = d.created_at ? new Date(d.created_at).getTime() : now;
      const ageDays = Math.max(1, Math.ceil((now - created) / 86_400_000));
      return { ...d, ageDays };
    });
    withAge.sort((a, b) => b.ageDays - a.ageDays);
    const max = Math.max(...withAge.map((d) => d.ageDays), 1);
    return { maxDays: max, sortedDeals: withAge };
  }, [deals, now]);

  const stages = ["L0", "L1", "L2", "L3", "L4", "L5", "L6", "L7"];

  return (
    <div className="max-w-2xl lg:max-w-5xl mx-auto space-y-4">
      {/* Legend */}
      <div className="flex items-center gap-4 text-xs text-slate-500 dark:text-slate-400">
        <span className="font-medium">階段：</span>
        {stages.map((s) => (
          <span key={s} className="flex items-center gap-1">
            <span className={`inline-block w-2.5 h-2.5 rounded-sm ${STAGE_BAR_COLORS[s]}`} />
            {STAGE_LABELS[s]}
          </span>
        ))}
      </div>

      {/* Timeline rows */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl overflow-hidden divide-y divide-slate-100 dark:divide-slate-800">
        {sortedDeals.map((deal) => {
          const pct = Math.max((deal.ageDays / maxDays) * 100, 3);
          const stageIdx = STAGE_INDEX[deal.stage] ?? 0;
          const stagePct = ((stageIdx + 1) / 8) * 100;
          const idleDays = deal.idle_days ?? 0;
          const needsPush = idleDays > 14;

          return (
            <Link
              key={deal.id}
              href={`/deals/${deal.id}`}
              className="flex items-center gap-3 px-4 py-3 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors cursor-pointer group"
            >
              <div className="w-36 lg:w-48 flex-shrink-0">
                <p className="text-sm font-medium text-slate-900 dark:text-slate-50 truncate group-hover:text-blue-500 transition-colors">
                  {deal.name}
                </p>
                <p className="text-[11px] text-slate-400 truncate">
                  {deal.client_name}
                </p>
              </div>

              <div className="flex-1 flex items-center gap-2">
                <div className="flex-1 relative h-7">
                  <div className="absolute inset-y-0 left-0 right-0 bg-slate-100 dark:bg-slate-800 rounded" />
                  <div
                    className="absolute inset-y-0 left-0 rounded overflow-hidden flex"
                    style={{ width: `${pct}%` }}
                  >
                    <div
                      className={`h-full ${STAGE_BAR_COLORS[deal.stage]} transition-all`}
                      style={{ width: `${stagePct}%` }}
                    />
                    <div
                      className="h-full bg-slate-200 dark:bg-slate-700"
                      style={{ width: `${100 - stagePct}%` }}
                    />
                  </div>
                  {needsPush && (
                    <div
                      className="absolute inset-y-0 right-0 bg-red-500/20 rounded-r border-r-2 border-red-500"
                      style={{ width: `${Math.min((idleDays / deal.ageDays) * pct, pct)}%` }}
                    />
                  )}
                  <span className="absolute inset-y-0 left-1.5 flex items-center text-[10px] font-semibold text-white drop-shadow-sm">
                    {deal.stage}
                  </span>
                </div>

                <div className="w-16 flex-shrink-0 text-right">
                  <span className={`text-xs font-medium ${needsPush ? "text-red-500" : "text-slate-500 dark:text-slate-400"}`}>
                    {deal.ageDays}天
                  </span>
                  {needsPush && (
                    <p className="text-[10px] text-red-400 flex items-center justify-end gap-0.5">
                      <AlertTriangle size={10} />
                      閒置{idleDays}天
                    </p>
                  )}
                </div>
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
