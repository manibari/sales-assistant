"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { TopBar } from "@/components/top-bar";
import { ChevronLeft, Loader2 } from "lucide-react";
import { nxApi, type NxClient } from "@/lib/nexus-api";
import Link from "next/link";

const BUDGET_OPTIONS = ["<100K", "100-500K", "500K-1M", "1M+", "unknown"];
const TIMELINE_OPTIONS = [
  { label: "本季", value: "this_quarter" },
  { label: "下季", value: "next_quarter" },
  { label: "半年內", value: "half_year" },
  { label: "一年內", value: "one_year" },
  { label: "未定", value: "undecided" },
];

function NewDealForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const prefilledClientId = searchParams.get("client_id");

  const [clients, setClients] = useState<NxClient[]>([]);
  const [clientId, setClientId] = useState<number | null>(
    prefilledClientId ? Number(prefilledClientId) : null
  );
  const [name, setName] = useState("");
  const [budget, setBudget] = useState("");
  const [timeline, setTimeline] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    nxApi.clients.list().then(setClients).catch(console.error);
  }, []);

  const handleSubmit = async () => {
    if (!name.trim() || !clientId) return;
    setSaving(true);
    try {
      const deal = await nxApi.deals.create({
        name: name.trim(),
        client_id: clientId,
        budget_range: budget || undefined,
        timeline: timeline || undefined,
      });
      router.push(`/deals/${deal.id}`);
    } catch (err) {
      console.error("Failed to create deal:", err);
      setSaving(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <TopBar title="建立商機">
        <Link
          href="/deals"
          className="p-2 rounded-lg text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer transition-colors"
        >
          <ChevronLeft size={20} />
        </Link>
      </TopBar>

      <div className="flex-1 px-4 py-6 overflow-auto max-w-2xl mx-auto w-full space-y-6">
        {/* Client selection */}
        <div>
          <label className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-2 block">
            選擇客戶 *
          </label>
          <select
            value={clientId ?? ""}
            onChange={(e) => setClientId(e.target.value ? Number(e.target.value) : null)}
            className="w-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-4 py-3 text-base text-slate-900 dark:text-slate-50 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none transition-colors"
          >
            <option value="">選擇客戶...</option>
            {clients.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name} ({c.industry || "—"})
              </option>
            ))}
          </select>
        </div>

        {/* Deal name */}
        <div>
          <label className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-2 block">
            商機名稱 *
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="例：A 食品 AOI 產線自動化"
            className="w-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-4 py-3 text-base text-slate-900 dark:text-slate-50 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none transition-colors"
          />
        </div>

        {/* Budget */}
        <div>
          <label className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-2 block">
            預估預算
          </label>
          <div className="grid grid-cols-3 gap-2">
            {BUDGET_OPTIONS.map((opt) => (
              <button
                key={opt}
                onClick={() => setBudget(budget === opt ? "" : opt)}
                className={`min-h-[44px] px-3 py-2 text-sm font-medium rounded-lg border transition-colors cursor-pointer ${
                  budget === opt
                    ? "border-blue-500 bg-blue-500/10 text-blue-500 dark:text-blue-400"
                    : "bg-slate-100 dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-50 hover:border-blue-500"
                }`}
              >
                {opt === "unknown" ? "未知" : opt}
              </button>
            ))}
          </div>
        </div>

        {/* Timeline */}
        <div>
          <label className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-2 block">
            預估時程
          </label>
          <div className="grid grid-cols-3 gap-2">
            {TIMELINE_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={() => setTimeline(timeline === opt.value ? "" : opt.value)}
                className={`min-h-[44px] px-3 py-2 text-sm font-medium rounded-lg border transition-colors cursor-pointer ${
                  timeline === opt.value
                    ? "border-blue-500 bg-blue-500/10 text-blue-500 dark:text-blue-400"
                    : "bg-slate-100 dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-50 hover:border-blue-500"
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        {/* Submit */}
        <button
          onClick={handleSubmit}
          disabled={!name.trim() || !clientId || saving}
          className="w-full flex items-center justify-center gap-2 bg-blue-500 hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold px-6 py-3 rounded-lg min-h-[44px] active:scale-[0.98] transition-all duration-200 cursor-pointer"
        >
          {saving ? <Loader2 size={20} className="animate-spin" /> : "建立商機"}
        </button>
      </div>
    </div>
  );
}

export default function NewDealPage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center h-full"><Loader2 size={24} className="animate-spin text-blue-500" /></div>}>
      <NewDealForm />
    </Suspense>
  );
}
