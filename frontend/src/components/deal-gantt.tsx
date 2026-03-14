"use client";

import { useState, useEffect, useRef } from "react";
import { nxApi, type NxMeeting } from "@/lib/nexus-api";
import { Flag, ZoomIn, ZoomOut, Pencil, Check, X } from "lucide-react";

interface DealGanttProps {
  dealId: number;
  dealCreatedAt: string;
  currentStage: string;
  onDealUpdated?: () => void;
}

// --- helpers ---

function daysBetween(a: Date, b: Date): number {
  return Math.round((b.getTime() - a.getTime()) / 86400000);
}
function fmtDate(d: Date): string {
  return `${d.getMonth() + 1}/${d.getDate()}`;
}
function fmtFull(d: Date): string {
  const wd = ["日", "一", "二", "三", "四", "五", "六"];
  return `${d.getFullYear()}/${d.getMonth() + 1}/${d.getDate()}（${wd[d.getDay()]}）`;
}
function fmtIsoDate(d: Date): string {
  const p = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}
function fmtTime(iso: string): string {
  return iso.slice(11, 16);
}
function toDay(d: Date): Date {
  const r = new Date(d);
  r.setHours(0, 0, 0, 0);
  return r;
}

const STATUS_ZH: Record<string, string> = {
  scheduled: "排定", completed: "已完成", cancelled: "已取消",
  draft: "草稿", confirmed: "已確認",
};

// --- Row type ---

interface GanttRow {
  id: string;
  label: string;
  start: Date;
  end: Date;
  color: "blue" | "cyan" | "indigo";
  tooltip: React.ReactNode;
}

// --- Zoom ---

const ZOOM_LEVELS = [14, 30, 60, 90, 180];
const COL_MIN_W = 28; // minimum px per day column

