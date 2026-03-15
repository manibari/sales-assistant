"use client";

import { useEffect, useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import {
  Loader2,
  Building2,
  Briefcase,
  ArrowUpDown,
  Users,
  TrendingUp,
  ChevronRight,
} from "lucide-react";
import { nxApi, type NxClient, type NxDeal, type NxContact } from "@/lib/nexus-api";

type SortKey = "deals" | "name" | "industry" | "budget";

const STAGE_ORDER: Record<string, number> = {
  L0: 0, L1: 1, L2: 2, L3: 3, L4: 4, L5: 5, L6: 6,
};

const STAGE_LABELS: Record<string, string> = {
  L0: "初步接觸",
  L1: "需求確認",
  L2: "提案中",
  L3: "評估中",
  L4: "議價中",
  L5: "簽約中",
  L6: "成交",
};

interface ClientNode {
  client: NxClient;
  deals: NxDeal[];
  contacts: NxContact[];
  dealCount: number;
  maxStage: number;
  totalBudget: number;
}

export default function NetworkPage() {
  const router = useRouter();
  const [clients, setClients] = useState<NxClient[]>([]);
  const [deals, setDeals] = useState<NxDeal[]>([]);
  const [contacts, setContacts] = useState<NxContact[]>([]);
  const [loading, setLoading] = useState(true);
  const [sortKey, setSortKey] = useState<SortKey>("deals");
  const [expandedId, setExpandedId] = useState<number | null>(null);

  useEffect(() => {
    Promise.all([
      nxApi.clients.list("active"),
      nxApi.deals.list("urgency"),
      nxApi.contacts.list("client"),
    ])
      .then(([c, d, ct]) => {
        setClients(c);
        setDeals(d.filter((deal) => deal.status === "active"));
        setContacts(ct);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const nodes: ClientNode[] = useMemo(() => {
    return clients.map((client) => {
      const clientDeals = deals.filter((d) => d.client_id === client.id);
      const clientContacts = contacts.filter(
        (c) => c.org_type === "client" && c.org_id === client.id
      );
      const maxStage = clientDeals.reduce(
        (max, d) => Math.max(max, STAGE_ORDER[d.stage] ?? 0),
        -1
      );
      const totalBudget = clientDeals.reduce(
        (sum, d) => sum + (d.budget_amount || 0),
        0
      );
      return {
        client,
        deals: clientDeals,
        contacts: clientContacts,
        dealCount: clientDeals.length,
        maxStage,
        totalBudget,
      };
    });
  }, [clients, deals, contacts]);

  const sorted = useMemo(() => {
    const copy = [...nodes];
    switch (sortKey) {
      case "deals":
        // Primary: deal count desc, secondary: max stage desc
        copy.sort(
          (a, b) =>
            b.dealCount - a.dealCount ||
            b.maxStage - a.maxStage ||
            b.totalBudget - a.totalBudget
        );
        break;
      case "budget":
        copy.sort((a, b) => b.totalBudget - a.totalBudget || b.dealCount - a.dealCount);
        break;
      case "industry":
        copy.sort((a, b) => {
          const ai = a.client.industry || "zzz";
          const bi = b.client.industry || "zzz";
          return ai.localeCompare(bi) || b.dealCount - a.dealCount;
        });
        break;
      case "name":
        copy.sort((a, b) => a.client.name.localeCompare(b.client.name));
        break;
    }
    return copy;
  }, [nodes, sortKey]);

  const withDeals = sorted.filter((n) => n.dealCount > 0);
  const withoutDeals = sorted.filter((n) => n.dealCount === 0);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 size={24} className="animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="h-14 px-4 flex items-center justify-between border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
        <h1 className="text-xl font-bold text-slate-900 dark:text-slate-50">
          關係網絡
        </h1>
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <span>{clients.length} 客戶</span>
          <span className="text-slate-300 dark:text-slate-600">|</span>
          <span>{deals.length} 商機</span>
        </div>
      </div>

      <div className="flex-1 px-4 py-4 overflow-auto max-w-2xl lg:max-w-4xl mx-auto w-full space-y-4">
        {/* Sort controls */}
        <div className="flex items-center gap-2">
          <ArrowUpDown size={14} className="text-slate-400" />
          <span className="text-xs text-slate-400">排序：</span>
          {(
            [
              { key: "deals", label: "商機數" },
              { key: "budget", label: "預算" },
              { key: "industry", label: "產業" },
              { key: "name", label: "名稱" },
            ] as { key: SortKey; label: string }[]
          ).map(({ key, label }) => (
            <button
              key={key}
              onClick={() => setSortKey(key)}
              className={`text-xs px-2.5 py-1 rounded-lg border cursor-pointer transition-colors ${
                sortKey === key
                  ? "border-blue-500 bg-blue-500/10 text-blue-500"
                  : "border-slate-200 dark:border-slate-700 text-slate-500 hover:text-slate-300"
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        {/* Clients WITH deals — elevated section */}
        {withDeals.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <TrendingUp size={14} className="text-green-500" />
              <h2 className="text-sm font-semibold text-green-500">
                有商機 ({withDeals.length})
              </h2>
            </div>
            {withDeals.map((node) => (
              <ClientCard
                key={node.client.id}
                node={node}
                expanded={expandedId === node.client.id}
                onToggle={() =>
                  setExpandedId(
                    expandedId === node.client.id ? null : node.client.id
                  )
                }
                onNavigate={(id) => router.push(`/deals/${id}`)}
              />
            ))}
          </div>
        )}

        {/* Clients WITHOUT deals */}
        {withoutDeals.length > 0 && (
          <div className="space-y-2">
            <h2 className="text-sm font-semibold text-slate-400">
              尚無商機 ({withoutDeals.length})
            </h2>
            {withoutDeals.map((node) => (
              <ClientCard
                key={node.client.id}
                node={node}
                expanded={expandedId === node.client.id}
                onToggle={() =>
                  setExpandedId(
                    expandedId === node.client.id ? null : node.client.id
                  )
                }
                onNavigate={(id) => router.push(`/deals/${id}`)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function ClientCard({
  node,
  expanded,
  onToggle,
  onNavigate,
}: {
  node: ClientNode;
  expanded: boolean;
  onToggle: () => void;
  onNavigate: (dealId: number) => void;
}) {
  const { client, deals, contacts, dealCount, totalBudget } = node;
  const hasDeals = dealCount > 0;

  return (
    <div
      className={`bg-white dark:bg-slate-900 border rounded-xl overflow-hidden transition-colors ${
        hasDeals
          ? "border-green-500/30"
          : "border-slate-200 dark:border-slate-700"
      }`}
    >
      <button
        onClick={onToggle}
        className="w-full p-4 flex items-center justify-between gap-3 text-left cursor-pointer"
      >
        <div className="flex items-center gap-3 min-w-0 flex-1">
          <div
            className={`w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 ${
              hasDeals
                ? "bg-green-500/10 text-green-500"
                : "bg-slate-100 dark:bg-slate-800 text-slate-400"
            }`}
          >
            <Building2 size={18} />
          </div>
          <div className="min-w-0">
            <p className="text-sm font-medium text-slate-900 dark:text-slate-50 truncate">
              {client.name}
            </p>
            <div className="flex items-center gap-2 mt-0.5">
              {client.industry && (
                <span className="text-[11px] px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-500">
                  {client.industry}
                </span>
              )}
              {contacts.length > 0 && (
                <span className="inline-flex items-center gap-0.5 text-[11px] text-slate-400">
                  <Users size={10} />
                  {contacts.length}
                </span>
              )}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3 flex-shrink-0">
          {hasDeals && (
            <>
              <span className="inline-flex items-center gap-1 text-xs font-medium text-green-500">
                <Briefcase size={12} />
                {dealCount}
              </span>
              {totalBudget > 0 && (
                <span className="text-[11px] text-slate-400">
                  {formatBudget(totalBudget)}
                </span>
              )}
            </>
          )}
          <ChevronRight
            size={14}
            className={`text-slate-400 transition-transform ${expanded ? "rotate-90" : ""}`}
          />
        </div>
      </button>

      {expanded && deals.length > 0 && (
        <div className="border-t border-slate-100 dark:border-slate-800 px-4 py-2 space-y-1.5">
          {deals.map((deal) => (
            <button
              key={deal.id}
              onClick={() => onNavigate(deal.id)}
              className="w-full flex items-center justify-between gap-2 px-3 py-2 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800 cursor-pointer transition-colors text-left"
            >
              <div className="min-w-0 flex-1">
                <p className="text-xs font-medium text-slate-700 dark:text-slate-300 truncate">
                  {deal.name}
                </p>
              </div>
              <div className="flex items-center gap-2 flex-shrink-0">
                <StageBadge stage={deal.stage} />
                {deal.budget_amount && (
                  <span className="text-[10px] text-slate-400">
                    {formatBudget(deal.budget_amount)}
                  </span>
                )}
              </div>
            </button>
          ))}
        </div>
      )}

      {expanded && deals.length === 0 && (
        <div className="border-t border-slate-100 dark:border-slate-800 px-4 py-3 text-xs text-slate-400">
          尚無進行中的商機
        </div>
      )}
    </div>
  );
}

function StageBadge({ stage }: { stage: string }) {
  const level = STAGE_ORDER[stage] ?? 0;
  const color =
    level >= 5
      ? "bg-green-500/10 text-green-500"
      : level >= 3
        ? "bg-blue-500/10 text-blue-500"
        : level >= 1
          ? "bg-amber-500/10 text-amber-500"
          : "bg-slate-100 dark:bg-slate-800 text-slate-500";
  return (
    <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${color}`}>
      {stage} {STAGE_LABELS[stage] || ""}
    </span>
  );
}

function formatBudget(amount: number): string {
  if (amount >= 1_000_000) return `${(amount / 1_000_000).toFixed(1)}M`;
  if (amount >= 1_000) return `${(amount / 1_000).toFixed(0)}K`;
  return String(amount);
}
