"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { TopBar } from "@/components/top-bar";
import { nxApi, type NxPlan, type NxClient, type NxDeal } from "@/lib/nexus-api";
import { Archive, ArrowLeft, Save } from "lucide-react";
import Link from "next/link";

const STATUS_LABELS: Record<string, string> = {
  draft: "草稿",
  active: "進行中",
  archived: "已封存",
};

const TYPE_LABELS: Record<string, string> = {
  annual: "年度計劃",
  product: "產品策略",
  internal: "營運計畫",
  proposal: "客戶提案",
};

export default function PlanDetailPage() {
  const params = useParams();
  const router = useRouter();
  const planId = Number(params.id);

  const [plan, setPlan] = useState<NxPlan | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Editable fields
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [status, setStatus] = useState("draft");
  const [fiscalYear, setFiscalYear] = useState<number | null>(null);
  const [notes, setNotes] = useState("");
  const [dealId, setDealId] = useState<number | null>(null);
  const [clientId, setClientId] = useState<number | null>(null);

  // For proposal type selectors
  const [clients, setClients] = useState<NxClient[]>([]);
  const [deals, setDeals] = useState<NxDeal[]>([]);

  const loadPlan = useCallback(() => {
    setLoading(true);
    nxApi.plans
      .get(planId)
      .then((p) => {
        setPlan(p);
        setTitle(p.title);
        setBody(p.body || "");
        setStatus(p.status);
        setFiscalYear(p.fiscal_year);
        setNotes(p.notes || "");
        setDealId(p.deal_id);
        setClientId(p.client_id);
        if (p.plan_type === "proposal") {
          nxApi.clients.list().then(setClients).catch(console.error);
          nxApi.deals.list().then(setDeals).catch(console.error);
        }
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [planId]);

  useEffect(() => { loadPlan(); }, [loadPlan]);

  const handleSave = async () => {
    setSaving(true);
    try {
      const updated = await nxApi.plans.update(planId, {
        title,
        body: body || null,
        status,
        fiscal_year: fiscalYear,
        notes: notes || null,
        deal_id: plan?.plan_type === "proposal" ? dealId : null,
        client_id: plan?.plan_type === "proposal" ? clientId : null,
      } as Partial<NxPlan>);
      setPlan(updated);
    } catch (err) {
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  const handleArchive = async () => {
    if (!confirm("確定要封存此計畫？")) return;
    try {
      await nxApi.plans.archive(planId);
      router.push("/strategy");
    } catch (err) {
      console.error(err);
    }
  };

  if (loading) {
    return (
      <>
        <TopBar title="載入中..." />
        <div className="p-4 text-sm text-slate-500">載入中...</div>
      </>
    );
  }

  if (!plan) {
    return (
      <>
        <TopBar title="找不到計畫" />
        <div className="p-4 text-sm text-slate-500">此計畫不存在。</div>
      </>
    );
  }

  return (
    <>
      <TopBar title={plan.title}>
        <button
          onClick={handleSave}
          disabled={saving}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600 text-white text-sm hover:bg-blue-500 disabled:opacity-50 transition-colors cursor-pointer"
        >
          <Save size={16} /> {saving ? "儲存中..." : "儲存"}
        </button>
        {plan.status !== "archived" && (
          <button
            onClick={handleArchive}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 text-slate-600 dark:text-slate-400 text-sm hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
          >
            <Archive size={16} /> 封存
          </button>
        )}
      </TopBar>

      <div className="p-4 space-y-6">
        {/* Back link */}
        <Link
          href="/strategy"
          className="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"
        >
          <ArrowLeft size={14} /> 返回列表
        </Link>

        {/* Metadata row */}
        <div className="flex flex-wrap items-center gap-4">
          <span className="px-2 py-0.5 rounded text-xs font-medium bg-slate-500/10 text-slate-500">
            {TYPE_LABELS[plan.plan_type] || plan.plan_type}
          </span>

          {/* Status selector */}
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            className="px-2 py-1 rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm"
          >
            {Object.entries(STATUS_LABELS).map(([val, label]) => (
              <option key={val} value={val}>{label}</option>
            ))}
          </select>

          {/* Fiscal year */}
          <div className="flex items-center gap-1.5">
            <span className="text-xs text-slate-500">年度</span>
            <input
              type="number"
              value={fiscalYear || ""}
              onChange={(e) => setFiscalYear(e.target.value ? Number(e.target.value) : null)}
              className="w-24 px-2 py-1 rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm"
            />
          </div>
        </div>

        {/* Title */}
        <div>
          <label className="block text-xs font-medium text-slate-500 mb-1">標題</label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm font-medium"
          />
        </div>

        <div className="grid gap-6 lg:grid-cols-[1fr_300px]">
          {/* Main: Markdown body */}
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">內容 (Markdown)</label>
            <textarea
              value={body}
              onChange={(e) => setBody(e.target.value)}
              rows={24}
              className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm font-mono leading-relaxed resize-y"
              placeholder="在此編輯計畫內容..."
            />
          </div>

          {/* Sidebar */}
          <div className="space-y-4">
            {/* Proposal-specific: Client & Deal */}
            {plan.plan_type === "proposal" && (
              <>
                <div>
                  <label className="block text-xs font-medium text-slate-500 mb-1">關聯客戶</label>
                  <select
                    value={clientId || ""}
                    onChange={(e) => setClientId(e.target.value ? Number(e.target.value) : null)}
                    className="w-full px-2 py-1.5 rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm"
                  >
                    <option value="">-- 無 --</option>
                    {clients.map((c) => (
                      <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-500 mb-1">關聯商機</label>
                  <select
                    value={dealId || ""}
                    onChange={(e) => setDealId(e.target.value ? Number(e.target.value) : null)}
                    className="w-full px-2 py-1.5 rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm"
                  >
                    <option value="">-- 無 --</option>
                    {deals.map((d) => (
                      <option key={d.id} value={d.id}>{d.name}</option>
                    ))}
                  </select>
                </div>
              </>
            )}

            {/* Notes */}
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">備註</label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={4}
                className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm resize-y"
                placeholder="附加備註..."
              />
            </div>

            {/* Info */}
            <div className="text-xs text-slate-400 space-y-1">
              <p>建立：{new Date(plan.created_at).toLocaleString("zh-TW")}</p>
              <p>更新：{new Date(plan.updated_at).toLocaleString("zh-TW")}</p>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
