"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { TopBar } from "@/components/top-bar";
import { nxApi, type NxClient, type NxPartner } from "@/lib/nexus-api";
import { INDUSTRIES, formatBudget } from "@/lib/options";
import { Building2, Handshake, Plus, X, Loader2 } from "lucide-react";

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

const TRUST_OPTIONS = [
  { label: "未驗證", value: "unverified" },
  { label: "驗證中", value: "testing" },
  { label: "已驗證", value: "verified" },
  { label: "核心班底", value: "core_team" },
  { label: "SI 擔保", value: "si_backed" },
];

const TEAM_SIZES = ["1-5", "6-10", "11-20", "21-50", "50+"];

export default function ContactsPage() {
  const [tab, setTab] = useState<"clients" | "partners">("clients");
  const [clients, setClients] = useState<NxClient[]>([]);
  const [partners, setPartners] = useState<NxPartner[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);

  const loadData = () => {
    setLoading(true);
    if (tab === "clients") {
      nxApi.clients.list().then(setClients).catch(console.error).finally(() => setLoading(false));
    } else {
      nxApi.partners.list().then(setPartners).catch(console.error).finally(() => setLoading(false));
    }
  };

  useEffect(() => {
    loadData();
  }, [tab]);

  return (
    <div className="flex flex-col h-full">
      <TopBar title="關係網">
        <button
          onClick={() => setShowCreateModal(true)}
          className="p-2 rounded-lg text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer transition-colors"
          title={tab === "clients" ? "新增客戶" : "新增夥伴"}
        >
          <Plus size={20} />
        </button>
      </TopBar>

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
                <Link
                  key={c.id}
                  href={`/contacts/clients/${c.id}`}
                  className="block bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4 cursor-pointer hover:border-slate-300 dark:hover:border-slate-600 transition-colors duration-200"
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
                        {c.industry || "—"} · {formatBudget(c.deal_budget_total)}
                      </p>
                    </div>
                  </div>
                </Link>
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
              <Link
                key={p.id}
                href={`/contacts/partners/${p.id}`}
                className="block bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4 cursor-pointer hover:border-slate-300 dark:hover:border-slate-600 transition-colors duration-200"
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
              </Link>
            ))}
          </div>
        )}
      </div>

      {/* Create modal */}
      {showCreateModal && (
        tab === "clients" ? (
          <CreateClientModal
            onClose={() => setShowCreateModal(false)}
            onCreated={() => {
              setShowCreateModal(false);
              loadData();
            }}
          />
        ) : (
          <CreatePartnerModal
            onClose={() => setShowCreateModal(false)}
            onCreated={() => {
              setShowCreateModal(false);
              loadData();
            }}
          />
        )
      )}
    </div>
  );
}

function CreateClientModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [name, setName] = useState("");
  const [industry, setIndustry] = useState("");
  const [customIndustry, setCustomIndustry] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async () => {
    if (!name.trim()) return;
    setSaving(true);
    setError("");
    try {
      await nxApi.clients.create({
        name: name.trim(),
        industry: industry || undefined,
      });
      onCreated();
    } catch {
      setError("建立失敗，請重試");
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-slate-950/50 flex items-end md:items-center justify-center z-50">
      <div className="bg-white dark:bg-slate-900 rounded-t-2xl md:rounded-xl p-6 w-full max-w-md mx-auto space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-bold text-slate-900 dark:text-slate-50">新增客戶</h3>
          <button onClick={onClose} className="p-1.5 text-slate-400 hover:text-slate-200 cursor-pointer transition-colors">
            <X size={20} />
          </button>
        </div>

        <div className="space-y-3">
          <div>
            <label className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-1 block">客戶名稱 *</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="公司名稱"
              className="w-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-4 py-3 text-base text-slate-900 dark:text-slate-50 placeholder:text-slate-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
              autoFocus
            />
          </div>
          <div>
            <label className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-1 block">產業</label>
            {customIndustry ? (
              <div className="flex gap-2">
                <input
                  type="text"
                  value={industry}
                  onChange={(e) => setIndustry(e.target.value)}
                  placeholder="輸入產業名稱"
                  className="flex-1 bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-4 py-3 text-base text-slate-900 dark:text-slate-50 placeholder:text-slate-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
                  autoFocus
                />
                <button
                  onClick={() => { setCustomIndustry(false); setIndustry(""); }}
                  className="px-3 text-xs text-slate-400 hover:text-slate-600 cursor-pointer transition-colors"
                >
                  選擇
                </button>
              </div>
            ) : (
              <div className="flex gap-2">
                <select
                  value={industry}
                  onChange={(e) => setIndustry(e.target.value)}
                  className="flex-1 bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-4 py-3 text-base text-slate-900 dark:text-slate-50 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none cursor-pointer"
                >
                  <option value="">選擇產業</option>
                  {INDUSTRIES.map((i) => (
                    <option key={i.value} value={i.value}>{i.label}</option>
                  ))}
                </select>
                <button
                  onClick={() => { setCustomIndustry(true); setIndustry(""); }}
                  className="px-3 text-xs text-blue-500 hover:text-blue-400 cursor-pointer transition-colors whitespace-nowrap"
                >
                  自訂
                </button>
              </div>
            )}
          </div>
        </div>

        {error && <p className="text-xs text-red-400">{error}</p>}

        <div className="flex gap-2">
          <button
            onClick={onClose}
            className="flex-1 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-700 font-medium px-4 py-3 rounded-lg min-h-[44px] cursor-pointer transition-colors"
          >
            取消
          </button>
          <button
            onClick={handleSubmit}
            disabled={!name.trim() || saving}
            className="flex-1 bg-blue-500 hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold px-4 py-3 rounded-lg min-h-[44px] active:scale-[0.98] transition-all cursor-pointer"
          >
            {saving ? <Loader2 size={20} className="animate-spin mx-auto" /> : "建立"}
          </button>
        </div>
      </div>
    </div>
  );
}

function CreatePartnerModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [name, setName] = useState("");
  const [trustLevel, setTrustLevel] = useState("unverified");
  const [teamSize, setTeamSize] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async () => {
    if (!name.trim()) return;
    setSaving(true);
    setError("");
    try {
      await nxApi.partners.create({
        name: name.trim(),
        trust_level: trustLevel,
        team_size: teamSize || undefined,
      });
      onCreated();
    } catch {
      setError("建立失敗，請重試");
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-slate-950/50 flex items-end md:items-center justify-center z-50">
      <div className="bg-white dark:bg-slate-900 rounded-t-2xl md:rounded-xl p-6 w-full max-w-md mx-auto space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-bold text-slate-900 dark:text-slate-50">新增夥伴</h3>
          <button onClick={onClose} className="p-1.5 text-slate-400 hover:text-slate-200 cursor-pointer transition-colors">
            <X size={20} />
          </button>
        </div>

        <div className="space-y-3">
          <div>
            <label className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-1 block">夥伴名稱 *</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="公司名稱"
              className="w-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-4 py-3 text-base text-slate-900 dark:text-slate-50 placeholder:text-slate-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
              autoFocus
            />
          </div>
          <div>
            <label className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-1 block">信任等級</label>
            <select
              value={trustLevel}
              onChange={(e) => setTrustLevel(e.target.value)}
              className="w-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-4 py-3 text-base text-slate-900 dark:text-slate-50 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none cursor-pointer"
            >
              {TRUST_OPTIONS.map((t) => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-1 block">團隊規模</label>
            <select
              value={teamSize}
              onChange={(e) => setTeamSize(e.target.value)}
              className="w-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-4 py-3 text-base text-slate-900 dark:text-slate-50 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none cursor-pointer"
            >
              <option value="">選擇團隊規模</option>
              {TEAM_SIZES.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>
        </div>

        {error && <p className="text-xs text-red-400">{error}</p>}

        <div className="flex gap-2">
          <button
            onClick={onClose}
            className="flex-1 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-700 font-medium px-4 py-3 rounded-lg min-h-[44px] cursor-pointer transition-colors"
          >
            取消
          </button>
          <button
            onClick={handleSubmit}
            disabled={!name.trim() || saving}
            className="flex-1 bg-blue-500 hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold px-4 py-3 rounded-lg min-h-[44px] active:scale-[0.98] transition-all cursor-pointer"
          >
            {saving ? <Loader2 size={20} className="animate-spin mx-auto" /> : "建立"}
          </button>
        </div>
      </div>
    </div>
  );
}
