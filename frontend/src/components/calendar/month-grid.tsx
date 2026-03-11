"use client";

import type { NxMeeting, NxReminder } from "@/lib/nexus-api";

const WEEKDAYS = ["日", "一", "二", "三", "四", "五", "六"];

function getDaysInMonth(year: number, month: number) {
  return new Date(year, month + 1, 0).getDate();
}

function getFirstDayOfMonth(year: number, month: number) {
  return new Date(year, month, 1).getDay();
}

interface MonthGridProps {
  year: number;
  month: number; // 0-indexed
  meetings: NxMeeting[];
  reminders: NxReminder[];
  selectedDate: string | null;
  onSelectDate: (date: string | null) => void;
}

export function MonthGrid({ year, month, meetings, reminders, selectedDate, onSelectDate }: MonthGridProps) {
  const today = new Date();
  const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;
  const daysInMonth = getDaysInMonth(year, month);
  const firstDay = getFirstDayOfMonth(year, month);

  const eventDates = new Set<string>();
  meetings.forEach((m) => eventDates.add(m.meeting_date.slice(0, 10)));
  reminders.forEach((r) => eventDates.add(r.due_date.slice(0, 10)));

  const cells: (number | null)[] = [];
  for (let i = 0; i < firstDay; i++) cells.push(null);
  for (let d = 1; d <= daysInMonth; d++) cells.push(d);

  return (
    <div>
      {/* Weekday headers */}
      <div className="grid grid-cols-7 gap-1 mb-1">
        {WEEKDAYS.map((d) => (
          <div key={d} className="text-center text-[11px] font-medium text-slate-400 dark:text-slate-500 py-1">
            {d}
          </div>
        ))}
      </div>

      {/* Calendar grid */}
      <div className="grid grid-cols-7 gap-1">
        {cells.map((day, i) => {
          if (day === null) return <div key={`empty-${i}`} />;
          const dateStr = `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
          const isToday = dateStr === todayStr;
          const isSelected = dateStr === selectedDate;
          const hasEvent = eventDates.has(dateStr);

          return (
            <button
              key={dateStr}
              onClick={() => onSelectDate(isSelected ? null : dateStr)}
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
    </div>
  );
}
