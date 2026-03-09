"use client";

import { useState, useEffect, useCallback } from "react";
import { TopBar } from "@/components/top-bar";
import {
  AlertTriangle,
  Bell,
  Calendar,
  ChevronRight,
  CircleDot,
  Loader2,
  Search,
  TrendingUp,
} from "lucide-react";
import { nxApi, type NxDeal, type NxReminder, type NxMeeting, type NxTbdItem } from "@/lib/nexus-api";
import Link from "next/link";

export default function DashboardPage() {
  const [pushDeals, setPushDeals] = useState<NxDeal[]>([]);
  const [reminders, setReminders] = useState<NxReminder[]>([]);
  const [meetings, setMeetings] = useState<NxMeeting[]>([]);
  const [staleTbds, setStaleTbds] = useState<NxTbdItem[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = useCallback(async () => {
    try {
      const today = new Date().toISOString().split("T")[0];
      const [deals, rems, mtgs, tbds] = await Promise.all([
        nxApi.deals.needsPush(7),
        nxApi.calendar.pendingReminders(),
        nxApi.calendar.meetingsByDate(today),
        nxApi.tbd.list(),
      ]);
      setPushDeals(deals);
      setReminders(rems);
      setMeetings(mtgs);
      setStaleTbds(tbds.filter((t) => !t.resolved));
    } catch (err) {
      console.error("Dashboard load failed:", err);
    } finally {
      setLoading(false);
    }
  }, []);

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
          className="p-2 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 cursor-pointer transition-colors"
        >
          <Search size={20} />
        </Link>
      </TopBar>

      <div className="flex-1 px-4 lg:px-6 py-4 overflow-auto max-w-2xl lg:max-w-6xl mx-auto w-full">
        {/* Summary header — always full width */}
        <div className="bg-gradient-to-br from-blue-500/10 to-blue-600/5 border border-blue-500/20 rounded-xl p-4 lg:p-5 mb-4">
          <p className="text-xs text-blue-400 font-medium">本週該推進的</p>
          <p className="text-2xl font-bold text-slate-900 dark:text-slate-50 mt-1">
            {totalActions}
            <span className="text-sm font-normal text-slate-400 ml-2">項待辦</span>
          </p>
          <div className="flex gap-4 mt-2 text-xs text-slate-500 dark:text-slate-400">
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
        </div>

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
                      className="flex items-center justify-between py-2 cursor-pointer group"
                    >
                      <div>
                        <p className="text-sm font-medium text-slate-900 dark:text-slate-50 group-hover:text-blue-500 transition-colors">
                          {m.title}
                        </p>
                        <p className="text-xs text-slate-400">
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
                        className="flex items-center justify-between py-2 cursor-pointer group"
                      >
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-slate-900 dark:text-slate-50 truncate group-hover:text-blue-500 transition-colors">
                            {deal.name}
                          </p>
                          <p className="text-xs text-slate-400">
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
                    <div key={r.id} className="flex items-start gap-2 py-2">
                      <Bell size={12} className="text-amber-400 mt-0.5 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-slate-700 dark:text-slate-300">
                          {r.content}
                        </p>
                        <p className="text-xs text-slate-400 mt-0.5">
                          {r.deal_name && `${r.deal_name} · `}
                          {new Date(r.due_date).toLocaleDateString("zh-TW")}
                        </p>
                      </div>
                    </div>
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
                    <div key={t.id} className="flex items-start gap-2 py-1">
                      <CircleDot size={12} className="text-amber-500 mt-0.5 flex-shrink-0" />
                      <span className="text-sm text-slate-700 dark:text-slate-300 line-clamp-1">
                        {t.question}
                      </span>
                    </div>
                  ))}
                  {staleTbds.length > 5 && (
                    <p className="text-xs text-slate-400 pl-5">
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
