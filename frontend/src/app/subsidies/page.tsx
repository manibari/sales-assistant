"use client";

import { useState, useEffect, useMemo } from "react";
import { TopBar } from "@/components/top-bar";
import { nxApi, type NxSubsidy } from "@/lib/nexus-api";
import { AlertTriangle, Building2, Calendar, ChevronDown, ChevronRight, ChevronRightCircle, Clock, Handshake, Plus } from "lucide-react";
import Link from "next/link";

const STAGE_ORDER = [
  "executing", "approved", "under_review", "applying",
  "evaluating", "draft", "rejected", "completed",
];

const STAGE_LABELS: Record<string, string> = {
  draft: "草稿",
  evaluating: "評估中",
  applying: "申請中",
  under_review: "審查中",
  approved: "核定",
  rejected: "未通過",
  executing: "執行中",
  completed: "結案",
};

const STAGE_COLORS: Record<string, string> = {
  draft: "bg-slate-500/10 text-slate-500",
  evaluating: "bg-blue-500/10 text-blue-400",
  applying: "bg-cyan-500/10 text-cyan-400",
  under_review: "bg-amber-500/10 text-amber-400",
  approved: "bg-green-500/10 text-green-400",
  rejected: "bg-red-500/10 text-red-400",
  executing: "bg-purple-500/10 text-purple-400",
  completed: "bg-slate-500/10 text-slate-400",
};

const TYPE_LABELS: Record<string, string> = {
  sbir: "SBIR",
  siir: "SIIR",
  local: "地方型",
  other: "其他",
};

const VIEW_LABELS: Record<string, string> = {
  stage: "階段",
  deadline: "截止日",
};
const VIEW_ORDER: Array<"stage" | "deadline"> = ["stage", "deadline"];

function deadlineBorderColor(days: number | null): string {
  if (days === null) return "border-l-slate-300 dark:border-l-slate-600";
  if (days < 0) return "border-l-slate-400";
  if (days <= 30) return "border-l-red-500";
  if (days <= 60) return "border-l-amber-500";
  return "border-l-green-500";
}

function formatDeadlineDate(dateStr: string | null): string {
  if (!dateStr) return "";
  const d = new Date(dateStr + "T00:00:00");
  return d.toLocaleDateString("zh-TW", { month: "numeric", day: "numeric" });
}

