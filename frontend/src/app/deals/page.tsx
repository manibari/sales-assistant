"use client";

import { useState, useEffect, useMemo } from "react";
import { TopBar } from "@/components/top-bar";
import { nxApi, type NxDeal } from "@/lib/nexus-api";
import { STAGE_LABELS } from "@/lib/deal-constants";
import { DealCard } from "@/components/deal-card";
import { TimelineView } from "@/components/deal-timeline";
import { ChevronDown, ChevronRight, Plus, Search, X } from "lucide-react";
import Link from "next/link";

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
  const [search, setSearch] = useState("");
  const [showSearch, setShowSearch] = useState(false);

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

  const filteredDeals = useMemo(() => {
    if (!search.trim()) return deals;
    const q = search.toLowerCase();
    return deals.filter(
      (d) =>
        d.name.toLowerCase().includes(q) ||
        d.client_name?.toLowerCase().includes(q) ||
        d.stage.toLowerCase().includes(q)
    );
  }, [deals, search]);

  const grouped = filteredDeals.reduce<Record<string, NxDeal[]>>((acc, deal) => {
    const stage = deal.stage;
    if (!acc[stage]) acc[stage] = [];
    acc[stage].push(deal);
    return acc;
  }, {});

  const stageOrder = ["L0", "L1", "L2", "L3", "L4", "L5", "L6", "L7", "LOST", "HOLD"];

  return (
    <div className="flex flex-col h-full">
      <TopBar title="商機 Pipeline">
        <button
          onClick={() => { setShowSearch((v) => !v); if (showSearch) setSearch(""); }}
          className="p-2 rounded-lg text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer transition-colors"
        >
          <Search size={20} />
        </button>
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

      {showSearch && (
        <div className="px-4 lg:px-6 pt-3">
          <div className="relative max-w-2xl lg:max-w-4xl mx-auto">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="搜尋商機名稱、客戶、階段..."
              autoFocus
              className="w-full pl-9 pr-9 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-50 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500"
            />
            {search && (
              <button
                onClick={() => setSearch("")}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 cursor-pointer"
              >
                <X size={16} />
              </button>
            )}
            {search && (
              <p className="text-[11px] text-slate-400 mt-1">
                {filteredDeals.length} / {deals.length} 筆
              </p>
            )}
          </div>
        </div>
      )}

      <div className="flex-1 px-4 lg:px-6 py-4 overflow-auto">
        {loading ? (
          <div className="flex items-center justify-center py-20 text-slate-400">
            載入中...
          </div>
        ) : filteredDeals.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-slate-400 dark:text-slate-500">
            <p className="text-sm">{search ? "找不到符合的商機" : "尚無商機"}</p>
            <p className="text-xs mt-1">{search ? "試試其他關鍵字" : "從情報建立第一個商機"}</p>
          </div>
        ) : view === "urgency" ? (
          <div className="space-y-3 lg:grid lg:grid-cols-2 lg:gap-4 lg:space-y-0 max-w-2xl lg:max-w-4xl mx-auto">
            {filteredDeals.map((deal) => (
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
          <TimelineView deals={filteredDeals} />
        )}
      </div>
    </div>
  );
}
