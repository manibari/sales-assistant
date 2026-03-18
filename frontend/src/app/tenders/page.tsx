"use client";

import { useState, useEffect, useMemo } from "react";
import { TopBar } from "@/components/top-bar";
import { nxApi, type NxTender } from "@/lib/nexus-api";
import Link from "next/link";
import { Calendar, FileText, Gavel } from "lucide-react";

const CLASS_FILTERS = ["全部", "招標公告", "公開徵求", "公開閱覽", "採購預告"] as const;
type ClassFilter = (typeof CLASS_FILTERS)[number];

const CLASS_COLORS: Record<string, string> = {
  招標公告: "bg-blue-500/10 text-blue-600 dark:text-blue-400",
  公開徵求: "bg-purple-500/10 text-purple-600 dark:text-purple-400",
  公開閱覽: "bg-amber-500/10 text-amber-600 dark:text-amber-400",
  採購預告: "bg-slate-200/60 text-slate-500 dark:bg-slate-700/60 dark:text-slate-400",
};

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
  const [filter, setFilter] = useState<ClassFilter>("全部");
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
    return tenders.filter((t) => t.tender_class === filter);
  }, [tenders, filter]);

  const classCounts = useMemo(() => {
    const counts: Record<string, number> = { 全部: tenders.length };
    for (const t of tenders) {
      const cls = t.tender_class || "招標公告";
      counts[cls] = (counts[cls] || 0) + 1;
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
              {CLASS_FILTERS.map((cls) => {
                const count = classCounts[cls] || 0;
                if (cls !== "全部" && count === 0) return null;
                const active = filter === cls;
                return (
                  <button
                    key={cls}
                    onClick={() => setFilter(cls)}
                    className={`flex items-center gap-2 rounded-lg px-3 py-2 text-xs transition-colors cursor-pointer border ${
                      active
                        ? "bg-blue-500/10 border-blue-500/30 text-blue-500 font-semibold"
                        : "bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-700 text-slate-500 dark:text-slate-400 hover:border-blue-500/50"
                    }`}
                  >
                    {cls}
                    <span
                      className={`font-bold ${active ? "text-blue-500" : "text-slate-900 dark:text-slate-50"}`}
                    >
                      {count}
                    </span>
                  </button>
                );
              })}
            </div>

            {/* Tender cards grouped by class */}
            <div className="space-y-3 lg:grid lg:grid-cols-2 lg:gap-4 lg:space-y-0">
              {filtered.map((t) => (
                <Link
                  key={t.job_number}
                  href={`/tenders/${encodeURIComponent(t.job_number)}`}
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
                      <span
                        className={`text-[11px] px-2 py-0.5 rounded-full font-medium ${
                          CLASS_COLORS[t.tender_class || "招標公告"] || CLASS_COLORS["招標公告"]
                        }`}
                      >
                        {t.tender_class || "招標公告"}
                      </span>
                      {t.has_notice && (
                        <FileText size={12} className="text-green-500" />
                      )}
                    </div>
                  </div>

                  {/* Meta row: category + deadline + budget */}
                  <div className="mt-2 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-400">
                        {t.category}
                      </span>
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
                </Link>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
