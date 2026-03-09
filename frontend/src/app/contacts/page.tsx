"use client";

import { useState, useEffect } from "react";
import { TopBar } from "@/components/top-bar";
import { nxApi, type NxClient, type NxPartner } from "@/lib/nexus-api";
import { Building2, Handshake } from "lucide-react";

const TRUST_LABELS: Record<string, string> = {
  unverified: "未驗證",
  testing: "驗證中",
  verified: "已驗證",
  core_team: "核心班底",
  si_backed: "SI 擔保",
  demoted: "不推薦",
};

const TRUST_COLORS: Record<string, string> = {
  unverified: "bg-amber-500/10 text-amber-400",
  testing: "bg-blue-500/10 text-blue-400",
  verified: "bg-green-500/10 text-green-400",
  core_team: "bg-green-500/10 text-green-400",
  si_backed: "bg-violet-500/10 text-violet-400",
  demoted: "bg-red-500/10 text-red-400",
};

export default function ContactsPage() {
  const [tab, setTab] = useState<"clients" | "partners">("clients");
  const [clients, setClients] = useState<NxClient[]>([]);
  const [partners, setPartners] = useState<NxPartner[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    if (tab === "clients") {
      nxApi.clients.list().then(setClients).catch(console.error).finally(() => setLoading(false));
    } else {
      nxApi.partners.list().then(setPartners).catch(console.error).finally(() => setLoading(false));
    }
  }, [tab]);

  return (
    <div className="flex flex-col h-full">
      <TopBar title="通訊錄" />

      {/* Sub-tabs */}
      <div className="px-4 pt-3 flex gap-2 border-b border-slate-200 dark:border-slate-800">
        <button
          onClick={() => setTab("clients")}
          className={`flex items-center gap-1.5 px-3 py-2 text-sm font-medium border-b-2 transition-colors cursor-pointer ${
            tab === "clients"
              ? "border-blue-500 text-blue-500"
              : "border-transparent text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
          }`}
        >
          <Building2 size={16} strokeWidth={1.5} />
          客戶
        </button>
        <button
          onClick={() => setTab("partners")}
          className={`flex items-center gap-1.5 px-3 py-2 text-sm font-medium border-b-2 transition-colors cursor-pointer ${
            tab === "partners"
              ? "border-blue-500 text-blue-500"
              : "border-transparent text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
          }`}
        >
          <Handshake size={16} strokeWidth={1.5} />
          夥伴
        </button>
      </div>

      <div className="flex-1 px-4 py-4 overflow-auto">
        {loading ? (
          <div className="flex items-center justify-center py-20 text-slate-400">載入中...</div>
        ) : tab === "clients" ? (
          clients.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 text-slate-400 dark:text-slate-500">
              <p className="text-sm">尚無客戶</p>
            </div>
          ) : (
            <div className="space-y-3 max-w-2xl lg:max-w-4xl mx-auto">
              {clients.map((c) => (
                <div
                  key={c.id}
                  className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4 cursor-pointer hover:border-slate-300 dark:hover:border-slate-600 transition-colors duration-200"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center flex-shrink-0">
                      <Building2 size={20} className="text-blue-500" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="text-base font-semibold text-slate-900 dark:text-slate-50 truncate">
                        {c.name}
                      </h3>
                      <p className="text-xs text-slate-500 dark:text-slate-400">
                        {c.industry || "—"} · {c.budget_range || "—"}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )
        ) : partners.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-slate-400 dark:text-slate-500">
            <p className="text-sm">尚無夥伴</p>
          </div>
        ) : (
          <div className="space-y-3 max-w-2xl lg:max-w-4xl mx-auto">
            {partners.map((p) => (
              <div
                key={p.id}
                className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4 cursor-pointer hover:border-slate-300 dark:hover:border-slate-600 transition-colors duration-200"
              >
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-green-500/10 flex items-center justify-center flex-shrink-0">
                    <Handshake size={20} className="text-green-500" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="text-base font-semibold text-slate-900 dark:text-slate-50 truncate">
                      {p.name}
                    </h3>
                    <div className="flex items-center gap-2 mt-1">
                      <span
                        className={`text-[11px] px-2 py-0.5 rounded-full font-medium ${
                          TRUST_COLORS[p.trust_level] || "bg-slate-700 text-slate-400"
                        }`}
                      >
                        {TRUST_LABELS[p.trust_level] || p.trust_level}
                      </span>
                      {p.team_size && (
                        <span className="text-[11px] text-slate-400">{p.team_size} 人</span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
