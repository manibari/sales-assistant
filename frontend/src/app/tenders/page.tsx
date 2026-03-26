"use client";

import { useState, useEffect, useMemo, useRef } from "react";
import { TopBar } from "@/components/top-bar";
import { nxApi, type NxTender } from "@/lib/nexus-api";
import Link from "next/link";
import { Calendar, FileText, Gavel, ChevronDown, X, RotateCcw } from "lucide-react";

/* ── Tender class (招標類型) ── */
const CLASS_FILTERS = ["全部", "招標公告", "公開徵求", "公開閱覽", "採購預告"] as const;
type ClassFilter = (typeof CLASS_FILTERS)[number];

const CLASS_COLORS: Record<string, string> = {
  招標公告: "bg-blue-500/10 text-blue-600 dark:text-blue-400",
  公開徵求: "bg-purple-500/10 text-purple-600 dark:text-purple-400",
  公開閱覽: "bg-amber-500/10 text-amber-600 dark:text-amber-400",
  採購預告: "bg-slate-200/60 text-slate-500 dark:bg-slate-700/60 dark:text-slate-400",
};

/* ── Tracking status (追蹤狀態) ── */
const TRACKING_STATUSES = [
  { key: "all", label: "全部" },
  { key: "unreviewed", label: "未分類" },
  { key: "evaluating", label: "評估中" },
  { key: "preparing", label: "準備中" },
  { key: "submitted", label: "已投標" },
  { key: "reviewing", label: "審查中" },
  { key: "awarded", label: "得標" },
  { key: "lost", label: "未得標" },
  { key: "skipped", label: "不投" },
] as const;

const TRACKING_COLORS: Record<string, string> = {
  unreviewed: "bg-slate-200/60 text-slate-500 dark:bg-slate-700/60 dark:text-slate-400",
  evaluating: "bg-sky-500/10 text-sky-600 dark:text-sky-400",
  preparing: "bg-amber-500/10 text-amber-600 dark:text-amber-400",
  submitted: "bg-indigo-500/10 text-indigo-600 dark:text-indigo-400",
  reviewing: "bg-violet-500/10 text-violet-600 dark:text-violet-400",
  awarded: "bg-green-500/10 text-green-600 dark:text-green-400",
  lost: "bg-red-500/10 text-red-500 dark:text-red-400",
  skipped: "bg-slate-300/40 text-slate-400 dark:bg-slate-700/40 dark:text-slate-500",
  dismissed: "bg-slate-300/40 text-slate-400 dark:bg-slate-700/40 dark:text-slate-500",
};

function trackingLabel(key: string): string {
  if (key === "dismissed") return "略過";
  return TRACKING_STATUSES.find((s) => s.key === key)?.label ?? key;
}

/* ── Urgency helpers ── */
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

