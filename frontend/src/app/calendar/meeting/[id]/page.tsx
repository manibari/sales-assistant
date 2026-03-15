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
  Plus,
  Link2,
  X,
} from "lucide-react";
import {
  nxApi,
  type NxMeeting,
  type NxDeal,
  type NxTbdItem,
  type NxIntel,
  type MeddicProgress,
} from "@/lib/nexus-api";
import { getIntelDisplayTitle } from "@/lib/intel-display";
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
  const [linkedIntel, setLinkedIntel] = useState<NxIntel[]>([]);
  const [showLinkIntel, setShowLinkIntel] = useState(false);
  const [dealIntel, setDealIntel] = useState<NxIntel[]>([]);
  const [creating, setCreating] = useState(false);

  const loadData = useCallback(async () => {
    try {
      const m = await nxApi.calendar.getMeeting(meetingId);
      setMeeting(m);
      const fullDeal = await nxApi.deals.get(m.deal_id);
      setDeal(fullDeal);
      setTbds(fullDeal.tbds || []);
      // Load intel linked to this meeting
      const meetingIntel = await nxApi.intel.byEntity("meeting", meetingId);
      setLinkedIntel(meetingIntel);
    } catch (err) {
      console.error("Failed to load meeting:", err);
    } finally {
      setLoading(false);
    }
  }, [meetingId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleNewMeetingNote = async () => {
    if (creating || !meeting) return;
    setCreating(true);
    try {
      const title = `${meeting.title} — 會議紀錄`;
      const newIntel = await nxApi.intel.create({
        raw_input: "",
        input_type: "text",
        title,
      });
      // Link to this meeting
      await nxApi.intel.linkMeeting(newIntel.id, meetingId);
      // Also link to the deal
      if (deal) {
        await nxApi.deals.linkIntel(deal.id, newIntel.id);
      }
      router.push(`/intel/${newIntel.id}`);
    } catch (err) {
      console.error("Failed to create meeting note:", err);
    } finally {
      setCreating(false);
    }
  };

  const handleOpenLinkIntel = async () => {
    setShowLinkIntel(true);
    if (!deal) return;
    try {
      const intels = await nxApi.intel.list();
      const linkedIds = new Set(linkedIntel.map((i) => i.id));
      setDealIntel(intels.filter((i) => !linkedIds.has(i.id)));
    } catch (err) {
      console.error("Failed to load intel:", err);
    }
  };

  const handleLinkExistingIntel = async (intelId: number) => {
    try {
      await nxApi.intel.linkMeeting(intelId, meetingId);
      if (deal) {
        await nxApi.deals.linkIntel(deal.id, intelId);
      }
      setShowLinkIntel(false);
      loadData();
    } catch (err) {
      console.error("Failed to link intel:", err);
    }
  };

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
                  {getIntelDisplayTitle(i, 80)}
                </p>
              ))}
            </div>
          </div>
        )}

        {/* Meeting-linked intel */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-3">
            <Zap size={16} className="text-cyan-500" />
            <span className="text-sm font-semibold text-slate-900 dark:text-slate-50">
              會議情報
            </span>
            <span className="text-xs text-slate-400">({linkedIntel.length})</span>
          </div>
          {linkedIntel.length > 0 ? (
            <div className="divide-y divide-slate-100 dark:divide-slate-800">
              {linkedIntel.map((i) => (
                <Link
                  key={i.id}
                  href={`/intel/${i.id}`}
                  className="flex items-center justify-between py-2 hover:bg-slate-50 dark:hover:bg-slate-800/50 -mx-1 px-1 rounded transition-colors"
                >
                  <span className="text-sm text-slate-700 dark:text-slate-300 line-clamp-1">
                    {getIntelDisplayTitle(i, 60)}
                  </span>
                  <span className="text-[11px] text-slate-400 flex-shrink-0 ml-2">
                    {new Date(i.created_at).toLocaleDateString("zh-TW")}
                  </span>
                </Link>
              ))}
            </div>
          ) : (
            <p className="text-xs text-slate-400">尚無會議紀錄</p>
          )}
        </div>

        {/* Post-meeting actions */}
        <div className="flex gap-3">
          <button
            onClick={handleNewMeetingNote}
            disabled={creating}
            className="flex-1 flex items-center justify-center gap-2 bg-blue-500 hover:bg-blue-600 text-white font-semibold px-4 py-3 rounded-lg min-h-[44px] active:scale-[0.98] transition-all cursor-pointer disabled:opacity-50"
          >
            <Plus size={16} />
            {creating ? "建立中..." : "新增會議紀錄"}
          </button>
          <button
            onClick={handleOpenLinkIntel}
            className="flex items-center justify-center gap-2 border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 font-medium px-4 py-3 rounded-lg min-h-[44px] active:scale-[0.98] transition-all cursor-pointer"
          >
            <Link2 size={16} />
            關聯情報
          </button>
        </div>
      </div>

      {/* Link intel modal */}
      {showLinkIntel && (
        <div className="fixed inset-0 bg-slate-950/50 flex items-end md:items-center justify-center z-50">
          <div className="bg-white dark:bg-slate-900 rounded-t-2xl md:rounded-xl p-6 w-full max-w-md mx-auto space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold text-slate-900 dark:text-slate-50">
                關聯到情報
              </h3>
              <button
                onClick={() => setShowLinkIntel(false)}
                className="p-1.5 text-slate-400 hover:text-slate-200 cursor-pointer transition-colors"
              >
                <X size={20} />
              </button>
            </div>
            <div className="max-h-72 overflow-auto divide-y divide-slate-100 dark:divide-slate-800">
              {dealIntel.length === 0 ? (
                <p className="text-sm text-slate-400 py-4 text-center">沒有可關聯的情報</p>
              ) : (
                dealIntel.map((i) => (
                  <button
                    key={i.id}
                    onClick={() => handleLinkExistingIntel(i.id)}
                    className="w-full flex items-center justify-between py-3 px-1 hover:bg-slate-50 dark:hover:bg-slate-800/50 rounded transition-colors cursor-pointer text-left"
                  >
                    <span className="text-sm text-slate-900 dark:text-slate-50 line-clamp-1">
                      {getIntelDisplayTitle(i, 60)}
                    </span>
                    <span className="text-[11px] text-slate-400 flex-shrink-0 ml-2">
                      {new Date(i.created_at).toLocaleDateString("zh-TW")}
                    </span>
                  </button>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
