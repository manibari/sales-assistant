"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { formatBudget, industryLabel } from "@/lib/options";
import type { NxClient } from "@/lib/nexus-api";

interface CellData {
  clients: NxClient[];
  count: number;
  totalBudget: number;
}

export function ClientHeatmap({ clients }: { clients: NxClient[] }) {
  const [hoveredCell, setHoveredCell] = useState<string | null>(null);

  const { industries, markets, grid, maxBudget, industryTotals, marketTotals, grandTotal } = useMemo(() => {
    const g: Record<string, Record<string, CellData>> = {};
    const indTotals: Record<string, { count: number; budget: number }> = {};
    const mktTotals: Record<string, { count: number; budget: number }> = {};
    let max = 0;
    let total = 0;

    for (const c of clients) {
      const ind = c.industry || "未分類";
      const mkt = c.market === "overseas" ? "overseas" : "domestic";
      const budget = c.deal_budget_total ?? 0;

      if (!g[ind]) g[ind] = {};
      if (!g[ind][mkt]) g[ind][mkt] = { clients: [], count: 0, totalBudget: 0 };
      g[ind][mkt].clients.push(c);
      g[ind][mkt].count++;
      g[ind][mkt].totalBudget += budget;

      if (!indTotals[ind]) indTotals[ind] = { count: 0, budget: 0 };
      indTotals[ind].count++;
      indTotals[ind].budget += budget;

      if (!mktTotals[mkt]) mktTotals[mkt] = { count: 0, budget: 0 };
      mktTotals[mkt].count++;
      mktTotals[mkt].budget += budget;

      total += budget;
      if (g[ind][mkt].totalBudget > max) max = g[ind][mkt].totalBudget;
    }

    // Sort industries by total budget descending
    const sortedIndustries = Object.keys(indTotals).sort(
      (a, b) => indTotals[b].budget - indTotals[a].budget
    );

    return {
      industries: sortedIndustries,
      markets: ["domestic", "overseas"] as const,
      grid: g,
      maxBudget: max,
      industryTotals: indTotals,
      marketTotals: mktTotals,
      grandTotal: total,
    };
  }, [clients]);

  const marketLabel = (m: string) => (m === "overseas" ? "海外" : "國內");

  const getIntensity = (budget: number): string => {
    if (maxBudget === 0 || budget === 0) return "bg-slate-50 dark:bg-slate-800/30";
    const ratio = budget / maxBudget;
    if (ratio > 0.75) return "bg-blue-500/70 dark:bg-blue-500/60";
    if (ratio > 0.5) return "bg-blue-500/50 dark:bg-blue-500/40";
    if (ratio > 0.25) return "bg-blue-500/30 dark:bg-blue-500/25";
    if (ratio > 0.1) return "bg-blue-500/15 dark:bg-blue-500/15";
    return "bg-blue-500/8 dark:bg-blue-500/8";
  };

  const getTextColor = (budget: number): string => {
    if (maxBudget === 0 || budget === 0) return "text-slate-400";
    const ratio = budget / maxBudget;
    if (ratio > 0.5) return "text-white";
    return "text-slate-700 dark:text-slate-200";
  };

  const hoveredData = hoveredCell ? (() => {
    const [ind, mkt] = hoveredCell.split("|||");
    return grid[ind]?.[mkt];
  })() : null;

  return (
    <div className="space-y-4">
      {/* Summary stats */}
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4 text-center">
          <p className="text-2xl font-bold text-slate-900 dark:text-slate-50">{clients.length}</p>
          <p className="text-xs text-slate-400 mt-1">客戶數</p>
        </div>
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4 text-center">
          <p className="text-2xl font-bold text-slate-900 dark:text-slate-50">{industries.length}</p>
          <p className="text-xs text-slate-400 mt-1">產業別</p>
        </div>
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4 text-center">
          <p className="text-2xl font-bold text-blue-500">{formatBudget(grandTotal)}</p>
          <p className="text-xs text-slate-400 mt-1">商機總額</p>
        </div>
      </div>

      {/* Heatmap */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-200 dark:border-slate-700">
                <th className="text-left text-xs font-semibold text-slate-500 dark:text-slate-400 p-3 w-48 min-w-[192px]">
                  產業
                </th>
                {markets.map((m) => (
                  <th key={m} className="text-center text-xs font-semibold text-slate-500 dark:text-slate-400 p-3 w-32">
                    {marketLabel(m)}
                    <span className="block text-[10px] font-normal text-slate-400 mt-0.5">
                      {marketTotals[m]?.count || 0} 家 · {formatBudget(marketTotals[m]?.budget || 0)}
                    </span>
                  </th>
                ))}
                <th className="text-center text-xs font-semibold text-slate-500 dark:text-slate-400 p-3 w-28">
                  小計
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {industries.map((ind) => (
                <tr key={ind} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30 transition-colors">
                  <td className="p-3 text-sm text-slate-700 dark:text-slate-300 font-medium whitespace-nowrap">
                    {industryLabel(ind)}
                  </td>
                  {markets.map((mkt) => {
                    const cell = grid[ind]?.[mkt];
                    const cellKey = `${ind}|||${mkt}`;
                    if (!cell) {
                      return (
                        <td key={mkt} className="p-1.5">
                          <div className="h-14 rounded-lg bg-slate-50 dark:bg-slate-800/30" />
                        </td>
                      );
                    }
                    return (
                      <td key={mkt} className="p-1.5">
                        <div
                          className={`relative h-14 rounded-lg ${getIntensity(cell.totalBudget)} cursor-pointer transition-all hover:ring-2 hover:ring-blue-500/50`}
                          onMouseEnter={() => setHoveredCell(cellKey)}
                          onMouseLeave={() => setHoveredCell(null)}
                        >
                          <div className={`absolute inset-0 flex flex-col items-center justify-center ${getTextColor(cell.totalBudget)}`}>
                            <span className="text-sm font-bold">{cell.count}</span>
                            <span className="text-[10px] opacity-80">{formatBudget(cell.totalBudget)}</span>
                          </div>
                        </div>
                      </td>
                    );
                  })}
                  <td className="p-3 text-center">
                    <span className="text-xs font-semibold text-slate-600 dark:text-slate-300">
                      {industryTotals[ind]?.count || 0} 家
                    </span>
                    <span className="block text-[10px] text-slate-400">
                      {formatBudget(industryTotals[ind]?.budget || 0)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Hover detail panel */}
      {hoveredData && (
        <div className="bg-white dark:bg-slate-900 border border-blue-500/30 rounded-xl p-4 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold text-slate-900 dark:text-slate-50">
              {hoveredData.count} 家客戶 · {formatBudget(hoveredData.totalBudget)}
            </span>
          </div>
          <div className="divide-y divide-slate-100 dark:divide-slate-800">
            {hoveredData.clients
              .sort((a, b) => (b.deal_budget_total ?? 0) - (a.deal_budget_total ?? 0))
              .map((c) => (
                <Link
                  key={c.id}
                  href={`/contacts/clients/${c.id}`}
                  className="flex items-center justify-between py-1.5 text-sm hover:text-blue-500 transition-colors"
                >
                  <span className="text-slate-700 dark:text-slate-300 truncate">{c.name}</span>
                  <span className="text-xs text-slate-400 ml-2 flex-shrink-0">
                    {c.deal_count ? `${c.deal_count} 商機 · ` : ""}{formatBudget(c.deal_budget_total)}
                  </span>
                </Link>
              ))}
          </div>
        </div>
      )}

      {/* Industry bar chart */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4">
        <h4 className="text-sm font-semibold text-slate-900 dark:text-slate-50 mb-3">
          產業商機金額分布
        </h4>
        <div className="space-y-2">
          {industries.slice(0, 10).map((ind) => {
            const total = industryTotals[ind];
            const pct = grandTotal > 0 ? (total.budget / grandTotal) * 100 : 0;
            const domestic = grid[ind]?.domestic?.totalBudget ?? 0;
            const overseas = grid[ind]?.overseas?.totalBudget ?? 0;
            const domPct = total.budget > 0 ? (domestic / total.budget) * pct : 0;
            const oPct = total.budget > 0 ? (overseas / total.budget) * pct : 0;

            return (
              <div key={ind} className="flex items-center gap-3">
                <span className="text-xs text-slate-500 dark:text-slate-400 w-32 lg:w-44 truncate text-right flex-shrink-0">
                  {industryLabel(ind)}
                </span>
                <div className="flex-1 flex items-center gap-0.5 h-6">
                  {domPct > 0 && (
                    <div
                      className="h-full bg-blue-500 rounded-l transition-all"
                      style={{ width: `${Math.max(domPct, 1)}%` }}
                      title={`國內 ${formatBudget(domestic)}`}
                    />
                  )}
                  {oPct > 0 && (
                    <div
                      className="h-full bg-amber-500 rounded-r transition-all"
                      style={{ width: `${Math.max(oPct, 1)}%` }}
                      title={`海外 ${formatBudget(overseas)}`}
                    />
                  )}
                </div>
                <span className="text-xs text-slate-500 dark:text-slate-400 w-16 text-right flex-shrink-0">
                  {formatBudget(total.budget)}
                </span>
              </div>
            );
          })}
          {/* Legend */}
          <div className="flex items-center gap-4 mt-2 pt-2 border-t border-slate-100 dark:border-slate-800">
            <span className="flex items-center gap-1.5 text-[11px] text-slate-400">
              <span className="w-3 h-3 rounded-sm bg-blue-500" /> 國內
            </span>
            <span className="flex items-center gap-1.5 text-[11px] text-slate-400">
              <span className="w-3 h-3 rounded-sm bg-amber-500" /> 海外
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
