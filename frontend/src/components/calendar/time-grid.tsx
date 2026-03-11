"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { useRouter } from "next/navigation";
import type { NxMeeting } from "@/lib/nexus-api";
import Link from "next/link";

const HOUR_HEIGHT = 60; // px per hour
const START_HOUR = 8;
const END_HOUR = 20;
const TOTAL_HOURS = END_HOUR - START_HOUR;
const SNAP_MINUTES = 15;

function formatDate(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

const WEEKDAYS_SHORT = ["日", "一", "二", "三", "四", "五", "六"];

interface TimeGridProps {
  days: Date[];
  meetings: NxMeeting[];
}

interface DragState {
  dayIndex: number;
  startMinute: number;
  endMinute: number;
}

function minuteToY(minute: number): number {
  return ((minute - START_HOUR * 60) / 60) * HOUR_HEIGHT;
}

function yToMinute(y: number): number {
  const raw = (y / HOUR_HEIGHT) * 60 + START_HOUR * 60;
  return Math.round(raw / SNAP_MINUTES) * SNAP_MINUTES;
}

function formatTime(totalMinutes: number): string {
  const h = Math.floor(totalMinutes / 60);
  const m = totalMinutes % 60;
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`;
}

export function TimeGrid({ days, meetings }: TimeGridProps) {
  const router = useRouter();
  const gridRef = useRef<HTMLDivElement>(null);
  const [drag, setDrag] = useState<DragState | null>(null);
  const draggingRef = useRef(false);
  const today = new Date();
  const todayStr = formatDate(today);

  // Current time indicator
  const [nowMinute, setNowMinute] = useState(() => today.getHours() * 60 + today.getMinutes());
  useEffect(() => {
    const interval = setInterval(() => {
      const n = new Date();
      setNowMinute(n.getHours() * 60 + n.getMinutes());
    }, 60000);
    return () => clearInterval(interval);
  }, []);

  // Group meetings by date
  const meetingsByDate = new Map<string, NxMeeting[]>();
  meetings.forEach((m) => {
    const dateKey = m.meeting_date.slice(0, 10);
    if (!meetingsByDate.has(dateKey)) meetingsByDate.set(dateKey, []);
    meetingsByDate.get(dateKey)!.push(m);
  });

  const getPointerMinute = useCallback((e: React.MouseEvent | React.TouchEvent, dayIndex: number) => {
    if (!gridRef.current) return START_HOUR * 60;
    const rect = gridRef.current.getBoundingClientRect();
    const clientY = "touches" in e ? e.touches[0].clientY : e.clientY;
    const y = clientY - rect.top + gridRef.current.scrollTop;
    const minute = yToMinute(y);
    return Math.max(START_HOUR * 60, Math.min(END_HOUR * 60, minute));
  }, []);

  const getDayIndex = useCallback((e: React.MouseEvent | React.TouchEvent) => {
    if (!gridRef.current) return 0;
    const rect = gridRef.current.getBoundingClientRect();
    const clientX = "touches" in e ? e.touches[0].clientX : e.clientX;
    const timeGutterWidth = 48; // matches w-12
    const x = clientX - rect.left - timeGutterWidth;
    const colWidth = (rect.width - timeGutterWidth) / days.length;
    return Math.max(0, Math.min(days.length - 1, Math.floor(x / colWidth)));
  }, [days.length]);

  const handlePointerDown = useCallback((e: React.MouseEvent | React.TouchEvent) => {
    const dayIdx = getDayIndex(e);
    const minute = getPointerMinute(e, dayIdx);
    draggingRef.current = true;
    setDrag({ dayIndex: dayIdx, startMinute: minute, endMinute: minute + 30 });
  }, [getDayIndex, getPointerMinute]);

  const handlePointerMove = useCallback((e: React.MouseEvent | React.TouchEvent) => {
    if (!draggingRef.current || !drag) return;
    const minute = getPointerMinute(e, drag.dayIndex);
    if (minute !== drag.endMinute) {
      setDrag((prev) => prev ? { ...prev, endMinute: Math.max(prev.startMinute + SNAP_MINUTES, minute) } : null);
    }
  }, [drag, getPointerMinute]);

  const handlePointerUp = useCallback(() => {
    if (!draggingRef.current || !drag) return;
    draggingRef.current = false;
    const day = days[drag.dayIndex];
    const dateStr = formatDate(day);
    const startTime = formatTime(drag.startMinute);
    const duration = drag.endMinute - drag.startMinute;
    setDrag(null);
    router.push(`/calendar/meeting/new?date=${dateStr}&time=${startTime}&duration=${Math.max(30, duration)}`);
  }, [drag, days, router]);

  // Touch event handlers
  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    handlePointerDown(e);
  }, [handlePointerDown]);

  const handleTouchMove = useCallback((e: React.TouchEvent) => {
    handlePointerMove(e);
  }, [handlePointerMove]);

  const handleTouchEnd = useCallback(() => {
    handlePointerUp();
  }, [handlePointerUp]);

  const showNowLine = days.some((d) => formatDate(d) === todayStr) && nowMinute >= START_HOUR * 60 && nowMinute <= END_HOUR * 60;
  const nowDayIndex = days.findIndex((d) => formatDate(d) === todayStr);

  return (
    <div className="flex flex-col flex-1 min-h-0">
      {/* Day headers */}
      <div className="flex border-b border-slate-200 dark:border-slate-700 sticky top-0 bg-white dark:bg-slate-950 z-10">
        <div className="w-12 flex-shrink-0" />
        {days.map((d, i) => {
          const isToday = formatDate(d) === todayStr;
          return (
            <div key={i} className="flex-1 text-center py-2 border-l border-slate-200 dark:border-slate-700">
              <div className="text-[11px] text-slate-400 dark:text-slate-500">{WEEKDAYS_SHORT[d.getDay()]}</div>
              <div className={`text-sm font-medium ${isToday ? "bg-blue-500 text-white w-7 h-7 rounded-full flex items-center justify-center mx-auto" : "text-slate-700 dark:text-slate-300"}`}>
                {d.getDate()}
              </div>
            </div>
          );
        })}
      </div>

      {/* Time grid body */}
      <div
        ref={gridRef}
        className="flex-1 overflow-auto relative select-none"
        onMouseDown={handlePointerDown}
        onMouseMove={handlePointerMove}
        onMouseUp={handlePointerUp}
        onMouseLeave={() => { if (draggingRef.current) handlePointerUp(); }}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
      >
        <div className="flex relative" style={{ height: TOTAL_HOURS * HOUR_HEIGHT }}>
          {/* Time gutter */}
          <div className="w-12 flex-shrink-0 relative">
            {Array.from({ length: TOTAL_HOURS }, (_, i) => (
              <div
                key={i}
                className="absolute right-2 text-[11px] text-slate-400 dark:text-slate-500 -translate-y-1/2"
                style={{ top: i * HOUR_HEIGHT }}
              >
                {String(START_HOUR + i).padStart(2, "0")}:00
              </div>
            ))}
          </div>

          {/* Day columns */}
          <div className="flex-1 flex relative">
            {days.map((d, dayIdx) => {
              const dateStr = formatDate(d);
              const dayMeetings = meetingsByDate.get(dateStr) || [];

              return (
                <div key={dayIdx} className="flex-1 relative border-l border-slate-200 dark:border-slate-700">
                  {/* Hour lines */}
                  {Array.from({ length: TOTAL_HOURS }, (_, i) => (
                    <div
                      key={i}
                      className="absolute w-full border-t border-slate-100 dark:border-slate-800"
                      style={{ top: i * HOUR_HEIGHT }}
                    />
                  ))}

                  {/* Meeting blocks */}
                  {dayMeetings.map((m) => {
                    const timePart = m.meeting_date.slice(11, 16);
                    const [hh, mm] = timePart.split(":").map(Number);
                    const meetingMinute = hh * 60 + mm;
                    const duration = m.duration_minutes || 60;
                    const top = minuteToY(meetingMinute);
                    const height = (duration / 60) * HOUR_HEIGHT;

                    if (meetingMinute < START_HOUR * 60 || meetingMinute >= END_HOUR * 60) return null;

                    return (
                      <Link
                        key={m.id}
                        href={`/calendar/meeting/${m.id}`}
                        className="absolute left-0.5 right-0.5 rounded-md px-1.5 py-0.5 overflow-hidden bg-blue-500/15 border border-blue-500/30 hover:bg-blue-500/25 transition-colors cursor-pointer z-[2]"
                        style={{ top, height: Math.max(height, 20) }}
                        onClick={(e) => e.stopPropagation()}
                        onMouseDown={(e) => e.stopPropagation()}
                        onTouchStart={(e) => e.stopPropagation()}
                      >
                        <p className="text-[11px] font-medium text-blue-700 dark:text-blue-300 truncate">{timePart} {m.title}</p>
                        <p className="text-[10px] text-blue-500/70 dark:text-blue-400/70 truncate">{m.deal_name}</p>
                      </Link>
                    );
                  })}
                </div>
              );
            })}

            {/* Now line */}
            {showNowLine && nowDayIndex >= 0 && (
              <div
                className="absolute left-0 right-0 z-[5] pointer-events-none"
                style={{ top: minuteToY(nowMinute) }}
              >
                <div
                  className="absolute h-0.5 bg-red-500"
                  style={{
                    left: `${(nowDayIndex / days.length) * 100}%`,
                    width: `${(1 / days.length) * 100}%`,
                  }}
                />
                <div
                  className="absolute w-2 h-2 rounded-full bg-red-500 -translate-y-[3px]"
                  style={{ left: `${(nowDayIndex / days.length) * 100}%` }}
                />
              </div>
            )}

            {/* Drag preview */}
            {drag && (
              <div
                className="absolute rounded-md bg-blue-500/20 border-2 border-blue-500/50 border-dashed z-[3] pointer-events-none"
                style={{
                  top: minuteToY(drag.startMinute),
                  height: minuteToY(drag.endMinute) - minuteToY(drag.startMinute),
                  left: `${(drag.dayIndex / days.length) * 100}%`,
                  width: `${(1 / days.length) * 100}%`,
                }}
              >
                <span className="text-[11px] text-blue-600 dark:text-blue-400 px-1 font-medium">
                  {formatTime(drag.startMinute)} — {formatTime(drag.endMinute)}
                </span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
