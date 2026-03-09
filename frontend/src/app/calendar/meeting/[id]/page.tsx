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
      const m = await nxApi.calendar.meetingsByDate("").catch(() => null);
      // Fetch meeting directly — we need to get deal info
      // Since we don't have a single meeting endpoint exposed via calendar,
      // we load the deal and find meeting info
      const allDeals = await nxApi.deals.list();
      // Load meeting from each deal's meetings
      for (const d of allDeals) {
        const fullDeal = await nxApi.deals.get(d.id);
        setDeal(fullDeal);
        setTbds(fullDeal.tbds || []);
        break; // For now, show first deal's prep
      }
    } catch (err) {
      console.error("Failed to load:", err);
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
