"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { TopBar } from "@/components/top-bar";
import { nxApi, type NxClient, type NxDeal } from "@/lib/nexus-api";

const PLAN_TYPES = [
  { value: "annual", label: "年度計劃" },
  { value: "product", label: "產品策略" },
  { value: "internal", label: "營運計畫" },
  { value: "proposal", label: "客戶提案" },
];

export default function NewPlanPage() {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [planType, setPlanType] = useState("annual");
  const [fiscalYear, setFiscalYear] = useState<number>(new Date().getFullYear());
  const [clientId, setClientId] = useState<number | undefined>();
  const [dealId, setDealId] = useState<number | undefined>();
  const [saving, setSaving] = useState(false);

  const [clients, setClients] = useState<NxClient[]>([]);
  const [deals, setDeals] = useState<NxDeal[]>([]);

  useEffect(() => {
    if (planType === "proposal") {
      nxApi.clients.list().then(setClients).catch(console.error);
      nxApi.deals.list().then(setDeals).catch(console.error);
    }
  }, [planType]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;
    setSaving(true);
    try {
      const plan = await nxApi.plans.create({
        title: title.trim(),
        plan_type: planType,
        fiscal_year: fiscalYear || undefined,
        client_id: planType === "proposal" ? clientId : undefined,
        deal_id: planType === "proposal" ? dealId : undefined,
      });
      router.push(`/strategy/${plan.id}`);
    } catch (err) {
      console.error(err);
      setSaving(false);
    }
  };

  return (
    <>
      <TopBar title="新增策略計畫" />
      <div className="p-4 max-w-lg">
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Plan Type */}
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
              計畫類型
            </label>
            <div className="flex gap-2 flex-wrap">
              {PLAN_TYPES.map((pt) => (
                <button
                  key={pt.value}
                  type="button"
                  onClick={() => setPlanType(pt.value)}
                  className={`px-3 py-1.5 rounded-lg text-sm border transition-colors cursor-pointer ${
                    planType === pt.value
                      ? "border-blue-500 bg-blue-500/10 text-blue-600 dark:text-blue-400"
                      : "border-slate-300 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:border-slate-400"
                  }`}
                >
                  {pt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Title */}
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
              標題
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="例：115 年度銷售計劃"
              className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm"
              required
            />
          </div>

          {/* Fiscal Year */}
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
              年度
            </label>
            <input
              type="number"
              value={fiscalYear}
              onChange={(e) => setFiscalYear(Number(e.target.value))}
              className="w-32 px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm"
            />
          </div>

          {/* Proposal-specific: Client & Deal */}
          {planType === "proposal" && (
            <>
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                  關聯客戶
                </label>
                <select
                  value={clientId || ""}
                  onChange={(e) => setClientId(e.target.value ? Number(e.target.value) : undefined)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm"
                >
                  <option value="">-- 選擇客戶 --</option>
                  {clients.map((c) => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                  關聯商機
                </label>
                <select
                  value={dealId || ""}
                  onChange={(e) => setDealId(e.target.value ? Number(e.target.value) : undefined)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm"
                >
                  <option value="">-- 選擇商機 --</option>
                  {deals.map((d) => (
                    <option key={d.id} value={d.id}>{d.name} ({d.client_name})</option>
                  ))}
                </select>
              </div>
            </>
          )}

          <button
            type="submit"
            disabled={saving || !title.trim()}
            className="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-500 disabled:opacity-50 transition-colors cursor-pointer"
          >
            {saving ? "建立中..." : "建立計畫"}
          </button>
        </form>
      </div>
    </>
  );
}
