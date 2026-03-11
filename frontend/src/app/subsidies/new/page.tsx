"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { TopBar } from "@/components/top-bar";
import { ChevronLeft, Loader2 } from "lucide-react";
import { nxApi, type NxClient, type NxPartner } from "@/lib/nexus-api";
import Link from "next/link";

const TYPE_OPTIONS = [
  { label: "SBIR", value: "sbir" },
  { label: "SIIR", value: "siir" },
  { label: "地方型", value: "local" },
  { label: "其他", value: "other" },
];

export default function NewSubsidyPage() {
  const router = useRouter();

  const [clients, setClients] = useState<NxClient[]>([]);
  const [partners, setPartners] = useState<NxPartner[]>([]);
  const [name, setName] = useState("");
  const [programType, setProgramType] = useState("other");
  const [agency, setAgency] = useState("");
  const [deadline, setDeadline] = useState("");
  const [fundingAmount, setFundingAmount] = useState("");
  const [eligibility, setEligibility] = useState("");
  const [scope, setScope] = useState("");
  const [requiredDocs, setRequiredDocs] = useState("");
  const [referenceUrl, setReferenceUrl] = useState("");
  const [clientId, setClientId] = useState<number | null>(null);
  const [partnerId, setPartnerId] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    nxApi.clients.list().then(setClients).catch(console.error);
    nxApi.partners.list().then(setPartners).catch(console.error);
  }, []);

  const handleSubmit = async () => {
    if (!name.trim()) return;
    setSaving(true);
    try {
      const subsidy = await nxApi.subsidies.create({
        name: name.trim(),
        program_type: programType,
        agency: agency || undefined,
        deadline: deadline || undefined,
        funding_amount: fundingAmount || undefined,
        eligibility: eligibility || undefined,
        scope: scope || undefined,
        required_docs: requiredDocs || undefined,
        reference_url: referenceUrl || undefined,
        client_id: clientId ?? undefined,
        partner_id: partnerId ?? undefined,
      });
      router.push(`/subsidies/${subsidy.id}`);
    } catch (err) {
      console.error("Failed to create subsidy:", err);
      setSaving(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <TopBar title="新增補助案">
        <Link
          href="/subsidies"
          className="p-2 rounded-lg text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer transition-colors"
        >
          <ChevronLeft size={20} />
        </Link>
      </TopBar>

      <div className="flex-1 px-4 py-6 overflow-auto max-w-2xl mx-auto w-full space-y-6">
        {/* Name */}
        <div>
          <label className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-2 block">
            計畫名稱 *
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="例：113年 SBIR 創新研發計畫"
            className="w-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-4 py-3 text-base text-slate-900 dark:text-slate-50 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none transition-colors"
          />
        </div>

        {/* Program type */}
        <div>
          <label className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-2 block">
            計畫類型
          </label>
          <div className="grid grid-cols-4 gap-2">
            {TYPE_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={() => setProgramType(opt.value)}
                className={`min-h-[44px] px-3 py-2 text-sm font-medium rounded-lg border transition-colors cursor-pointer ${
                  programType === opt.value
                    ? "border-blue-500 bg-blue-500/10 text-blue-500 dark:text-blue-400"
                    : "bg-slate-100 dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-50 hover:border-blue-500"
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        {/* Agency */}
        <div>
          <label className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-2 block">
            主辦機關
          </label>
          <input
            type="text"
            value={agency}
            onChange={(e) => setAgency(e.target.value)}
            placeholder="例：經濟部中小及新創企業署"
            className="w-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-4 py-3 text-base text-slate-900 dark:text-slate-50 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none transition-colors"
          />
        </div>

        {/* Deadline */}
        <div>
          <label className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-2 block">
            申請截止日
          </label>
          <input
            type="date"
            value={deadline}
            onChange={(e) => setDeadline(e.target.value)}
            className="w-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-4 py-3 text-base text-slate-900 dark:text-slate-50 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none transition-colors"
          />
        </div>

        {/* Funding amount */}
        <div>
          <label className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-2 block">
            補助額度
          </label>
          <input
            type="text"
            value={fundingAmount}
            onChange={(e) => setFundingAmount(e.target.value)}
            placeholder="例：50-100萬"
            className="w-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-4 py-3 text-base text-slate-900 dark:text-slate-50 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none transition-colors"
          />
        </div>

        {/* Eligibility */}
        <div>
          <label className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-2 block">
            申請資格
          </label>
          <textarea
            value={eligibility}
            onChange={(e) => setEligibility(e.target.value)}
            rows={2}
            placeholder="申請資格條件..."
            className="w-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-4 py-3 text-base text-slate-900 dark:text-slate-50 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none transition-colors resize-none"
          />
        </div>

        {/* Scope */}
        <div>
          <label className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-2 block">
            申請範疇
          </label>
          <textarea
            value={scope}
            onChange={(e) => setScope(e.target.value)}
            rows={2}
            placeholder="計畫申請範疇..."
            className="w-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-4 py-3 text-base text-slate-900 dark:text-slate-50 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none transition-colors resize-none"
          />
        </div>

        {/* Required docs */}
        <div>
          <label className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-2 block">
            申請文件
          </label>
          <textarea
            value={requiredDocs}
            onChange={(e) => setRequiredDocs(e.target.value)}
            rows={2}
            placeholder="需要準備的文件..."
            className="w-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-4 py-3 text-base text-slate-900 dark:text-slate-50 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none transition-colors resize-none"
          />
        </div>

        {/* Reference URL */}
        <div>
          <label className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-2 block">
            參考連結
          </label>
          <input
            type="url"
            value={referenceUrl}
            onChange={(e) => setReferenceUrl(e.target.value)}
            placeholder="https://..."
            className="w-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-4 py-3 text-base text-slate-900 dark:text-slate-50 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none transition-colors"
          />
        </div>

        {/* Client / Partner */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-2 block">
              關聯客戶
            </label>
            <select
              value={clientId ?? ""}
              onChange={(e) => setClientId(e.target.value ? Number(e.target.value) : null)}
              className="w-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-4 py-3 text-base text-slate-900 dark:text-slate-50 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none transition-colors"
            >
              <option value="">無</option>
              {clients.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-2 block">
              關聯夥伴
            </label>
            <select
              value={partnerId ?? ""}
              onChange={(e) => setPartnerId(e.target.value ? Number(e.target.value) : null)}
              className="w-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-4 py-3 text-base text-slate-900 dark:text-slate-50 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none transition-colors"
            >
              <option value="">無</option>
              {partners.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Submit */}
        <button
          onClick={handleSubmit}
          disabled={!name.trim() || saving}
          className="w-full flex items-center justify-center gap-2 bg-blue-500 hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold px-6 py-3 rounded-lg min-h-[44px] active:scale-[0.98] transition-all duration-200 cursor-pointer"
        >
          {saving ? <Loader2 size={20} className="animate-spin" /> : "建立補助案"}
        </button>
      </div>
    </div>
  );
}
