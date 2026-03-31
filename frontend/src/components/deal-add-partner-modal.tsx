"use client";

import { useState } from "react";
import { X } from "lucide-react";
import { nxApi, type NxDeal, type NxPartner } from "@/lib/nexus-api";

const TRUST_LABELS: Record<string, string> = {
  unverified: "未驗證", testing: "驗證中", verified: "已驗證",
  core_team: "核心班底", si_backed: "SI 擔保", demoted: "不推薦",
};

interface DealAddPartnerModalProps {
  dealId: number;
  deal: NxDeal;
  allPartners: NxPartner[];
  onClose: () => void;
  onAdded: () => void;
}

export function DealAddPartnerModal({ dealId, deal, allPartners, onClose, onAdded }: DealAddPartnerModalProps) {
  const [partnerRole, setPartnerRole] = useState("");

  const available = allPartners.filter(
    (p) => !(deal.partners || []).some((dp) => dp.partner_id === p.id)
  );

  return (
    <div className="fixed inset-0 bg-slate-950/50 flex items-end md:items-center justify-center z-50">
      <div className="bg-white dark:bg-slate-900 rounded-t-2xl md:rounded-xl p-6 w-full max-w-md mx-auto space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-bold text-slate-900 dark:text-slate-50">新增搭配夥伴</h3>
          <button onClick={onClose} className="p-1.5 text-slate-400 hover:text-slate-200 cursor-pointer transition-colors">
            <X size={20} />
          </button>
        </div>
        <div>
          <label className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-1 block">角色 (選填)</label>
          <input
            type="text"
            value={partnerRole}
            onChange={(e) => setPartnerRole(e.target.value)}
            placeholder="例：系統整合、硬體供應"
            className="w-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-4 py-3 text-sm text-slate-900 dark:text-slate-50 placeholder:text-slate-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
          />
        </div>
        <div className="max-h-72 overflow-auto divide-y divide-slate-100 dark:divide-slate-800">
          {allPartners.length === 0 ? (
            <p className="text-sm text-slate-400 py-4 text-center">載入中...</p>
          ) : available.length === 0 ? (
            <p className="text-sm text-slate-400 py-4 text-center">所有夥伴已配對</p>
          ) : (
            available.map((p) => (
              <button
                key={p.id}
                onClick={async () => {
                  try {
                    await nxApi.deals.addPartner(dealId, p.id, partnerRole || undefined);
                    onClose();
                    onAdded();
                  } catch (err) { console.error(err); }
                }}
                className="w-full flex items-center justify-between py-3 px-1 hover:bg-slate-50 dark:hover:bg-slate-800/50 rounded transition-colors cursor-pointer text-left"
              >
                <span className="text-sm text-slate-900 dark:text-slate-50">{p.name}</span>
                <span className="text-[11px] px-2 py-0.5 rounded-full bg-green-500/10 text-green-400">
                  {TRUST_LABELS[p.trust_level] || p.trust_level}
                </span>
              </button>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