/* ── Inline status dropdown ── */
function TrackingStatusDropdown({
  tender,
  onUpdate,
}: {
  tender: NxTender;
  onUpdate: (jobNumber: string, status: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    if (open) document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [open]);

  const current = tender.tracking_status || "unreviewed";

  return (
    <div ref={ref} className="relative">
      <button
        onClick={(e) => {
          e.preventDefault();
          e.stopPropagation();
          setOpen(!open);
        }}
        className={`flex items-center gap-0.5 text-[11px] px-2 py-0.5 rounded-full font-medium cursor-pointer transition-colors hover:ring-1 hover:ring-slate-300 dark:hover:ring-slate-600 ${TRACKING_COLORS[current] || TRACKING_COLORS.unreviewed}`}
      >
        {trackingLabel(current)}
        <ChevronDown size={10} />
      </button>
      {open && (
        <div className="absolute right-0 top-full mt-1 z-50 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg shadow-lg py-1 min-w-[100px]">
          {TRACKING_STATUSES.filter((s) => s.key !== "all").map((s) => (
            <button
              key={s.key}
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                onUpdate(tender.job_number, s.key);
                setOpen(false);
              }}
              className={`w-full text-left px-3 py-1.5 text-xs hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors cursor-pointer ${
                current === s.key ? "font-semibold text-blue-500" : "text-slate-600 dark:text-slate-300"
              }`}
            >
              <span className={`inline-block w-2 h-2 rounded-full mr-2 ${TRACKING_COLORS[s.key]?.split(" ")[0] || "bg-slate-300"}`} />
              {s.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

type Tab = "active" | "past";

/* ── Main page ── */
export default function TendersPage() {
  const [tenders, setTenders] = useState<NxTender[]>([]);
  const [tab, setTab] = useState<Tab>("active");
  const [classFilter, setClassFilter] = useState<ClassFilter>("全部");
  const [trackingFilter, setTrackingFilter] = useState("all");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    nxApi.tenders
      .list()
      .then(setTenders)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const today = new Date().toISOString().slice(0, 10);

  // Split into active vs past
  const activeTenders = useMemo(
    () => tenders.filter((t) => {
      const ts = t.tracking_status || "unreviewed";
      if (ts === "dismissed") return false;
      // Expired with active status → past
      if (t.deadline && t.deadline < today && t.status === "active") return false;
      return true;
    }),
    [tenders, today],
  );

  const pastTenders = useMemo(
    () => tenders.filter((t) => {
      const ts = t.tracking_status || "unreviewed";
      if (ts === "dismissed") return true;
      if (t.deadline && t.deadline < today && t.status === "active") return true;
      return false;
    }),
    [tenders, today],
  );

  const currentTenders = tab === "active" ? activeTenders : pastTenders;

  const filtered = useMemo(() => {
    let result = currentTenders;
    if (classFilter !== "全部") result = result.filter((t) => t.tender_class === classFilter);
    if (tab === "active" && trackingFilter !== "all") result = result.filter((t) => (t.tracking_status || "unreviewed") === trackingFilter);
    return result;
  }, [currentTenders, classFilter, trackingFilter, tab]);

  const classCounts = useMemo(() => {
    const counts: Record<string, number> = { 全部: currentTenders.length };
    for (const t of currentTenders) {
      const cls = t.tender_class || "招標公告";
      counts[cls] = (counts[cls] || 0) + 1;
    }
    return counts;
  }, [currentTenders]);

  const trackingCounts = useMemo(() => {
    const counts: Record<string, number> = { all: currentTenders.length };
    for (const t of currentTenders) {
      const ts = t.tracking_status || "unreviewed";
      counts[ts] = (counts[ts] || 0) + 1;
    }
    return counts;
  }, [currentTenders]);

  async function handleTrackingUpdate(jobNumber: string, status: string) {
    try {
      await nxApi.tenders.updateTrackingStatus(jobNumber, status);
      setTenders((prev) =>
        prev.map((t) =>
          t.job_number === jobNumber ? { ...t, tracking_status: status } : t,
        ),
      );
    } catch (err) {
      console.error("Failed to update tracking status:", err);
    }
  }

  async function handleDismiss(jobNumber: string) {
    await handleTrackingUpdate(jobNumber, "dismissed");
  }

  async function handleUndismiss(jobNumber: string) {
    await handleTrackingUpdate(jobNumber, "unreviewed");
  }

  return (
    <div className="flex flex-col h-full">
      <TopBar title="政府標案">
        <div className="flex items-center gap-1.5 text-xs text-slate-400">
          <Gavel size={14} />
          {tenders.length} 筆
        </div>
      </TopBar>

      <div className="flex-1 px-4 lg:px-6 py-4 overflow-auto">
        {/* Tab switcher */}
        <div className="max-w-2xl lg:max-w-4xl mx-auto mb-4">
          <div className="flex gap-1 bg-slate-100 dark:bg-slate-800 rounded-lg p-1">
            <button
              onClick={() => { setTab("active"); setTrackingFilter("all"); }}
              className={`flex-1 py-2 text-sm font-medium rounded-md transition-colors cursor-pointer ${
                tab === "active"
                  ? "bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-50 shadow-sm"
                  : "text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300"
              }`}
            >
              進行中 ({activeTenders.length})
            </button>
            <button
              onClick={() => { setTab("past"); setTrackingFilter("all"); }}
              className={`flex-1 py-2 text-sm font-medium rounded-md transition-colors cursor-pointer ${
                tab === "past"
                  ? "bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-50 shadow-sm"
                  : "text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300"
              }`}
            >
              過去的 ({pastTenders.length})
            </button>
          </div>
        </div>

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
            {/* Tracking status filter — active tab only */}
            {tab === "active" && (
              <div className="flex gap-1.5 mb-3 flex-wrap">
                {TRACKING_STATUSES.map((s) => {
                  const count = trackingCounts[s.key] || 0;
                  if (s.key !== "all" && count === 0) return null;
                  const active = trackingFilter === s.key;
                  return (
                    <button
                      key={s.key}
                      onClick={() => setTrackingFilter(s.key)}
                      className={`flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-[11px] transition-colors cursor-pointer border ${
                        active
                          ? "bg-blue-500/10 border-blue-500/30 text-blue-500 font-semibold"
                          : "bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-700 text-slate-500 dark:text-slate-400 hover:border-blue-500/50"
                      }`}
                    >
                      {s.label}
                      <span className={`font-bold ${active ? "text-blue-500" : "text-slate-900 dark:text-slate-50"}`}>
                        {count}
                      </span>
                    </button>
                  );
                })}
              </div>
            )}

            {/* Class filter chips */}
            <div className="flex gap-2 mb-4 flex-wrap">
              {CLASS_FILTERS.map((cls) => {
                const count = classCounts[cls] || 0;
                if (cls !== "全部" && count === 0) return null;
                const active = classFilter === cls;
                return (
                  <button
                    key={cls}
                    onClick={() => setClassFilter(cls)}
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

            {/* Tender cards */}
            <div className="space-y-3 lg:grid lg:grid-cols-2 lg:gap-4 lg:space-y-0">
              {filtered.map((t) => (
                <div
                  key={t.job_number}
                  className={`relative bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4 transition-colors duration-200 hover:border-slate-300 dark:hover:border-slate-600 border-l-4 ${urgencyColor(t.days_left)} group`}
                >
                  <Link
                    href={`/tenders/${encodeURIComponent(t.job_number)}`}
                    className="block cursor-pointer"
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
                      <div className="flex flex-col items-end gap-1.5 flex-shrink-0">
                        <TrackingStatusDropdown tender={t} onUpdate={handleTrackingUpdate} />
                        <span
                          className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium ${
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

                    {/* Meta row */}
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

                  {/* Dismiss / Restore button */}
                  {tab === "active" && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDismiss(t.job_number);
                      }}
                      className="mt-2 flex items-center justify-center gap-1 w-full py-1.5 rounded-lg text-[11px] font-medium text-slate-400 hover:text-red-500 bg-slate-50 dark:bg-slate-800 hover:bg-red-500/10 border border-slate-200 dark:border-slate-700 hover:border-red-500/20 transition-colors cursor-pointer"
                      title="略過此標案"
                    >
                      <X size={13} />
                      略過
                    </button>
                  )}
                  {tab === "past" && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleUndismiss(t.job_number);
                      }}
                      className="mt-2 flex items-center justify-center gap-1.5 w-full py-1.5 rounded-lg text-[11px] font-medium text-green-500 bg-green-500/5 hover:bg-green-500/10 border border-green-500/20 transition-colors cursor-pointer"
                    >
                      <RotateCcw size={13} />
                      還原
                    </button>
                  )}
                </div>
              ))}

              {filtered.length === 0 && (
                <div className="col-span-2 text-center py-12 text-slate-400 text-sm">
                  {tab === "active" ? "此篩選條件下無標案" : "尚無過去的標案"}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
