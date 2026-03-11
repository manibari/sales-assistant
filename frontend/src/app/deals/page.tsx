"use client";

import { useState, useEffect, useMemo } from "react";
import { TopBar } from "@/components/top-bar";
import { nxApi, type NxDeal } from "@/lib/nexus-api";
import { formatBudget } from "@/lib/options";
import { AlertTriangle, ChevronDown, ChevronRight, Plus } from "lucide-react";
import Link from "next/link";

const STAGE_LABELS: Record<string, string> = {
  L0: "L0 潛在",
  L1: "L1 接觸中",
  L2: "L2 需求確認",
  L3: "L3 報價",
  L4: "L4 簽約",
  closed: "已關閉",
};

const STAGE_INDEX: Record<string, number> = { L0: 0, L1: 1, L2: 2, L3: 3, L4: 4, closed: 5 };

const STAGE_BAR_COLORS: Record<string, string> = {
  L0: "bg-slate-400",
  L1: "bg-blue-400",
  L2: "bg-cyan-400",
  L3: "bg-amber-400",
  L4: "bg-green-500",
  closed: "bg-slate-600",
};

const VIEW_LABELS: Record<string, string> = {
  urgency: "緊急度",
  stage: "階段",
  timeline: "時間軸",
};

const VIEW_ORDER: Array<"urgency" | "stage" | "timeline"> = ["urgency", "stage", "timeline"];

