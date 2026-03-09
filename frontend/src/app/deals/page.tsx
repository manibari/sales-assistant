"use client";

import { useState, useEffect } from "react";
import { TopBar } from "@/components/top-bar";
import { nxApi, type NxDeal } from "@/lib/nexus-api";
import { AlertTriangle, ChevronDown, ChevronRight } from "lucide-react";

const STAGE_LABELS: Record<string, string> = {
  L0: "L0 潛在",
  L1: "L1 接觸中",
  L2: "L2 需求確認",
  L3: "L3 報價",
  L4: "L4 簽約",
  closed: "已關閉",
};

export default function DealsPage() {
  const [deals, setDeals] = useState<NxDeal[]>([]);
  const [view, setView] = useState<"urgency" | "stage">("urgency");
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
        <button
          onClick={() => setView(view === "urgency" ? "stage" : "urgency")}
          className="px-3 py-1.5 text-xs font-medium rounded-lg bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors cursor-pointer"
        >
          {view === "urgency" ? "階段" : "緊急度"}
        </button>
      </TopBar>

      <div className="flex-1 px-4 py-4 overflow-auto">
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
          <div className="space-y-3 max-w-2xl mx-auto">
            {deals.map((deal) => (
              <DealCard key={deal.id} deal={deal} />
            ))}
          </div>
        ) : (
          <div className="space-y-4 max-w-2xl mx-auto">
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
    <div
      className={`bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4 transition-colors duration-200 cursor-pointer hover:border-slate-300 dark:hover:border-slate-600 active:bg-slate-50 dark:active:bg-slate-800 border-l-4 ${borderColor}`}
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
        {deal.budget_range && <span>預算: {deal.budget_range}</span>}
        {deal.timeline && <span>時程: {deal.timeline}</span>}
      </div>
    </div>
  );
}