export function DealGantt({ dealId, dealCreatedAt, currentStage, onDealUpdated }: DealGanttProps) {
  const [meetings, setMeetings] = useState<NxMeeting[]>([]);
  const [zoomIdx, setZoomIdx] = useState(2);
  const [editingStart, setEditingStart] = useState(false);
  const [startInput, setStartInput] = useState("");
  const [hoveredRow, setHoveredRow] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    nxApi.calendar.meetingsByDeal(dealId).then(setMeetings).catch(console.error);
  }, [dealId]);

  const dealStart = toDay(new Date(dealCreatedAt));
  const today = toDay(new Date());
  const elapsedDays = daysBetween(dealStart, today);

  // Visible window centered on today
  const visibleDays = ZOOM_LEVELS[zoomIdx];
  const halfDays = Math.floor(visibleDays / 2);
  const winStart = toDay(new Date(today.getTime() - halfDays * 86400000));
  const winEnd = toDay(new Date(today.getTime() + (visibleDays - halfDays) * 86400000));

  // Generate date columns
  const cols: Date[] = [];
  for (let d = new Date(winStart); d <= winEnd; d.setDate(d.getDate() + 1)) {
    cols.push(toDay(new Date(d)));
  }

  // Build rows
  const rows: GanttRow[] = [];

  // Deal lifespan row
  rows.push({
    id: "deal",
    label: "案件期間",
    start: dealStart,
    end: today,
    color: "indigo",
    tooltip: (
      <div>
        <div className="font-semibold mb-1">案件期間</div>
        <div>開案：{fmtFull(dealStart)}</div>
        <div>至今第 {elapsedDays} 天</div>
        <div>階段：{currentStage}</div>
      </div>
    ),
  });

  // Meeting rows
  meetings
    .slice()
    .sort((a, b) => a.meeting_date.localeCompare(b.meeting_date))
    .forEach((m) => {
      const mStart = toDay(new Date(m.meeting_date));
      rows.push({
        id: `m-${m.id}`,
        label: m.title,
        start: mStart,
        end: mStart, // single-day bar
        color: "blue",
        tooltip: (
          <div>
            <div className="font-semibold mb-1">{m.title}</div>
            <div>{fmtFull(mStart)}</div>
            <div>{fmtTime(m.meeting_date)} · {m.duration_minutes} 分鐘</div>
            <div className="mt-1">
              <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${
                m.status === "completed" ? "bg-green-500/20 text-green-300"
                  : m.status === "cancelled" ? "bg-slate-500/20 text-slate-400"
                  : "bg-blue-500/20 text-blue-300"
              }`}>{STATUS_ZH[m.status] || m.status}</span>
            </div>
          </div>
        ),
      });
    });

  // Intel rows removed — intel is shown in the "相關情報" section instead

  // Bar position helpers
  const colIndex = (d: Date): number => daysBetween(winStart, d);

  const barStyle = (row: GanttRow) => {
    const si = colIndex(row.start);
    const ei = colIndex(row.end);
    const startCol = Math.max(si, 0);
    const endCol = Math.min(ei, cols.length - 1);
    if (startCol > cols.length - 1 || endCol < 0) return null;
    return { startCol, span: endCol - startCol + 1 };
  };

  const colorMap = {
    blue: {
      bar: "bg-blue-500/20 border-blue-500/40",
      fill: "bg-blue-500",
    },
    cyan: {
      bar: "bg-cyan-500/20 border-cyan-500/40",
      fill: "bg-cyan-500",
    },
    indigo: {
      bar: "bg-indigo-500/20 border-indigo-500/40",
      fill: "bg-indigo-500",
    },
  };

  const canZoomIn = zoomIdx > 0;
  const canZoomOut = zoomIdx < ZOOM_LEVELS.length - 1;

  const handleSaveStart = async () => {
    if (!startInput) return;
    try {
      await nxApi.deals.update(dealId, { created_at: startInput } as Parameters<typeof nxApi.deals.update>[1]);
      setEditingStart(false);
      onDealUpdated?.();
    } catch (err) {
      console.error("Failed to update start date:", err);
    }
  };

  // Scroll to today on mount
  useEffect(() => {
    if (scrollRef.current) {
      const todayIdx = colIndex(today);
      const containerW = scrollRef.current.clientWidth;
      const scrollTarget = todayIdx * COL_MIN_W - containerW / 2;
      scrollRef.current.scrollLeft = Math.max(0, scrollTarget);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [zoomIdx]);

  const LABEL_W = 120;
  const gridW = cols.length * COL_MIN_W;
  const todayIdx = colIndex(today);

  // Group header dates: show month labels
  const monthHeaders: { label: string; startIdx: number; span: number }[] = [];
  let curMonth = -1;
  let curStart = 0;
  cols.forEach((d, i) => {
    const m = d.getMonth();
    if (m !== curMonth) {
      if (curMonth >= 0) {
        monthHeaders.push({ label: `${cols[curStart].getMonth() + 1}月`, startIdx: curStart, span: i - curStart });
      }
      curMonth = m;
      curStart = i;
    }
  });
  monthHeaders.push({ label: `${cols[curStart].getMonth() + 1}月`, startIdx: curStart, span: cols.length - curStart });

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Flag size={16} className="text-indigo-500" />
          <span className="text-sm font-semibold text-slate-900 dark:text-slate-50">攻案節奏</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="text-[10px] text-slate-400 mr-1">{visibleDays}天</span>
          <button
            onClick={() => canZoomIn && setZoomIdx(zoomIdx - 1)}
            disabled={!canZoomIn}
            className="p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-30 cursor-pointer disabled:cursor-default transition-colors"
          ><ZoomIn size={14} className="text-slate-500" /></button>
          <button
            onClick={() => canZoomOut && setZoomIdx(zoomIdx + 1)}
            disabled={!canZoomOut}
            className="p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-30 cursor-pointer disabled:cursor-default transition-colors"
          ><ZoomOut size={14} className="text-slate-500" /></button>
        </div>
      </div>

      {/* Editable start date */}
      <div className="flex flex-wrap gap-x-4 gap-y-1 mb-3 text-xs text-slate-500 dark:text-slate-400">
        {editingStart ? (
          <span className="flex items-center gap-1">
            開案
            <input type="date" value={startInput} onChange={(e) => setStartInput(e.target.value)}
              className="bg-slate-100 dark:bg-slate-800 border border-blue-500 rounded px-1.5 py-0.5 text-xs text-slate-900 dark:text-slate-50 focus:outline-none" autoFocus />
            <button onClick={handleSaveStart} className="p-0.5 text-blue-500 cursor-pointer"><Check size={12} /></button>
            <button onClick={() => setEditingStart(false)} className="p-0.5 text-slate-400 cursor-pointer"><X size={12} /></button>
          </span>
        ) : (
          <span className="flex items-center gap-1 cursor-pointer hover:text-blue-500 transition-colors"
            onClick={() => { setStartInput(fmtIsoDate(dealStart)); setEditingStart(true); }}
            title="點擊修改開案日期">
            開案 {fmtFull(dealStart)} <Pencil size={10} />
          </span>
        )}
        <span>第 {elapsedDays} 天</span>
      </div>

      {/* Gantt chart */}
      <div className="flex border border-slate-200 dark:border-slate-700 rounded-lg overflow-hidden">
        {/* Left: row labels */}
        <div className="flex-shrink-0 border-r border-slate-200 dark:border-slate-700" style={{ width: LABEL_W }}>
          {/* Header spacer (month + day rows) */}
          <div className="h-10 border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/80" />
          {/* Row labels */}
          {rows.map((row) => (
            <div
              key={row.id}
              className={`h-8 flex items-center px-2 text-[11px] truncate border-b border-slate-100 dark:border-slate-800 transition-colors ${
                hoveredRow === row.id ? "bg-slate-100 dark:bg-slate-800" : ""
              } ${row.id === "deal" ? "font-semibold text-indigo-600 dark:text-indigo-400" : "text-slate-600 dark:text-slate-400"}`}
              onMouseEnter={() => setHoveredRow(row.id)}
              onMouseLeave={() => setHoveredRow(null)}
            >
              {row.id === "deal" ? "📋" : row.color === "blue" ? "📅" : "⚡"}{" "}
              {row.label}
            </div>
          ))}
        </div>

        {/* Right: scrollable grid */}
        <div ref={scrollRef} className="flex-1 overflow-x-auto">
          <div style={{ width: gridW }}>
            {/* Date headers */}
            <div className="sticky top-0 z-10 bg-slate-50 dark:bg-slate-800/80 border-b border-slate-200 dark:border-slate-700">
              {/* Month row */}
              <div className="flex h-5">
                {monthHeaders.map((mh, mi) => (
                  <div
                    key={mi}
                    className="text-[10px] font-medium text-slate-500 dark:text-slate-400 border-r border-slate-200 dark:border-slate-700 flex items-center justify-center"
                    style={{ width: mh.span * COL_MIN_W }}
                  >
                    {mh.label}
                  </div>
                ))}
              </div>
              {/* Day row */}
              <div className="flex h-5">
                {cols.map((d, i) => {
                  const isToday = i === todayIdx;
                  const isWeekend = d.getDay() === 0 || d.getDay() === 6;
                  return (
                    <div
                      key={i}
                      className={`text-center text-[9px] border-r border-slate-100 dark:border-slate-800 flex items-center justify-center
                        ${isToday ? "bg-red-500 text-white font-bold rounded-sm" : isWeekend ? "text-slate-300 dark:text-slate-600" : "text-slate-400 dark:text-slate-500"}`}
                      style={{ width: COL_MIN_W }}
                    >
                      {d.getDate()}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Grid body */}
            {rows.map((row) => {
              const bar = barStyle(row);
              return (
                <div
                  key={row.id}
                  className={`relative h-8 flex border-b border-slate-100 dark:border-slate-800 transition-colors ${
                    hoveredRow === row.id ? "bg-slate-50 dark:bg-slate-800/50" : ""
                  }`}
                  onMouseEnter={() => setHoveredRow(row.id)}
                  onMouseLeave={() => setHoveredRow(null)}
                >
                  {/* Weekend shading + grid lines */}
                  {cols.map((d, i) => {
                    const isWeekend = d.getDay() === 0 || d.getDay() === 6;
                    const isToday = i === todayIdx;
                    return (
                      <div
                        key={i}
                        className={`absolute top-0 bottom-0 border-r border-slate-100 dark:border-slate-800
                          ${isWeekend ? "bg-slate-50/50 dark:bg-slate-800/30" : ""}
                          ${isToday ? "border-r-red-400 dark:border-r-red-500" : ""}`}
                        style={{ left: i * COL_MIN_W, width: COL_MIN_W }}
                      />
                    );
                  })}

                  {/* Today vertical line */}
                  <div
                    className="absolute top-0 bottom-0 w-0.5 bg-red-500/40 z-[1]"
                    style={{ left: todayIdx * COL_MIN_W + COL_MIN_W / 2 }}
                  />

                  {/* Bar */}
                  {bar && (
                    <div
                      className={`absolute top-1.5 h-5 rounded group z-[2] border ${colorMap[row.color].bar} cursor-default`}
                      style={{
                        left: bar.startCol * COL_MIN_W + 2,
                        width: Math.max(bar.span * COL_MIN_W - 4, COL_MIN_W - 4),
                      }}
                    >
                      {/* Inner fill */}
                      <div className={`absolute inset-0 rounded ${colorMap[row.color].fill} opacity-30`} />
                      {/* Bar label */}
                      {bar.span * COL_MIN_W > 50 && (
                        <span className="relative z-[1] text-[10px] font-medium px-1.5 truncate block leading-5 text-slate-700 dark:text-slate-200">
                          {row.label}
                        </span>
                      )}

                      {/* Hover tooltip */}
                      <div className="absolute bottom-full left-0 mb-1.5 hidden group-hover:block z-30 pointer-events-none">
                        <div className="bg-slate-800 dark:bg-slate-700 text-white text-[11px] px-3 py-2 rounded-lg shadow-xl whitespace-nowrap">
                          {row.tooltip}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