export default function DealsPage() {
  const [deals, setDeals] = useState<NxDeal[]>([]);
  const [view, setView] = useState<"urgency" | "stage" | "timeline">("urgency");
  const [collapsed, setCollapsed] = useState<Record<string, boolean>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    nxApi.deals
      .list(view)
      .then(setDeals)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [view]);

  const toggleCollapse = (stage: string) => {
    setCollapsed((prev) => ({ ...prev, [stage]: !prev[stage] }));
  };

  // Group deals by stage for stage view
  const grouped = deals.reduce<Record<string, NxDeal[]>>((acc, deal) => {
    const stage = deal.stage;
    if (!acc[stage]) acc[stage] = [];
    acc[stage].push(deal);
    return acc;
  }, {});

  const stageOrder = ["L0", "L1", "L2", "L3", "L4", "closed"];

  return (
    <div className="flex flex-col h-full">
      <TopBar title="商機 Pipeline">
        <Link
          href="/deals/new"
          className="p-2 rounded-lg text-blue-500 hover:bg-blue-500/10 cursor-pointer transition-colors"
        >
          <Plus size={20} />
        </Link>
        <button
          onClick={() => {
            const idx = VIEW_ORDER.indexOf(view);
            setView(VIEW_ORDER[(idx + 1) % VIEW_ORDER.length]);
          }}
          className="px-3 py-1.5 text-xs font-medium rounded-lg bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors cursor-pointer"
        >
          {VIEW_LABELS[VIEW_ORDER[(VIEW_ORDER.indexOf(view) + 1) % VIEW_ORDER.length]]}
        </button>
      </TopBar>

      <div className="flex-1 px-4 lg:px-6 py-4 overflow-auto">
        {loading ? (
          <div className="flex items-center justify-center py-20 text-slate-400">
            載入中...
          </div>
        ) : deals.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-slate-400 dark:text-slate-500">
            <p className="text-sm">尚無商機</p>
            <p className="text-xs mt-1">從情報建立第一個商機</p>
          </div>
        ) : view === "urgency" ? (
          <div className="space-y-3 lg:grid lg:grid-cols-2 lg:gap-4 lg:space-y-0 max-w-2xl lg:max-w-4xl mx-auto">
            {deals.map((deal) => (
              <DealCard key={deal.id} deal={deal} />
            ))}
          </div>
        ) : view === "stage" ? (
          <div className="space-y-4 max-w-2xl lg:max-w-4xl mx-auto">
            {stageOrder.map((stage) => {
              const stageDeals = grouped[stage];
              if (!stageDeals || stageDeals.length === 0) return null;
              const isCollapsed = collapsed[stage];
              return (
                <div key={stage}>
                  <button
                    onClick={() => toggleCollapse(stage)}
                    className="flex items-center gap-2 w-full text-left px-2 py-2 cursor-pointer"
                  >
                    {isCollapsed ? (
                      <ChevronRight size={16} className="text-slate-400" />
                    ) : (
                      <ChevronDown size={16} className="text-slate-400" />
                    )}
                    <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                      {STAGE_LABELS[stage] || stage}
                    </span>
                    <span className="text-xs text-slate-400 dark:text-slate-500">
                      ({stageDeals.length})
                    </span>
                  </button>
                  {!isCollapsed && (
                    <div className="space-y-3 mt-1">
                      {stageDeals.map((deal) => (
                        <DealCard key={deal.id} deal={deal} />
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          <TimelineView deals={deals} />
        )}
      </div>
    </div>
  );
}

function DealCard({ deal }: { deal: NxDeal }) {
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

function TimelineView({ deals }: { deals: NxDeal[] }) {
  const now = Date.now();

  // Calculate timeline range across all deals
  const { maxDays, sortedDeals } = useMemo(() => {
    const withAge = deals.map((d) => {
      const created = d.created_at ? new Date(d.created_at).getTime() : now;
      const ageDays = Math.max(1, Math.ceil((now - created) / 86_400_000));
      return { ...d, ageDays };
    });
    // Sort by age descending (oldest first)
    withAge.sort((a, b) => b.ageDays - a.ageDays);
    const max = Math.max(...withAge.map((d) => d.ageDays), 1);
    return { maxDays: max, sortedDeals: withAge };
  }, [deals, now]);

  // Stage legend
  const stages = ["L0", "L1", "L2", "L3", "L4"];

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
          const stagePct = ((stageIdx + 1) / 5) * 100;
          const idleDays = deal.idle_days ?? 0;
          const needsPush = idleDays > 14;

          return (
            <Link
              key={deal.id}
              href={`/deals/${deal.id}`}
              className="flex items-center gap-3 px-4 py-3 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors cursor-pointer group"
            >
              {/* Deal name + info */}
              <div className="w-36 lg:w-48 flex-shrink-0">
                <p className="text-sm font-medium text-slate-900 dark:text-slate-50 truncate group-hover:text-blue-500 transition-colors">
                  {deal.name}
                </p>
                <p className="text-[11px] text-slate-400 truncate">
                  {deal.client_name}
                </p>
              </div>

              {/* Gantt bar area */}
              <div className="flex-1 flex items-center gap-2">
                <div className="flex-1 relative h-7">
                  {/* Background track */}
                  <div className="absolute inset-y-0 left-0 right-0 bg-slate-100 dark:bg-slate-800 rounded" />

                  {/* Duration bar */}
                  <div
                    className="absolute inset-y-0 left-0 rounded overflow-hidden flex"
                    style={{ width: `${pct}%` }}
                  >
                    {/* Stage progress fill */}
                    <div
                      className={`h-full ${STAGE_BAR_COLORS[deal.stage]} transition-all`}
                      style={{ width: `${stagePct}%` }}
                    />
                    {/* Remaining (unfilled stage area) */}
                    <div
                      className="h-full bg-slate-200 dark:bg-slate-700"
                      style={{ width: `${100 - stagePct}%` }}
                    />
                  </div>

                  {/* Idle warning stripe */}
                  {needsPush && (
                    <div
                      className="absolute inset-y-0 right-0 bg-red-500/20 rounded-r border-r-2 border-red-500"
                      style={{ width: `${Math.min((idleDays / deal.ageDays) * pct, pct)}%` }}
                    />
                  )}

                  {/* Stage label on bar */}
                  <span className="absolute inset-y-0 left-1.5 flex items-center text-[10px] font-semibold text-white drop-shadow-sm">
                    {deal.stage}
                  </span>
                </div>

                {/* Days label */}
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