export default function SubsidiesPage() {
  const [subsidies, setSubsidies] = useState<NxSubsidy[]>([]);
  const [view, setView] = useState<"stage" | "deadline">("stage");
  const [filter, setFilter] = useState<"all" | "urgent" | "upcoming" | "nodate">("all");
  const [collapsed, setCollapsed] = useState<Record<string, boolean>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    nxApi.subsidies
      .list(view)
      .then(setSubsidies)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [view]);

  const toggleCollapse = (key: string) => {
    setCollapsed((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const handleAdvance = async (id: number, stage: string) => {
    try {
      const updated = await nxApi.subsidies.advance(id, stage);
      setSubsidies((prev) => prev.map((s) => (s.id === id ? { ...s, ...updated } : s)));
    } catch (err) {
      console.error("Advance failed:", err);
    }
  };

  // Deadline summary stats (always from full list)
  const deadlineStats = useMemo(() => {
    const withDate = subsidies.filter((s) => s.days_left != null);
    const urgent = withDate.filter((s) => s.days_left! >= 0 && s.days_left! <= 30);
    const upcoming = withDate.filter((s) => s.days_left! > 30 && s.days_left! <= 90);
    const noDate = subsidies.filter((s) => s.days_left == null);
    return { urgent, upcoming, noDate, withDate };
  }, [subsidies]);

  // Filtered list
  const filtered = useMemo(() => {
    if (filter === "all") return subsidies;
    if (filter === "urgent") return subsidies.filter((s) => s.days_left != null && s.days_left >= 0 && s.days_left <= 30);
    if (filter === "upcoming") return subsidies.filter((s) => s.days_left != null && s.days_left > 30 && s.days_left <= 90);
    return subsidies.filter((s) => s.days_left == null);
  }, [subsidies, filter]);

  // Groups for deadline view
  const deadlineGroups = useMemo(() => {
    const groups: { label: string; color: string; items: NxSubsidy[] }[] = [];
    const urgent = filtered.filter((s) => s.days_left != null && s.days_left >= 0 && s.days_left <= 30);
    const soon = filtered.filter((s) => s.days_left != null && s.days_left > 30 && s.days_left <= 90);
    const later = filtered.filter((s) => s.days_left != null && s.days_left > 90);
    const noDate = filtered.filter((s) => s.days_left == null);
    if (urgent.length) groups.push({ label: "30 天內", color: "text-red-500", items: urgent });
    if (soon.length) groups.push({ label: "30–90 天", color: "text-amber-500", items: soon });
    if (later.length) groups.push({ label: "90 天以上", color: "text-green-500", items: later });
    if (noDate.length) groups.push({ label: "未定 / 隨到隨審", color: "text-slate-400", items: noDate });
    return groups;
  }, [filtered]);

  const grouped = filtered.reduce<Record<string, NxSubsidy[]>>((acc, s) => {
    const key = s.stage;
    if (!acc[key]) acc[key] = [];
    acc[key].push(s);
    return acc;
  }, {});

  return (
    <div className="flex flex-col h-full">
      <TopBar title="補助案">
        <Link
          href="/subsidies/new"
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
        ) : subsidies.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-slate-400 dark:text-slate-500">
            <p className="text-sm">尚無補助案</p>
            <p className="text-xs mt-1">點右上角新增第一個補助案</p>
          </div>
        ) : (
          <div className="max-w-2xl lg:max-w-4xl mx-auto">
            {/* Deadline summary banner */}
            {deadlineStats.urgent.length > 0 && (
              <div className="mb-4 bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3 flex items-center gap-3">
                <AlertTriangle size={18} className="text-red-500 flex-shrink-0" />
                <div className="flex-1">
                  <p className="text-sm font-semibold text-red-500">
                    {deadlineStats.urgent.length} 個補助案將在 30 天內截止
                  </p>
                  <p className="text-xs text-red-400 mt-0.5">
                    {deadlineStats.urgent.map((s) => `${s.name.slice(0, 15)}(${s.days_left}天)`).join("、")}
                  </p>
                </div>
              </div>
            )}

            {/* Filter chips */}
            <div className="flex gap-2 mb-4 flex-wrap">
              <FilterChip active={filter === "all"} onClick={() => setFilter("all")} dotColor="bg-blue-500" label="全部" count={subsidies.length} />
              <FilterChip active={filter === "urgent"} onClick={() => setFilter("urgent")} dotColor="bg-red-500" label="≤30天" count={deadlineStats.urgent.length} />
              <FilterChip active={filter === "upcoming"} onClick={() => setFilter("upcoming")} dotColor="bg-amber-500" label="30-90天" count={deadlineStats.upcoming.length} />
              <FilterChip active={filter === "nodate"} onClick={() => setFilter("nodate")} dotColor="bg-slate-400" label="隨到隨審" count={deadlineStats.noDate.length} />
            </div>

            {view === "stage" ? (
              <div className="space-y-4">
                {STAGE_ORDER.map((stage) => {
                  const items = grouped[stage];
                  if (!items || items.length === 0) return null;
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
                          ({items.length})
                        </span>
                      </button>
                      {!isCollapsed && (
                        <div className="space-y-3 mt-1 lg:grid lg:grid-cols-2 lg:gap-4 lg:space-y-0">
                          {items.map((s) => (
                            <SubsidyCard key={s.id} subsidy={s} onAdvance={handleAdvance} />
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            ) : (
              /* Deadline view — grouped by urgency */
              <div className="space-y-4">
                {deadlineGroups.map((group) => {
                  const key = group.label;
                  const isCollapsed = collapsed[key];
                  return (
                    <div key={key}>
                      <button
                        onClick={() => toggleCollapse(key)}
                        className="flex items-center gap-2 w-full text-left px-2 py-2 cursor-pointer"
                      >
                        {isCollapsed ? (
                          <ChevronRight size={16} className="text-slate-400" />
                        ) : (
                          <ChevronDown size={16} className="text-slate-400" />
                        )}
                        <Clock size={14} className={group.color} />
                        <span className={`text-xs font-semibold uppercase tracking-wider ${group.color}`}>
                          {group.label}
                        </span>
                        <span className="text-xs text-slate-400 dark:text-slate-500">
                          ({group.items.length})
                        </span>
                      </button>
                      {!isCollapsed && (
                        <div className="space-y-3 mt-1 lg:grid lg:grid-cols-2 lg:gap-4 lg:space-y-0">
                          {group.items.map((s) => (
                            <SubsidyCard key={s.id} subsidy={s} onAdvance={handleAdvance} />
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function FilterChip({ active, onClick, dotColor, label, count }: {
  active: boolean; onClick: () => void; dotColor: string; label: string; count: number;
}) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 rounded-lg px-3 py-2 text-xs transition-colors cursor-pointer border ${
        active
          ? "bg-blue-500/10 border-blue-500/30 text-blue-500 font-semibold"
          : "bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-700 text-slate-500 dark:text-slate-400 hover:border-blue-500/50"
      }`}
    >
      <div className={`w-2 h-2 rounded-full ${dotColor}`} />
      {label}
      <span className={`font-bold ${active ? "text-blue-500" : "text-slate-900 dark:text-slate-50"}`}>{count}</span>
    </button>
  );
}

const STAGE_PROGRESSION = [
  "draft", "evaluating", "applying", "under_review",
  "approved", "executing", "completed",
];

function getNextStage(current: string): string | null {
  const idx = STAGE_PROGRESSION.indexOf(current);
  if (idx === -1 || idx >= STAGE_PROGRESSION.length - 1) return null;
  return STAGE_PROGRESSION[idx + 1];
}

function SubsidyCard({ subsidy, onAdvance }: { subsidy: NxSubsidy; onAdvance?: (id: number, stage: string) => void }) {
  const days = subsidy.days_left;
  const borderColor = deadlineBorderColor(days ?? null);
  const hasDate = subsidy.deadline_date != null;
  const nextStage = getNextStage(subsidy.stage);

  return (
    <div className={`relative bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4 transition-colors duration-200 hover:border-slate-300 dark:hover:border-slate-600 border-l-4 ${borderColor}`}>
      <Link
        href={`/subsidies/${subsidy.id}`}
        className="block cursor-pointer active:bg-slate-50 dark:active:bg-slate-800"
      >
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-50 line-clamp-2 leading-snug">
              {subsidy.name}
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 truncate">
              {subsidy.agency || "—"}
            </p>
          </div>
          <div className="flex flex-col items-end gap-1 flex-shrink-0">
            <span className={`text-[11px] px-2 py-0.5 rounded-full font-medium ${STAGE_COLORS[subsidy.stage] || "bg-slate-500/10 text-slate-400"}`}>
              {STAGE_LABELS[subsidy.stage] || subsidy.stage}
            </span>
            <span className="text-[11px] px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 font-medium">
              {TYPE_LABELS[subsidy.program_type] || subsidy.program_type}
            </span>
          </div>
        </div>

        {/* Client / Partner row */}
        {(subsidy.client_name || subsidy.partner_name) && (
          <div className="mt-2 flex items-center gap-3 flex-wrap">
            {subsidy.client_name && (
              <span className="flex items-center gap-1 text-[11px] text-slate-500 dark:text-slate-400">
                <Building2 size={11} className="text-blue-400" />
                {subsidy.client_name}
              </span>
            )}
            {subsidy.partner_name && (
              <span className="flex items-center gap-1 text-[11px] text-slate-500 dark:text-slate-400">
                <Handshake size={11} className="text-green-400" />
                {subsidy.partner_name}
              </span>
            )}
          </div>
        )}

        {/* Deadline row — enhanced */}
        <div className="mt-2 flex items-center justify-between">
          <div className="flex items-center gap-2">
            {hasDate ? (
              <>
                <Calendar size={12} className={
                  days != null && days <= 30 ? "text-red-500" :
                  days != null && days <= 60 ? "text-amber-500" : "text-slate-400"
                } />
                <span className={`text-xs font-medium ${
                  days != null && days <= 30 ? "text-red-500" :
                  days != null && days <= 60 ? "text-amber-500" :
                  "text-slate-500 dark:text-slate-400"
                }`}>
                  {formatDeadlineDate(subsidy.deadline_date)}
                </span>
                {days != null && days >= 0 && (
                  <span className={`text-[11px] px-1.5 py-0.5 rounded font-bold ${
                    days <= 14 ? "bg-red-500 text-white animate-pulse" :
                    days <= 30 ? "bg-red-500/15 text-red-500" :
                    days <= 60 ? "bg-amber-500/15 text-amber-500" :
                    "bg-green-500/10 text-green-500"
                  }`}>
                    {days === 0 ? "今天截止" : days <= 7 ? `剩 ${days} 天！` : `${days} 天`}
                  </span>
                )}
                {days != null && days < 0 && (
                  <span className="text-[11px] px-1.5 py-0.5 rounded bg-slate-500/10 text-slate-400 font-medium">
                    已截止
                  </span>
                )}
              </>
            ) : subsidy.deadline ? (
              <span className="text-[11px] text-slate-400 truncate max-w-[200px]">
                {subsidy.deadline.slice(0, 30)}{subsidy.deadline.length > 30 ? "..." : ""}
              </span>
            ) : null}
          </div>
          {subsidy.funding_amount && (
            <span className="text-[11px] text-slate-400 dark:text-slate-500 truncate max-w-[120px]">
              {subsidy.funding_amount.slice(0, 20)}
            </span>
          )}
        </div>
      </Link>

      {/* Quick advance button */}
      {nextStage && onAdvance && (
        <button
          onClick={(e) => {
            e.stopPropagation();
            onAdvance(subsidy.id, nextStage);
          }}
          className="mt-2 w-full flex items-center justify-center gap-1.5 py-1.5 rounded-lg text-[11px] font-medium text-blue-500 bg-blue-500/5 hover:bg-blue-500/10 border border-blue-500/20 transition-colors cursor-pointer"
        >
          <ChevronRightCircle size={13} />
          推進至「{STAGE_LABELS[nextStage]}」
        </button>
      )}
    </div>
  );
}
