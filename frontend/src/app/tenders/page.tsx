"use client";

import { useState, useEffect, useMemo } from "react";
import { TopBar } from "@/components/top-bar";
import { nxApi, type NxTender } from "@/lib/nexus-api";
import { Calendar, ExternalLink, Gavel } from "lucide-react";

const CATEGORY_FILTERS = ["全部", "勞務", "財物", "工程", "其他"] as const;
type CategoryFilter = (typeof CATEGORY_FILTERS)[number];

function urgencyColor(days: number | null): string {
  if (days === null) return "border-l-slate-300 dark:border-l-slate-600";
  if (days <= 7) return "border-l-red-500";
  if (days <= 14) return "border-l-orange-500";
  return "border-l-green-500";
}

function daysLeftBadge(days: number | null) {
  if (days === null) return null;
  const color =
    days <= 7
      ? "bg-red-500 text-white"
      : days <= 14
        ? "bg-orange-500/15 text-orange-500"
        : "bg-green-500/10 text-green-500";
  const label = days === 0 ? "今天截止" : days < 0 ? "已截止" : `${days} 天`;
  return (
    <span className={`text-[11px] px-1.5 py-0.5 rounded font-bold ${color}`}>
      {label}
    </span>
  );
}

export default function TendersPage() {
  const [tenders, setTenders] = useState<NxTender[]>([]);
  const [filter, setFilter] = useState<CategoryFilter>("全部");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    nxApi.tenders
      .list()
      .then(setTenders)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(() => {
    if (filter === "全部") return tenders;
    return tenders.filter((t) => t.category === filter);
  }, [tenders, filter]);

  const categoryCounts = useMemo(() => {
    const counts: Record<string, number> = { 全部: tenders.length };
    for (const t of tenders) {
      counts[t.category] = (counts[t.category] || 0) + 1;
    }
    return counts;
  }, [tenders]);

  return (
    <div className="flex flex-col h-full">
      <TopBar title="政府標案">
        <div className="flex items-center gap-1.5 text-xs text-slate-400">
          <Gavel size={14} />
          {tenders.length} 筆等標中
        </div>
      </TopBar>

      <div className="flex-1 px-4 lg:px-6 py-4 overflow-auto">
        {loading ? (
          <div className="flex items-center justify-center py-20 text-slate-400">
            載入中...
          </div>
        ) : tenders.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-slate-400 dark:text-slate-500">
            <p className="text-sm">尚無標案資料</p>
            <p className="text-xs mt-1">等待 tender-scraper 爬取案件</p>
          </div>
        ) : (
          <div className="max-w-2xl lg:max-w-4xl mx-auto">
            {/* Filter chips */}
            <div className="flex gap-2 mb-4 flex-wrap">
              {CATEGORY_FILTERS.map((cat) => {
                const count = categoryCounts[cat] || 0;
                if (cat !== "全部" && count === 0) return null;
                const active = filter === cat;
                return (
                  <button
                    key={cat}
                    onClick={() => setFilter(cat)}
                    className={`flex items-center gap-2 rounded-lg px-3 py-2 text-xs transition-colors cursor-pointer border ${
                      active
                        ? "bg-blue-500/10 border-blue-500/30 text-blue-500 font-semibold"
                        : "bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-700 text-slate-500 dark:text-slate-400 hover:border-blue-500/50"
                    }`}
                  >
                    {cat}
                    <span
                      className={`font-bold ${active ? "text-blue-500" : "text-slate-900 dark:text-slate-50"}`}
                    >
                      {count}
                    </span>
                  </button>
                );
              })}
            </div>

            {/* Tender cards */}
            <div className="space-y-3 lg:grid lg:grid-cols-2 lg:gap-4 lg:space-y-0">
              {filtered.map((t) => (
                <a
                  key={t.job_number}
                  href={t.reference_url || "#"}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={`block bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4 transition-colors duration-200 hover:border-slate-300 dark:hover:border-slate-600 border-l-4 ${urgencyColor(t.days_left)} cursor-pointer group`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-50 line-clamp-2 leading-snug group-hover:text-blue-500 transition-colors">
                        {t.name}
                      </h3>
                      <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 truncate">
                        {t.agency}
                      </p>
                    </div>
                    <div className="flex flex-col items-end gap-1 flex-shrink-0">
                      <span className="text-[11px] px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 font-medium">
                        {t.category}
                      </span>
                      <ExternalLink
                        size={12}
                        className="text-slate-300 dark:text-slate-600 group-hover:text-blue-400 transition-colors"
                      />
                    </div>
                  </div>

                  {/* Deadline + budget row */}
                  <div className="mt-2 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {t.deadline && (
                        <>
                          <Calendar
                            size={12}
                            className={
                              t.days_left != null && t.days_left <= 7
                                ? "text-red-500"
                                : t.days_left != null && t.days_left <= 14
                                  ? "text-orange-500"
                                  : "text-slate-400"
                            }
                          />
                          <span
                            className={`text-xs font-medium ${
                              t.days_left != null && t.days_left <= 7
                                ? "text-red-500"
                                : t.days_left != null && t.days_left <= 14
                                  ? "text-orange-500"
                                  : "text-slate-500 dark:text-slate-400"
                            }`}
                          >
                            {new Date(t.deadline + "T00:00:00").toLocaleDateString(
                              "zh-TW",
                              { month: "numeric", day: "numeric" },
                            )}
                          </span>
                          {daysLeftBadge(t.days_left)}
                        </>
                      )}
                    </div>
                    {t.budget_amount && (
                      <span className="text-[11px] text-slate-400 dark:text-slate-500">
                        {t.budget_amount}
                      </span>
                    )}
                  </div>

                  {/* Tags */}
                  {t.tags && t.tags.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {t.tags.slice(0, 4).map((tag) => (
                        <span
                          key={tag}
                          className="text-[10px] px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </a>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
