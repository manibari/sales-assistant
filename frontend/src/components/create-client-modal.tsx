"use client";

import { useState } from "react";
import { X, Loader2 } from "lucide-react";
import { nxApi } from "@/lib/nexus-api";
import { INDUSTRIES } from "@/lib/options";

interface CreateClientModalProps {
  onClose: () => void;
  onCreated: () => void;
}

export function CreateClientModal({ onClose, onCreated }: CreateClientModalProps) {
  const [name, setName] = useState("");
  const [industry, setIndustry] = useState("");
  const [market, setMarket] = useState<"domestic" | "overseas">("domestic");
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
        market,
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
          <div>
            <label className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-1 block">市場</label>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setMarket("domestic")}
                className={`flex-1 min-h-[44px] px-3 py-2 text-sm font-medium rounded-lg border transition-colors cursor-pointer ${
                  market === "domestic"
                    ? "border-blue-500 bg-blue-500/10 text-blue-500"
                    : "bg-slate-100 dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200"
                }`}
              >
                國內
              </button>
              <button
                type="button"
                onClick={() => setMarket("overseas")}
                className={`flex-1 min-h-[44px] px-3 py-2 text-sm font-medium rounded-lg border transition-colors cursor-pointer ${
                  market === "overseas"
                    ? "border-amber-500 bg-amber-500/10 text-amber-500"
                    : "bg-slate-100 dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200"
                }`}
              >
                海外
              </button>
            </div>
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
