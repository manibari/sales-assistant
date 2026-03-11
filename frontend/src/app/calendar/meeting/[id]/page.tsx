"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { TopBar } from "@/components/top-bar";
import {
  ChevronLeft,
  CircleDot,
  Check,
  FileCheck,
  Lightbulb,
  Zap,
  Loader2,
} from "lucide-react";
import {
  nxApi,
  type NxMeeting,
  type NxDeal,
  type NxTbdItem,
  type MeddicProgress,
} from "@/lib/nexus-api";
import Link from "next/link";

const WEEKDAYS = ["日", "一", "二", "三", "四", "五", "六"];

const STATUS_STYLES: Record<string, { label: string; cls: string }> = {
  scheduled: { label: "已排定", cls: "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300" },
  completed: { label: "已完成", cls: "bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300" },
  cancelled: { label: "已取消", cls: "bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400" },
};

function formatMeetingTime(isoDate: string, durationMin: number) {
  const d = new Date(isoDate);
  const pad = (n: number) => String(n).padStart(2, "0");
  const dateStr = `${d.getFullYear()}/${pad(d.getMonth() + 1)}/${pad(d.getDate())}（${WEEKDAYS[d.getDay()]}）`;
  const startH = pad(d.getHours());
  const startM = pad(d.getMinutes());
  const end = new Date(d.getTime() + durationMin * 60000);
  const endH = pad(end.getHours());
  const endM = pad(end.getMinutes());
  return { dateStr, timeRange: `${startH}:${startM} — ${endH}:${endM}`, duration: `${durationMin} 分鐘` };
}

