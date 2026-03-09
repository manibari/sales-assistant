"use client";

import { useState, useEffect } from "react";
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

const WEEKDAYS = ["日", "一", "二", "三", "四", "五", "六"];
const MONTHS = [
  "一月", "二月", "三月", "四月", "五月", "六月",
  "七月", "八月", "九月", "十月", "十一月", "十二月",
];

function getDaysInMonth(year: number, month: number) {
  return new Date(year, month + 1, 0).getDate();
}

function getFirstDayOfMonth(year: number, month: number) {
  return new Date(year, month, 1).getDay();
}

export default function CalendarPage() {
  const today = new Date();
  const [year, setYear] = useState(today.getFullYear());
  const [month, setMonth] = useState(today.getMonth());
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [meetings, setMeetings] = useState<NxMeeting[]>([]);
  const [reminders, setReminders] = useState<NxReminder[]>([]);
  const [dayMeetings, setDayMeetings] = useState<NxMeeting[]>([]);
  const [dayReminders, setDayReminders] = useState<NxReminder[]>([]);

  // Load month data
  useEffect(() => {
    const m = month + 1;
    nxApi.calendar.meetingsByMonth(year, m).then(setMeetings).catch(console.error);
    nxApi.calendar.remindersByMonth(year, m).then(setReminders).catch(console.error);
  }, [year, month]);

  // Load day data when selected
  useEffect(() => {
    if (!selectedDate) {
      setDayMeetings([]);
      setDayReminders([]);
      return;
    }
    nxApi.calendar.meetingsByDate(selectedDate).then(setDayMeetings).catch(console.error);
    nxApi.calendar.remindersByDate(selectedDate).then(setDayReminders).catch(console.error);
  }, [selectedDate]);

  const prevMonth = () => {
    if (month === 0) { setYear(year - 1); setMonth(11); }
    else setMonth(month - 1);
    setSelectedDate(null);
  };

  const nextMonth = () => {
    if (month === 11) { setYear(year + 1); setMonth(0); }
    else setMonth(month + 1);
    setSelectedDate(null);
  };

  // Build calendar grid
  const daysInMonth = getDaysInMonth(year, month);
  const firstDay = getFirstDayOfMonth(year, month);
  const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;

  // Dates with events
  const eventDates = new Set<string>();
  meetings.forEach((m) => {
    const d = m.meeting_date.slice(0, 10);
    eventDates.add(d);
  });
  reminders.forEach((r) => {
    const d = r.due_date.slice(0, 10);
    eventDates.add(d);
  });

  const cells: (number | null)[] = [];
  for (let i = 0; i < firstDay; i++) cells.push(null);
  for (let d = 1; d <= daysInMonth; d++) cells.push(d);

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

      <div className="flex-1 px-4 py-4 overflow-auto max-w-2xl lg:max-w-4xl mx-auto w-full">
        {/* Month header */}
        <div className="flex items-center justify-between mb-4">
          <button onClick={prevMonth} className="p-2 cursor-pointer text-slate-400 hover:text-slate-200 transition-colors">
            <ChevronLeft size={20} />
          </button>
          <h2 className="text-base font-semibold text-slate-900 dark:text-slate-50">
            {year} {MONTHS[month]}
          </h2>
          <button onClick={nextMonth} className="p-2 cursor-pointer text-slate-400 hover:text-slate-200 transition-colors">
            <ChevronRight size={20} />
          </button>
        </div>

        {/* Weekday headers */}
        <div className="grid grid-cols-7 gap-1 mb-1">
          {WEEKDAYS.map((d) => (
            <div key={d} className="text-center text-[11px] font-medium text-slate-400 dark:text-slate-500 py-1">
              {d}
            </div>
          ))}
        </div>

        {/* Calendar grid */}
        <div className="grid grid-cols-7 gap-1 mb-6">
          {cells.map((day, i) => {
            if (day === null) return <div key={`empty-${i}`} />;
            const dateStr = `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
            const isToday = dateStr === todayStr;
            const isSelected = dateStr === selectedDate;
            const hasEvent = eventDates.has(dateStr);

            return (
              <button
                key={dateStr}
                onClick={() => setSelectedDate(isSelected ? null : dateStr)}
                className={`aspect-square flex flex-col items-center justify-center rounded-lg text-sm transition-colors cursor-pointer relative ${
                  isSelected
                    ? "bg-blue-500 text-white"
                    : isToday
                      ? "bg-blue-500/10 text-blue-500 font-semibold"
                      : "text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800"
                }`}
              >
                {day}
                {hasEvent && !isSelected && (
                  <div className="absolute bottom-1 w-1 h-1 rounded-full bg-blue-500" />
                )}
              </button>
            );
          })}
        </div>

        {/* Day detail */}
        {selectedDate && (
          <div className="space-y-3">
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
                        {m.deal_name} · {m.meeting_date.slice(11, 16)}
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
    </div>
  );
}
