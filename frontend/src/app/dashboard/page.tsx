"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import { TopBar } from "@/components/top-bar";
import {
  AlertTriangle,
  Bell,
  Calendar,
  ChevronRight,
  CircleDot,
  DollarSign,
  Landmark,
  Loader2,
  Search,
  TrendingUp,
} from "lucide-react";
import { nxApi, type NxDeal, type NxReminder, type NxMeeting, type NxTbdItem, type NxSubsidy } from "@/lib/nexus-api";
import { formatBudget } from "@/lib/options";
import Link from "next/link";

const STAGE_LABELS: Record<string, string> = {
  L0: "L0 潛在",
  L1: "L1 接觸",
  L2: "L2 需求",
  L3: "L3 報價",
  L4: "L4 簽約",
};

const STAGE_COLORS: Record<string, string> = {
  L0: "bg-slate-400",
  L1: "bg-blue-400",
  L2: "bg-cyan-400",
  L3: "bg-amber-400",
  L4: "bg-green-400",
};

function getBudgetAmount(deal: NxDeal): number {
  return deal.budget_amount || 0;
}

export default function DashboardPage() {
  const [allDeals, setAllDeals] = useState<NxDeal[]>([]);
  const [pushDeals, setPushDeals] = useState<NxDeal[]>([]);
  const [reminders, setReminders] = useState<NxReminder[]>([]);
  const [meetings, setMeetings] = useState<NxMeeting[]>([]);
  const [staleTbds, setStaleTbds] = useState<NxTbdItem[]>([]);
  const [expiringSubsidies, setExpiringSubsidies] = useState<NxSubsidy[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = useCallback(async () => {
    try {
      const today = new Date().toISOString().split("T")[0];
      const [all, push, rems, mtgs, tbds, expSubs] = await Promise.all([
        nxApi.deals.list(),
        nxApi.deals.needsPush(7),
        nxApi.calendar.pendingReminders(),
        nxApi.calendar.meetingsByDate(today),
        nxApi.tbd.list(),
        nxApi.subsidies.expiring(60),
      ]);
      setAllDeals(all);
      setPushDeals(push);
      setReminders(rems);
      setMeetings(mtgs);
      setStaleTbds(tbds.filter((t) => !t.resolved));
      setExpiringSubsidies(expSubs);
    } catch (err) {
      console.error("Dashboard load failed:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  const pipeline = useMemo(() => {
    const activeDeals = allDeals.filter((d) => d.status === "active");
    const totalValue = activeDeals.reduce((sum, d) => sum + getBudgetAmount(d), 0);
    const dealCount = activeDeals.length;

    const byStage: Record<string, { count: number; value: number }> = {};
    for (const stage of ["L0", "L1", "L2", "L3", "L4"]) {
      byStage[stage] = { count: 0, value: 0 };
    }
    for (const d of activeDeals) {
      const s = byStage[d.stage];
      if (s) {
        s.count++;
        s.value += getBudgetAmount(d);
      }
    }

    // Weighted pipeline (later stages = higher probability)
    const weights: Record<string, number> = { L0: 0.1, L1: 0.2, L2: 0.4, L3: 0.7, L4: 0.9 };
    const weightedValue = activeDeals.reduce(
      (sum, d) => sum + getBudgetAmount(d) * (weights[d.stage] || 0),
      0
    );

    return { totalValue, weightedValue, dealCount, byStage };
  }, [allDeals]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 size={24} className="animate-spin text-blue-500" />
      </div>
    );
  }

  const totalActions = pushDeals.length + reminders.length + staleTbds.length;

  return (
    <div className="flex flex-col h-full">
      <TopBar title="控制台">
        <Link
          href="/search"
          className="p-2 rounded-lg text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer transition-colors"
        >
          <Search size={20} />
        </Link>
      </TopBar>

      <div className="flex-1 px-4 lg:px-6 py-4 overflow-auto max-w-2xl lg:max-w-6xl mx-auto w-full">
        {/* Pipeline Summary — the core numbers */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-5 lg:p-6 mb-4">
          <div className="flex items-center gap-2 mb-4">
            <DollarSign size={16} className="text-green-500" />
            <span className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Pipeline Overview</span>
          </div>

          {/* Top metrics row */}
          <div className="grid grid-cols-3 gap-4 mb-5">
            <div>
              <p className="text-2xl lg:text-3xl font-bold text-slate-900 dark:text-slate-50">{formatBudget(pipeline.totalValue)}</p>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">總 Pipeline</p>
            </div>
            <div>
              <p className="text-2xl lg:text-3xl font-bold text-green-600 dark:text-green-400">{formatBudget(pipeline.weightedValue)}</p>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">加權預估</p>
            </div>
            <div>
              <p className="text-2xl lg:text-3xl font-bold text-blue-600 dark:text-blue-400">{pipeline.dealCount}</p>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">進行中商機</p>
            </div>
          </div>

          {/* Stage breakdown bar */}
          {pipeline.totalValue > 0 && (
            <div className="mb-3">
              <div className="flex h-2.5 rounded-full overflow-hidden gap-0.5 bg-slate-100 dark:bg-slate-800">
                {["L0", "L1", "L2", "L3", "L4"].map((stage) => {
                  const pct = (pipeline.byStage[stage].value / pipeline.totalValue) * 100;
                  if (pct === 0) return null;
                  return (
                    <div
                      key={stage}
                      className={`${STAGE_COLORS[stage]} rounded-full transition-all`}
                      style={{ width: `${Math.max(pct, 2)}%` }}
                      title={`${STAGE_LABELS[stage]}: ${formatBudget(pipeline.byStage[stage].value)}`}
                    />
                  );
                })}
              </div>
            </div>
          )}

          {/* Stage detail chips */}
          <div className="flex flex-wrap gap-2">
            {["L0", "L1", "L2", "L3", "L4"].map((stage) => {
              const s = pipeline.byStage[stage];
              if (s.count === 0) return null;
              return (
                <div
                  key={stage}
                  className="flex items-center gap-1.5 bg-slate-50 dark:bg-slate-800 rounded-lg px-2.5 py-1.5"
                >
                  <div className={`w-2 h-2 rounded-full ${STAGE_COLORS[stage]}`} />
                  <span className="text-xs text-slate-600 dark:text-slate-300">{STAGE_LABELS[stage]}</span>
                  <span className="text-xs font-semibold text-slate-900 dark:text-slate-50">{s.count}</span>
                  <span className="text-[11px] text-slate-500 dark:text-slate-400">{formatBudget(s.value)}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Action summary — secondary */}
        {totalActions > 0 && (
          <div className="flex items-center gap-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-3 mb-4 text-xs text-slate-500 dark:text-slate-400">
            {pushDeals.length > 0 && (
              <span className="flex items-center gap-1">
                <AlertTriangle size={12} className="text-red-400" />
                {pushDeals.length} 商機需推進
              </span>
            )}
            {reminders.length > 0 && (
              <span className="flex items-center gap-1">
                <Bell size={12} className="text-amber-400" />
                {reminders.length} 提醒
              </span>
            )}
            {staleTbds.length > 0 && (
              <span className="flex items-center gap-1">
                <CircleDot size={12} className="text-amber-500" />
                {staleTbds.length} TBD
              </span>
            )}
          </div>
        )}

        {/* 2-column grid on desktop */}
        <div className="lg:grid lg:grid-cols-2 lg:gap-6 space-y-4 lg:space-y-0">
          {/* Left column — primary action items */}
          <div className="space-y-4">
            {/* Today's meetings */}
            {meetings.length > 0 && (
              <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-3">
                  <Calendar size={16} className="text-blue-500" />
                  <span className="text-sm font-semibold text-slate-900 dark:text-slate-50">
                    今日會議
                  </span>
                </div>
                <div className="space-y-2">
                  {meetings.map((m) => (
                    <Link
                      key={m.id}
                      href={`/calendar/meeting/${m.id}`}
                      className="flex items-center justify-between p-3 rounded-lg bg-slate-50 dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 cursor-pointer group transition-colors"
                    >
                      <div>
                        <p className="text-sm font-medium text-slate-900 dark:text-slate-50 group-hover:text-blue-500 transition-colors">
                          {m.title}
                        </p>
                        <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                          {m.client_name} · {new Date(m.meeting_date).toLocaleTimeString("zh-TW", { hour: "2-digit", minute: "2-digit" })}
                        </p>
                      </div>
                      <ChevronRight size={16} className="text-slate-400" />
                    </Link>
                  ))}
                </div>
              </div>
            )}

            {/* Deals needing push */}
            {pushDeals.length > 0 && (
              <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-3">
                  <TrendingUp size={16} className="text-red-500" />
                  <span className="text-sm font-semibold text-slate-900 dark:text-slate-50">
                    需要推進
                  </span>
                  <span className="text-xs text-slate-400">({pushDeals.length})</span>
                </div>
                <div className="space-y-2">
                  {pushDeals.map((deal) => {
                    const idleDays = deal.idle_days ?? 0;
                    return (
                      <Link
                        key={deal.id}
                        href={`/deals/${deal.id}`}
                        className="flex items-center justify-between p-3 rounded-lg bg-slate-50 dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 cursor-pointer group transition-colors"
                      >
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-slate-900 dark:text-slate-50 truncate group-hover:text-blue-500 transition-colors">
                            {deal.name}
                          </p>
                          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                            {deal.client_name} · {deal.stage}
                          </p>
                        </div>
                        <span className="flex items-center gap-1 text-xs text-red-400 flex-shrink-0 ml-2">
                          <AlertTriangle size={12} />
                          {idleDays}天
                        </span>
                      </Link>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Quick actions */}
            <div className="grid grid-cols-2 gap-3">
              <Link
                href="/capture"
                className="flex items-center justify-center gap-2 bg-blue-500 hover:bg-blue-600 text-white font-semibold px-4 py-3 rounded-xl min-h-[44px] active:scale-[0.98] transition-all cursor-pointer"
              >
                新增情報
              </Link>
              <Link
                href="/deals"
                className="flex items-center justify-center gap-2 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 font-semibold px-4 py-3 rounded-xl min-h-[44px] active:scale-[0.98] transition-all cursor-pointer"
              >
                商機列表
              </Link>
            </div>
          </div>

          {/* Right column — reminders & TBDs */}
          <div className="space-y-4">
            {/* Pending reminders */}
            {reminders.length > 0 && (
              <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-3">
                  <Bell size={16} className="text-amber-500" />
                  <span className="text-sm font-semibold text-slate-900 dark:text-slate-50">
                    待處理提醒
                  </span>
                  <span className="text-xs text-slate-400">({reminders.length})</span>
                </div>
                <div className="space-y-2">
                  {reminders.map((r) => (
                    <div key={r.id} className="flex items-start gap-2 p-3 rounded-lg bg-slate-50 dark:bg-slate-800">
                      <Bell size={12} className="text-amber-400 mt-0.5 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-slate-700 dark:text-slate-300">
                          {r.content}
                        </p>
                        <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                          {r.deal_name && `${r.deal_name} · `}
                          {new Date(r.due_date).toLocaleDateString("zh-TW")}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Expiring subsidies */}
            {expiringSubsidies.length > 0 && (
              <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-3">
                  <Landmark size={16} className="text-red-500" />
                  <span className="text-sm font-semibold text-slate-900 dark:text-slate-50">
                    即將到期補助案
                  </span>
                  <span className="text-xs text-slate-400">({expiringSubsidies.length})</span>
                </div>
                <div className="space-y-2">
                  {expiringSubsidies.map((s) => (
                    <Link
                      key={s.id}
                      href={`/subsidies/${s.id}`}
                      className="flex items-center justify-between p-3 rounded-lg bg-slate-50 dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 cursor-pointer group transition-colors"
                    >
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-slate-900 dark:text-slate-50 truncate group-hover:text-blue-500 transition-colors">
                          {s.name}
                        </p>
                        <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                          {s.agency || "—"}
                        </p>
                      </div>
                      <span className={`text-xs flex-shrink-0 ml-2 font-medium ${(s.days_left ?? 99) <= 30 ? "text-red-400" : "text-amber-400"}`}>
                        {s.days_left != null ? `${s.days_left}天` : s.deadline}
                      </span>
                    </Link>
                  ))}
                </div>
              </div>
            )}

            {/* Stale TBDs */}
            {staleTbds.length > 0 && (
              <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-3">
                  <CircleDot size={16} className="text-amber-500" />
                  <span className="text-sm font-semibold text-slate-900 dark:text-slate-50">
                    待確認事項
                  </span>
                  <span className="text-xs text-slate-400">({staleTbds.length})</span>
                </div>
                <div className="space-y-2">
                  {staleTbds.slice(0, 5).map((t) => (
                    <div key={t.id} className="flex items-start gap-2 p-3 rounded-lg bg-slate-50 dark:bg-slate-800">
                      <CircleDot size={12} className="text-amber-500 mt-0.5 flex-shrink-0" />
                      <span className="text-sm text-slate-700 dark:text-slate-300 line-clamp-1">
                        {t.question}
                      </span>
                    </div>
                  ))}
                  {staleTbds.length > 5 && (
                    <p className="text-xs text-slate-400 pl-5 pt-1">
                      還有 {staleTbds.length - 5} 項...
                    </p>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Empty state */}
        {totalActions === 0 && meetings.length === 0 && (
          <div className="flex flex-col items-center justify-center py-20 text-slate-400 dark:text-slate-500">
            <p className="text-sm">一切就緒</p>
            <p className="text-xs mt-1">目前沒有需要推進的事項</p>
          </div>
        )}
      </div>
    </div>
  );
}