export default function MeetingPrepPage() {
  const params = useParams();
  const router = useRouter();
  const meetingId = Number(params.id);

  const [meeting, setMeeting] = useState<NxMeeting | null>(null);
  const [deal, setDeal] = useState<NxDeal | null>(null);
  const [tbds, setTbds] = useState<NxTbdItem[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = useCallback(async () => {
    try {
      const m = await nxApi.calendar.getMeeting(meetingId);
      setMeeting(m);
      const fullDeal = await nxApi.deals.get(m.deal_id);
      setDeal(fullDeal);
      setTbds(fullDeal.tbds || []);
    } catch (err) {
      console.error("Failed to load meeting:", err);
    } finally {
      setLoading(false);
    }
  }, [meetingId]);

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

  const meddic: MeddicProgress = deal?.meddic_progress || {
    completed: 0,
    total: 6,
    missing: [],
  };

  return (
    <div className="flex flex-col h-full">
      <TopBar title="會前準備包">
        <Link
          href="/calendar"
          className="p-2 rounded-lg text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer transition-colors"
        >
          <ChevronLeft size={20} />
        </Link>
      </TopBar>

      <div className="flex-1 px-4 py-4 overflow-auto max-w-2xl lg:max-w-4xl mx-auto w-full space-y-4">
        {/* Meeting info */}
        {meeting && (() => {
          const { dateStr, timeRange, duration } = formatMeetingTime(meeting.meeting_date, meeting.duration_minutes || 60);
          const status = STATUS_STYLES[meeting.status] || STATUS_STYLES.scheduled;
          return (
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4">
              <div className="flex items-start justify-between mb-2">
                <h2 className="text-base font-semibold text-slate-900 dark:text-slate-50">{meeting.title}</h2>
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${status.cls}`}>{status.label}</span>
              </div>
              <div className="space-y-1 text-sm text-slate-600 dark:text-slate-400">
                <p>{dateStr}</p>
                <p>{timeRange}（{duration}）</p>
              </div>
            </div>
          );
        })()}

        {/* Deal header */}
        {deal && (
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4">
            <p className="text-xs text-slate-400 mb-1">關聯商機</p>
            <h2 className="text-base font-semibold text-slate-900 dark:text-slate-50">
              {deal.name}
            </h2>
            <p className="text-xs text-slate-500 mt-1">
              {deal.client_name} · {deal.stage}
            </p>
          </div>
        )}

        {/* TBD list */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-3">
            <CircleDot size={16} className="text-amber-500" />
            <span className="text-sm font-semibold text-slate-900 dark:text-slate-50">
              TBD 清單
            </span>
            <span className="text-xs text-slate-400">({tbds.length})</span>
          </div>
          {tbds.length > 0 ? (
            <div className="space-y-2">
              {tbds.map((t) => (
                <div key={t.id} className="flex items-center gap-2 py-1">
                  <CircleDot size={12} className="text-amber-500 flex-shrink-0" />
                  <span className="text-sm text-slate-700 dark:text-slate-300">
                    {t.question}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-slate-400">無待確認事項</p>
          )}
        </div>

        {/* MEDDIC progress */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-3">
            <Check size={16} className="text-green-500" />
            <span className="text-sm font-semibold text-slate-900 dark:text-slate-50">
              MEDDIC 進度
            </span>
            <span className="text-xs text-slate-400">
              {meddic.completed}/{meddic.total}
            </span>
          </div>
          <div className="h-2 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden mb-2">
            <div
              className="h-full bg-green-500 rounded-full transition-all"
              style={{ width: `${(meddic.completed / meddic.total) * 100}%` }}
            />
          </div>
          {meddic.missing.length > 0 && (
            <p className="text-xs text-amber-400">
              缺少：{meddic.missing.join(", ")}
            </p>
          )}
        </div>

        {/* NDA/MOU status */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-3">
            <FileCheck size={16} className="text-blue-500" />
            <span className="text-sm font-semibold text-slate-900 dark:text-slate-50">
              文件狀態
            </span>
          </div>
          <p className="text-xs text-slate-400">
            查看商機詳情頁確認 NDA/MOU 狀態
          </p>
        </div>

        {/* AI suggested questions */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-3">
            <Lightbulb size={16} className="text-amber-500" />
            <span className="text-sm font-semibold text-slate-900 dark:text-slate-50">
              建議提問
            </span>
          </div>
          <div className="space-y-2">
            {tbds.length > 0 ? (
              tbds.map((t) => (
                <div key={`q-${t.id}`} className="flex items-start gap-2 py-1">
                  <span className="text-xs text-blue-500 mt-0.5">Q</span>
                  <span className="text-sm text-slate-700 dark:text-slate-300">
                    {t.question}？
                  </span>
                </div>
              ))
            ) : meddic.missing.length > 0 ? (
              meddic.missing.map((m) => (
                <div key={m} className="flex items-start gap-2 py-1">
                  <span className="text-xs text-blue-500 mt-0.5">Q</span>
                  <span className="text-sm text-slate-700 dark:text-slate-300">
                    了解 {m} 的具體情況
                  </span>
                </div>
              ))
            ) : (
              <p className="text-xs text-slate-400">準備充分，沒有建議提問</p>
            )}
          </div>
        </div>

        {/* Related intel */}
        {deal?.intel && deal.intel.length > 0 && (
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-3">
              <Zap size={16} className="text-cyan-500" />
              <span className="text-sm font-semibold text-slate-900 dark:text-slate-50">
                歷史情報
              </span>
            </div>
            <div className="space-y-2">
              {deal.intel.slice(0, 3).map((i: { id: number; raw_input: string }) => (
                <p key={i.id} className="text-sm text-slate-600 dark:text-slate-400 line-clamp-2">
                  {i.raw_input}
                </p>
              ))}
            </div>
          </div>
        )}

        {/* Post-meeting action */}
        <Link
          href="/capture"
          className="block w-full bg-blue-500 hover:bg-blue-600 text-white font-semibold px-6 py-3 rounded-lg min-h-[44px] text-center active:scale-[0.98] transition-all cursor-pointer"
        >
          記錄會議結果
        </Link>
      </div>
    </div>
  );
}
