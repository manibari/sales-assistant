"use client";

import { useState, useEffect, useMemo, useCallback } from "react";
import { TopBar } from "@/components/top-bar";
import {
  ChevronLeft,
  ChevronRight,
  Plus,
  Clock,
  AlertTriangle,
  FileCheck,
} from "lucide-react";
import { nxApi, type NxMeeting, type NxReminder } from "@/lib/nexus-api";
import Link from "next/link";
import { MonthGrid } from "@/components/calendar/month-grid";
import { TimeGrid } from "@/components/calendar/time-grid";

type ViewType = "month" | "week" | "3day";

const MONTHS = [
  "一月", "二月", "三月", "四月", "五月", "六月",
  "七月", "八月", "九月", "十月", "十一月", "十二月",
];

const VIEW_LABELS: Record<ViewType, string> = {
  month: "月",
  week: "週",
  "3day": "3天",
};

function formatDate(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

function addDays(d: Date, n: number): Date {
  const r = new Date(d);
  r.setDate(r.getDate() + n);
  return r;
}

function getWeekStart(d: Date): Date {
  const r = new Date(d);
  r.setDate(r.getDate() - r.getDay()); // Sunday start
  return r;
}

function getDefaultView(): ViewType {
  if (typeof window === "undefined") return "month";
  return window.innerWidth >= 768 ? "week" : "month";
}

export default function CalendarPage() {
  const today = new Date();
  const [view, setView] = useState<ViewType>(getDefaultView);
  const [viewAnchor, setViewAnchor] = useState(today);
  const [year, setYear] = useState(today.getFullYear());
  const [month, setMonth] = useState(today.getMonth());
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [meetings, setMeetings] = useState<NxMeeting[]>([]);
  const [reminders, setReminders] = useState<NxReminder[]>([]);
  const [dayMeetings, setDayMeetings] = useState<NxMeeting[]>([]);
  const [dayReminders, setDayReminders] = useState<NxReminder[]>([]);

  // Compute days for week/3day views
  const viewDays = useMemo(() => {
    if (view === "week") {
      const start = getWeekStart(viewAnchor);
      return Array.from({ length: 7 }, (_, i) => addDays(start, i));
    }
    if (view === "3day") {
      return Array.from({ length: 3 }, (_, i) => addDays(viewAnchor, i));
    }
    return [];
  }, [view, viewAnchor]);

  // Date range for week/3day
  const dateRange = useMemo(() => {
    if (viewDays.length === 0) return { start: "", end: "" };
    return {
      start: formatDate(viewDays[0]),
      end: formatDate(viewDays[viewDays.length - 1]),
    };
  }, [viewDays]);

  // Load month data (for month view)
  useEffect(() => {
    if (view !== "month") return;
    const m = month + 1;
    nxApi.calendar.meetingsByMonth(year, m).then(setMeetings).catch(console.error);
    nxApi.calendar.remindersByMonth(year, m).then(setReminders).catch(console.error);
  }, [year, month, view]);

  // Load range data (for week/3day views)
  useEffect(() => {
    if (view === "month" || !dateRange.start) return;
    nxApi.calendar.meetingsByRange(dateRange.start, dateRange.end).then(setMeetings).catch(console.error);
  }, [view, dateRange.start, dateRange.end]);

  // Load day data when selected (month view)
  useEffect(() => {
    if (!selectedDate) {
      setDayMeetings([]);
      setDayReminders([]);
      return;
    }
    nxApi.calendar.meetingsByDate(selectedDate).then(setDayMeetings).catch(console.error);
    nxApi.calendar.remindersByDate(selectedDate).then(setDayReminders).catch(console.error);
  }, [selectedDate]);

  // Navigation
  const navPrev = useCallback(() => {
    if (view === "month") {
      if (month === 0) { setYear(year - 1); setMonth(11); }
      else setMonth(month - 1);
      setSelectedDate(null);
    } else if (view === "week") {
      setViewAnchor(addDays(viewAnchor, -7));
    } else {
      setViewAnchor(addDays(viewAnchor, -3));
    }
  }, [view, month, year, viewAnchor]);

  const navNext = useCallback(() => {
    if (view === "month") {
      if (month === 11) { setYear(year + 1); setMonth(0); }
      else setMonth(month + 1);
      setSelectedDate(null);
    } else if (view === "week") {
      setViewAnchor(addDays(viewAnchor, 7));
    } else {
      setViewAnchor(addDays(viewAnchor, 3));
    }
  }, [view, month, year, viewAnchor]);

  const goToday = useCallback(() => {
    const t = new Date();
    setViewAnchor(t);
    setYear(t.getFullYear());
    setMonth(t.getMonth());
  }, []);

  // Header label
  const headerLabel = useMemo(() => {
    if (view === "month") return `${year} ${MONTHS[month]}`;
    if (viewDays.length === 0) return "";
    const first = viewDays[0];
    const last = viewDays[viewDays.length - 1];
    const fmtShort = (d: Date) => `${d.getMonth() + 1}/${d.getDate()}`;
    return `${fmtShort(first)} — ${fmtShort(last)}`;
  }, [view, year, month, viewDays]);

  return (
    <div className="flex flex-col h-full">
      <TopBar title="行事曆">
        <Link
          href="/calendar/meeting/new"
          className="p-2 rounded-lg text-blue-500 hover:bg-blue-500/10 cursor-pointer transition-colors"
        >
          <Plus size={20} />
        </Link>
      </TopBar>

      <div className="flex-1 flex flex-col overflow-hidden max-w-2xl lg:max-w-4xl mx-auto w-full">
        {/* View switcher + navigation */}
        <div className="px-4 pt-4 pb-2 space-y-3">
          {/* View pills */}
          <div className="flex items-center justify-center gap-1 bg-slate-100 dark:bg-slate-800 rounded-lg p-1">
            {(["month", "week", "3day"] as ViewType[]).map((v) => (
              <button
                key={v}
                onClick={() => setView(v)}
                className={`flex-1 px-3 py-1.5 rounded-md text-xs font-medium transition-colors cursor-pointer ${
                  view === v
                    ? "bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-50 shadow-sm"
                    : "text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300"
                }`}
              >
                {VIEW_LABELS[v]}
              </button>
            ))}
          </div>

          {/* Nav header */}
          <div className="flex items-center justify-between">
            <button onClick={navPrev} className="p-2 cursor-pointer text-slate-400 hover:text-slate-200 transition-colors">
              <ChevronLeft size={20} />
            </button>
            <button
              onClick={goToday}
              className="text-base font-semibold text-slate-900 dark:text-slate-50 cursor-pointer hover:text-blue-500 transition-colors"
            >
              {headerLabel}
            </button>
            <button onClick={navNext} className="p-2 cursor-pointer text-slate-400 hover:text-slate-200 transition-colors">
              <ChevronRight size={20} />
            </button>
          </div>
        </div>

        {/* Views */}
        {view === "month" ? (
          <div className="flex-1 px-4 pb-4 overflow-auto">
            <MonthGrid
              year={year}
              month={month}
              meetings={meetings}
              reminders={reminders}
              selectedDate={selectedDate}
              onSelectDate={setSelectedDate}
            />

            {/* Day detail */}
            {selectedDate && (
              <div className="space-y-3 mt-6">
                <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-50">
                  {selectedDate}
                </h3>

                {dayMeetings.length === 0 && dayReminders.length === 0 ? (
                  <p className="text-xs text-slate-400 py-4 text-center">無事項</p>
                ) : (
                  <>
                    {dayMeetings.map((m) => (
                      <Link
                        key={m.id}
                        href={`/calendar/meeting/${m.id}`}
                        className="flex items-center gap-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4 cursor-pointer hover:border-slate-300 dark:hover:border-slate-600 transition-colors"
                      >
                        <div className="w-1 h-10 rounded-full bg-blue-500 flex-shrink-0" />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-slate-900 dark:text-slate-50 truncate">
                            {m.title}
                          </p>
                          <p className="text-xs text-slate-400 mt-0.5">
                            {m.deal_name} · {m.meeting_date.slice(11, 16)} · {m.duration_minutes || 60}分鐘
                          </p>
                        </div>
                      </Link>
                    ))}

                    {dayReminders.map((r) => (
                      <div
                        key={r.id}
                        className="flex items-center gap-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4"
                      >
                        <div
                          className={`w-1 h-10 rounded-full flex-shrink-0 ${
                            r.reminder_type === "push" ? "bg-amber-500" : r.reminder_type === "document" ? "bg-red-500" : "bg-slate-500"
                          }`}
                        />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-1.5">
                            {r.reminder_type === "push" ? (
                              <Clock size={14} className="text-amber-500" />
                            ) : r.reminder_type === "document" ? (
                              <FileCheck size={14} className="text-red-500" />
                            ) : (
                              <AlertTriangle size={14} className="text-slate-400" />
                            )}
                            <p className="text-sm text-slate-900 dark:text-slate-50 truncate">
                              {r.content}
                            </p>
                          </div>
                          {r.deal_name && (
                            <p className="text-xs text-slate-400 mt-0.5">{r.deal_name}</p>
                          )}
                        </div>
                      </div>
                    ))}
                  </>
                )}
              </div>
            )}
          </div>
        ) : (
          <div className="flex-1 min-h-0 px-4 pb-4">
            <TimeGrid days={viewDays} meetings={meetings} />
          </div>
        )}
      </div>
    </div>
  );
}
