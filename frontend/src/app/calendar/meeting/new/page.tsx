"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { TopBar } from "@/components/top-bar";
import { ChevronLeft, Loader2 } from "lucide-react";
import { nxApi, type NxDeal } from "@/lib/nexus-api";
import Link from "next/link";

export default function NewMeetingPage() {
  const router = useRouter();
  const [deals, setDeals] = useState<NxDeal[]>([]);
  const [dealId, setDealId] = useState<number | null>(null);
  const [title, setTitle] = useState("");
  const [date, setDate] = useState("");
  const [time, setTime] = useState("14:00");
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    nxApi.deals.list().then(setDeals).catch(console.error);
  }, []);

  const handleSubmit = async () => {
    if (!dealId || !title.trim() || !date) return;
    setSaving(true);
    try {
      await nxApi.calendar.createMeeting({
        deal_id: dealId,
        title: title.trim(),
        meeting_date: `${date}T${time}:00`,
      });
      router.push("/calendar");
    } catch (err) {
      console.error("Failed to create meeting:", err);
      setSaving(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <TopBar title="新增會議">
        <Link
          href="/calendar"
          className="p-2 rounded-lg text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer transition-colors"
        >
          <ChevronLeft size={20} />
        </Link>
      </TopBar>

      <div className="flex-1 px-4 py-6 overflow-auto max-w-2xl mx-auto w-full space-y-6">
        <div>
          <label className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-2 block">
            關聯商機 *
          </label>
          <select
            value={dealId ?? ""}
            onChange={(e) => setDealId(e.target.value ? Number(e.target.value) : null)}
            className="w-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-4 py-3 text-base text-slate-900 dark:text-slate-50 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
          >
            <option value="">選擇商機...</option>
            {deals.map((d) => (
              <option key={d.id} value={d.id}>{d.name}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-2 block">
            會議名稱 *
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="例：A 食品 — AOI 需求訪談"
            className="w-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-4 py-3 text-base text-slate-900 dark:text-slate-50 placeholder:text-slate-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-2 block">
              日期 *
            </label>
            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              className="w-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-4 py-3 text-base text-slate-900 dark:text-slate-50 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-2 block">
              時間
            </label>
            <input
              type="time"
              value={time}
              onChange={(e) => setTime(e.target.value)}
              className="w-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-4 py-3 text-base text-slate-900 dark:text-slate-50 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
            />
          </div>
        </div>

        <div>
          <label className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-2 block">
            備註
          </label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="備註..."
            className="w-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-4 py-3 text-base text-slate-900 dark:text-slate-50 placeholder:text-slate-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none resize-none h-20"
          />
        </div>

        <button
          onClick={handleSubmit}
          disabled={!dealId || !title.trim() || !date || saving}
          className="w-full bg-blue-500 hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold px-6 py-3 rounded-lg min-h-[44px] active:scale-[0.98] transition-all cursor-pointer"
        >
          {saving ? <Loader2 size={20} className="animate-spin mx-auto" /> : "排定會議"}
        </button>
      </div>
    </div>
  );
}
