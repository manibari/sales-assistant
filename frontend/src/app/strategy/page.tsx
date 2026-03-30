"use client";

import { useState, useEffect, useMemo } from "react";
import { TopBar } from "@/components/top-bar";
import { nxApi, type NxPlan } from "@/lib/nexus-api";
import { Plus } from "lucide-react";
import Link from "next/link";

const TAB_CONFIG: { key: string; label: string; planType: string }[] = [
  { key: "annual", label: "年度計劃", planType: "annual" },
  { key: "product", label: "產品策略", planType: "product" },
  { key: "internal", label: "營運計畫", planType: "internal" },
  { key: "proposal", label: "客戶提案", planType: "proposal" },
];

const STATUS_LABELS: Record<string, string> = {
  draft: "草稿",
  active: "進行中",
  archived: "已封存",
};

const STATUS_COLORS: Record<string, string> = {
  draft: "bg-slate-500/10 text-slate-400",
  active: "bg-green-500/10 text-green-400",
  archived: "bg-gray-500/10 text-gray-500",
};

function formatDate(dateStr: string): string {
  const d = new Date(dateStr);
  return d.toLocaleDateString("zh-TW", { year: "numeric", month: "numeric", day: "numeric" });
}

export default function StrategyPage() {
  const [plans, setPlans] = useState<NxPlan[]>([]);
  const [tab, setTab] = useState("annual");
  const [showArchived, setShowArchived] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    nxApi.plans
      .list(tab)
      .then(setPlans)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [tab]);

  const filtered = useMemo(() => {
    if (showArchived) return plans;
    return plans.filter((p) => p.status !== "archived");
  }, [plans, showArchived]);

  return (
    <>
      <TopBar title="策略計畫">
        <Link
          href="/strategy/new"
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600 text-white text-sm hover:bg-blue-500 transition-colors"
        >
          <Plus size={16} /> 新增
        </Link>
      </TopBar>

      <div className="p-4 space-y-4">
        {/* Tabs */}
        <div className="flex items-center gap-1 border-b border-slate-200 dark:border-slate-800">
          {TAB_CONFIG.map((t) => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors cursor-pointer ${
                tab === t.key
                  ? "border-blue-500 text-blue-600 dark:text-blue-400"
                  : "border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"
              }`}
            >
              {t.label}
            </button>
          ))}
          <label className="ml-auto flex items-center gap-1.5 text-xs text-slate-500 cursor-pointer">
            <input
              type="checkbox"
              checked={showArchived}
              onChange={(e) => setShowArchived(e.target.checked)}
              className="rounded"
            />
            顯示已封存
          </label>
        </div>

        {/* Content */}
        {loading ? (
          <p className="text-sm text-slate-500">載入中...</p>
        ) : filtered.length === 0 ? (
          <p className="text-sm text-slate-500">尚無計畫，點擊右上角新增。</p>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {filtered.map((plan) => (
              <Link
                key={plan.id}
                href={`/strategy/${plan.id}`}
                className="block p-4 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-blue-400 dark:hover:border-blue-600 transition-colors"
              >
                <div className="flex items-start justify-between gap-2">
                  <h3 className="font-medium text-sm text-slate-900 dark:text-slate-100 line-clamp-2">
                    {plan.title}
                  </h3>
                  <span className={`shrink-0 px-2 py-0.5 rounded text-xs font-medium ${STATUS_COLORS[plan.status] || STATUS_COLORS.draft}`}>
                    {STATUS_LABELS[plan.status] || plan.status}
                  </span>
                </div>
                {plan.fiscal_year && (
                  <p className="mt-1 text-xs text-slate-500">FY {plan.fiscal_year}</p>
                )}
                {tab === "proposal" && (plan.client_name || plan.deal_name) && (
                  <p className="mt-1 text-xs text-slate-500">
                    {plan.client_name && <span>{plan.client_name}</span>}
                    {plan.client_name && plan.deal_name && <span> · </span>}
                    {plan.deal_name && <span>{plan.deal_name}</span>}
                  </p>
                )}
                <p className="mt-2 text-xs text-slate-400">
                  更新於 {formatDate(plan.updated_at)}
                </p>
              </Link>
            ))}
          </div>
        )}
      </div>
    </>
  );
}
