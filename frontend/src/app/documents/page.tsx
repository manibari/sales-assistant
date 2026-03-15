"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import { TopBar } from "@/components/top-bar";
import Link from "next/link";
import {
  Building2,
  FileText,
  AlertTriangle,
  Clock,
  Loader2,
  Search,
  CheckCircle,
  ChevronRight,
  ShieldCheck,
  FolderOpen,
} from "lucide-react";
import { nxApi, type ClientDocSummary } from "@/lib/nexus-api";

function daysUntilExpiry(expiryDate: string | null): number | null {
  if (!expiryDate) return null;
  const diff = new Date(expiryDate).getTime() - Date.now();
  return Math.ceil(diff / (1000 * 60 * 60 * 24));
}

function DocStatusChip({ label, status }: { label: string; status: string | null }) {
  if (!status)
    return (
      <span className="text-[11px] px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-400">
        {label} --
      </span>
    );
  if (status === "signed")
    return (
      <span className="text-[11px] px-2 py-0.5 rounded-full bg-green-500/10 text-green-400">
        {label} ✓
      </span>
    );
  return (
    <span className="text-[11px] px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-500">
      {label} …
    </span>
  );
}

export default function DocumentsPage() {
  const [clients, setClients] = useState<ClientDocSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  const loadData = useCallback(async () => {
    try {
      const data = await nxApi.documents.clientsSummary();
      setClients(data);
    } catch (err) {
      console.error("Failed to load document summary:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const filtered = useMemo(() => {
    if (!search.trim()) return clients;
    const q = search.toLowerCase();
    return clients.filter(
      (c) =>
        c.name.toLowerCase().includes(q) ||
        (c.industry && c.industry.toLowerCase().includes(q)),
    );
  }, [clients, search]);

  const totalClients = clients.length;
  const signedContracts = clients.filter(
    (c) => c.nda_status === "signed" || c.mou_status === "signed",
  ).length;
  const expiringCount = clients.filter((c) => {
    const days = daysUntilExpiry(c.earliest_expiry);
    return days !== null && days >= 0 && days <= 30;
  }).length;
  const missingDocs = clients.filter(
    (c) => !c.nda_status && !c.mou_status,
  ).length;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 size={24} className="animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <TopBar title="文件中心" />

      <div className="flex-1 px-4 py-4 overflow-auto max-w-2xl lg:max-w-4xl mx-auto w-full space-y-3">
        {/* Summary cards */}
        <div className="grid grid-cols-4 gap-3">
          <SummaryCard
            icon={<Building2 size={16} />}
            label="公司數"
            value={totalClients}
            color="text-slate-700 dark:text-slate-200"
          />
          <SummaryCard
            icon={<ShieldCheck size={16} />}
            label="已簽合約"
            value={signedContracts}
            color="text-green-600 dark:text-green-400"
          />
          <SummaryCard
            icon={<Clock size={16} />}
            label="即將到期"
            value={expiringCount}
            color="text-amber-600 dark:text-amber-400"
          />
          <SummaryCard
            icon={<AlertTriangle size={16} />}
            label="缺 NDA/MOU"
            value={missingDocs}
            color="text-red-600 dark:text-red-400"
          />
        </div>

        {/* Search */}
        <div className="relative">
          <Search
            size={16}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
          />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="搜尋公司名稱或產業..."
            className="w-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl pl-10 pr-4 py-2.5 text-sm text-slate-900 dark:text-slate-50 placeholder:text-slate-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
          />
        </div>

        {/* Client list */}
        {filtered.length === 0 ? (
          <div className="text-center py-12 text-slate-400 text-sm">
            {search ? "沒有符合的公司" : "尚無文件資料"}
          </div>
        ) : (
          <div className="space-y-2">
            {filtered.map((client) => (
              <ClientRow key={client.id} client={client} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function ClientRow({ client }: { client: ClientDocSummary }) {
  const days = daysUntilExpiry(client.earliest_expiry);
  const hasExpiry = days !== null && days >= 0 && days <= 30;
  const isExpired = days !== null && days < 0;

  return (
    <Link
      href={`/documents/${client.id}`}
      className="block bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4 hover:border-blue-500/50 transition-colors"
    >
      <div className="flex items-center justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <p className="text-sm font-semibold text-slate-900 dark:text-slate-50 truncate">
              {client.name}
            </p>
            {client.industry && (
              <span className="text-[11px] px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-500 flex-shrink-0">
                {client.industry}
              </span>
            )}
          </div>
          <div className="flex items-center gap-3 mt-1.5">
            <DocStatusChip label="NDA" status={client.nda_status} />
            <DocStatusChip label="MOU" status={client.mou_status} />
            {isExpired && (
              <span className="text-[11px] px-2 py-0.5 rounded-full bg-red-500/10 text-red-400 font-medium">
                已過期
              </span>
            )}
            {!isExpired && hasExpiry && (
              <span className="text-[11px] px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-500 font-medium">
                {days} 天到期
              </span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-3 flex-shrink-0">
          <div className="flex items-center gap-1 text-xs text-slate-400">
            <FolderOpen size={14} />
            <span>{client.file_count}</span>
          </div>
          <div className="flex items-center gap-1 text-xs text-slate-400">
            <FileText size={14} />
            <span>{client.contract_count}</span>
          </div>
          <ChevronRight size={16} className="text-slate-300" />
        </div>
      </div>
    </Link>
  );
}

function SummaryCard({
  icon,
  label,
  value,
  color,
}: {
  icon: React.ReactNode;
  label: string;
  value: number;
  color: string;
}) {
  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-3 text-center">
      <div className={`flex justify-center mb-1 ${color}`}>{icon}</div>
      <p className={`text-xl font-bold ${color}`}>{value}</p>
      <p className="text-xs text-slate-500 mt-0.5">{label}</p>
    </div>
  );
}
