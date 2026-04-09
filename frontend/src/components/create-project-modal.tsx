"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { X, Briefcase } from "lucide-react";
import { nxApi } from "@/lib/nexus-api";

export function CreateProjectModal({
  dealId,
  defaultName,
  onClose,
}: {
  dealId: number;
  defaultName: string;
  onClose: () => void;
}) {
  const router = useRouter();
  const [name, setName] = useState(defaultName);
  const [pmId, setPmId] = useState<number | null>(null);
  const [startDate, setStartDate] = useState(new Date().toISOString().slice(0, 10));
  const [endDate, setEndDate] = useState("");
  const [users, setUsers] = useState<{ id: number; name: string }[]>([]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    nxApi.deals.listUsers().then(setUsers).catch(console.error);
  }, []);

  const handleSubmit = async () => {
    if (!name.trim()) return;
    setSaving(true);
    setError("");
    try {
      const proj = await nxApi.projects.create({
        deal_id: dealId,
        name: name.trim(),
        pm_id: pmId,
        start_date: startDate || null,
        end_date: endDate || null,
      });
      router.push(`/projects/${proj.id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "建立失敗");
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-xl w-full max-w-md mx-4 overflow-hidden">
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-200 dark:border-slate-700">
          <div className="flex items-center gap-2">
            <Briefcase size={18} className="text-indigo-500" />
            <h2 className="text-base font-semibold text-slate-900 dark:text-slate-50">
              建立交付專案
            </h2>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 cursor-pointer"
          >
            <X size={18} />
          </button>
        </div>

        <div className="px-5 py-4 space-y-3">
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">專案名稱 *</label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full text-sm px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 focus:outline-none focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">PM (專案經理)</label>
            <select
              value={pmId ?? ""}
              onChange={(e) => setPmId(e.target.value ? Number(e.target.value) : null)}
              className="w-full text-sm px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 focus:outline-none focus:border-blue-500"
            >
              <option value="">未指定</option>
              {users.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.name}
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">起始日</label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full text-sm px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 focus:outline-none focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">預計結束</label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-full text-sm px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>

          <p className="text-[11px] text-slate-400">
            CSM 可以在交付完成後再指派。建立後可在專案頁加入成員。
          </p>

          {error && <p className="text-xs text-red-500">{error}</p>}
        </div>

        <div className="flex justify-end gap-2 px-5 py-4 border-t border-slate-200 dark:border-slate-700">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 text-slate-600 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800"
          >
            取消
          </button>
          <button
            onClick={handleSubmit}
            disabled={saving || !name.trim()}
            className="px-4 py-2 text-sm rounded-lg bg-blue-500 text-white font-medium cursor-pointer hover:bg-blue-600 disabled:opacity-50"
          >
            {saving ? "建立中..." : "建立並前往"}
          </button>
        </div>
      </div>
    </div>
  );
}
