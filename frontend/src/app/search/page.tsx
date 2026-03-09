"use client";

import { useState, useCallback } from "react";
import { TopBar } from "@/components/top-bar";
import {
  Search as SearchIcon,
  TrendingUp,
  Building2,
  Handshake,
  User,
  Zap,
  Loader2,
  ChevronLeft,
} from "lucide-react";
import { nxApi, type SearchResults } from "@/lib/nexus-api";
import Link from "next/link";

type TabKey = "all" | "deals" | "clients" | "partners" | "contacts" | "intel";

const TABS: { key: TabKey; label: string }[] = [
  { key: "all", label: "全部" },
  { key: "deals", label: "商機" },
  { key: "clients", label: "客戶" },
  { key: "partners", label: "夥伴" },
  { key: "contacts", label: "人物" },
  { key: "intel", label: "情報" },
];

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResults | null>(null);
  const [tab, setTab] = useState<TabKey>("all");
  const [loading, setLoading] = useState(false);

  const doSearch = useCallback(async (q: string) => {
    if (!q.trim()) {
      setResults(null);
      return;
    }
    setLoading(true);
    try {
      const res = await nxApi.search(q.trim());
      setResults(res);
    } catch (err) {
      console.error("Search failed:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") doSearch(query);
  };

  const totalCount = results
    ? results.deals.length + results.clients.length + results.partners.length + results.contacts.length + results.intel.length
    : 0;

  return (
    <div className="flex flex-col h-full">
      <TopBar title="搜尋">
        <Link
          href="/dashboard"
          className="p-2 rounded-lg text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer transition-colors"
        >
          <ChevronLeft size={20} />
        </Link>
      </TopBar>

      <div className="px-4 pt-4 max-w-2xl lg:max-w-4xl mx-auto w-full">
        {/* Search input */}
        <div className="relative">
          <SearchIcon size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="搜尋商機、客戶、夥伴、情報..."
            autoFocus
            className="w-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl pl-10 pr-4 py-3 text-base text-slate-900 dark:text-slate-50 placeholder:text-slate-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
          />
        </div>

        {/* Filter tabs */}
        {results && (
          <div className="flex gap-2 mt-3 overflow-x-auto no-scrollbar">
            {TABS.map((t) => {
              const count = t.key === "all" ? totalCount : (results[t.key as keyof SearchResults] || []).length;
              if (t.key !== "all" && count === 0) return null;
              return (
                <button
                  key={t.key}
                  onClick={() => setTab(t.key)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors cursor-pointer ${
                    tab === t.key
                      ? "bg-blue-500/10 text-blue-500 border border-blue-500/30"
                      : "bg-slate-100 dark:bg-slate-800 text-slate-500 border border-slate-200 dark:border-slate-700"
                  }`}
                >
                  {t.label} ({count})
                </button>
              );
            })}
          </div>
        )}
      </div>

      <div className="flex-1 px-4 py-4 overflow-auto max-w-2xl lg:max-w-4xl mx-auto w-full">
        {loading && (
          <div className="flex items-center justify-center py-10">
            <Loader2 size={20} className="animate-spin text-blue-500" />
          </div>
        )}

        {!loading && !results && (
          <div className="flex flex-col items-center justify-center py-20 text-slate-400 dark:text-slate-500">
            <SearchIcon size={32} className="mb-2 opacity-30" />
            <p className="text-sm">輸入關鍵字搜尋</p>
          </div>
        )}

        {!loading && results && totalCount === 0 && (
          <div className="flex flex-col items-center justify-center py-20 text-slate-400 dark:text-slate-500">
            <p className="text-sm">找不到相關結果</p>
            <p className="text-xs mt-1">試試不同的關鍵字</p>
          </div>
        )}

        {!loading && results && totalCount > 0 && (
          <div className="space-y-4">
            {/* Deals */}
            {(tab === "all" || tab === "deals") && results.deals.length > 0 && (
              <ResultSection title="商機" icon={TrendingUp} count={results.deals.length}>
                {results.deals.map((d) => (
                  <Link key={d.id} href={`/deals/${d.id}`} className="block py-2 cursor-pointer group">
                    <p className="text-sm font-medium text-slate-900 dark:text-slate-50 group-hover:text-blue-500 transition-colors">
                      {d.name}
                    </p>
                    <p className="text-xs text-slate-400">{d.client_name} · {d.stage}</p>
                  </Link>
                ))}
              </ResultSection>
            )}

            {/* Clients */}
            {(tab === "all" || tab === "clients") && results.clients.length > 0 && (
              <ResultSection title="客戶" icon={Building2} count={results.clients.length}>
                {results.clients.map((c) => (
                  <div key={c.id} className="py-2">
                    <p className="text-sm font-medium text-slate-900 dark:text-slate-50">{c.name}</p>
                    <p className="text-xs text-slate-400">{c.industry || "—"} · {c.status}</p>
                  </div>
                ))}
              </ResultSection>
            )}

            {/* Partners */}
            {(tab === "all" || tab === "partners") && results.partners.length > 0 && (
              <ResultSection title="夥伴" icon={Handshake} count={results.partners.length}>
                {results.partners.map((p) => (
                  <div key={p.id} className="py-2">
                    <p className="text-sm font-medium text-slate-900 dark:text-slate-50">{p.name}</p>
                    <p className="text-xs text-slate-400">信任等級: {p.trust_level}</p>
                  </div>
                ))}
              </ResultSection>
            )}

            {/* Contacts */}
            {(tab === "all" || tab === "contacts") && results.contacts.length > 0 && (
              <ResultSection title="人物" icon={User} count={results.contacts.length}>
                {results.contacts.map((c) => (
                  <div key={c.id} className="py-2">
                    <p className="text-sm font-medium text-slate-900 dark:text-slate-50">{c.name}</p>
                    <p className="text-xs text-slate-400">{c.title || "—"}</p>
                  </div>
                ))}
              </ResultSection>
            )}

            {/* Intel */}
            {(tab === "all" || tab === "intel") && results.intel.length > 0 && (
              <ResultSection title="情報" icon={Zap} count={results.intel.length}>
                {results.intel.map((i) => (
                  <div key={i.id} className="py-2">
                    <p className="text-sm text-slate-700 dark:text-slate-300 line-clamp-2">{i.raw_input}</p>
                    <p className="text-xs text-slate-400 mt-0.5">
                      {i.status} · {new Date(i.created_at).toLocaleDateString("zh-TW")}
                    </p>
                  </div>
                ))}
              </ResultSection>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function ResultSection({
  title,
  icon: Icon,
  count,
  children,
}: {
  title: string;
  icon: React.ComponentType<{ size?: number; className?: string }>;
  count: number;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4">
      <div className="flex items-center gap-2 mb-2">
        <Icon size={16} className="text-blue-500" />
        <span className="text-sm font-semibold text-slate-900 dark:text-slate-50">{title}</span>
        <span className="text-xs text-slate-400">({count})</span>
      </div>
      <div className="divide-y divide-slate-100 dark:divide-slate-800">{children}</div>
    </div>
  );
}
