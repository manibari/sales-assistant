"use client";

import { useState } from "react";
import { X, Loader2 } from "lucide-react";
import { nxApi, type NxContact } from "@/lib/nexus-api";

interface ContactFormModalProps {
  orgType: "client" | "partner";
  orgId: number;
  contact?: NxContact;
  onClose: () => void;
  onCreated: () => void;
}

export function ContactFormModal({ orgType, orgId, contact, onClose, onCreated }: ContactFormModalProps) {
  const isEdit = !!contact;
  const [name, setName] = useState(contact?.name || "");
  const [title, setTitle] = useState(contact?.title || "");
  const [phone, setPhone] = useState(contact?.phone || "");
  const [email, setEmail] = useState(contact?.email || "");
  const [lineId, setLineId] = useState(contact?.line_id || "");
  const [role, setRole] = useState(contact?.role || "");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async () => {
    if (!name.trim()) return;
    setSaving(true);
    setError("");
    try {
      const data = {
        name: name.trim(),
        title: title.trim() || undefined,
        phone: phone.trim() || undefined,
        email: email.trim() || undefined,
        line_id: lineId.trim() || undefined,
        role: role.trim() || undefined,
      };
      if (isEdit) {
        await nxApi.contacts.update(contact.id, data);
      } else {
        await nxApi.contacts.create({
          ...data,
          org_type: orgType,
          org_id: orgId,
        });
      }
      onCreated();
      onClose();
    } catch {
      setError(isEdit ? "更新失敗，請重試" : "建立失敗，請重試");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-slate-950/50 flex items-end md:items-center justify-center z-50">
      <div className="bg-white dark:bg-slate-900 rounded-t-2xl md:rounded-xl p-6 w-full max-w-md mx-auto space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-bold text-slate-900 dark:text-slate-50">
            {isEdit ? "編輯聯絡人" : "新增聯絡人"}
          </h3>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-200 cursor-pointer transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        <div className="space-y-3">
          <div>
            <label className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-1 block">
              姓名 *
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="聯絡人姓名"
              className="w-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-4 py-3 text-base text-slate-900 dark:text-slate-50 placeholder:text-slate-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
              autoFocus
            />
          </div>
          <div>
            <label className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-1 block">
              職稱
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="例：副廠長、業務經理"
              className="w-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-4 py-3 text-base text-slate-900 dark:text-slate-50 placeholder:text-slate-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
            />
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-1 block">
                電話
              </label>
              <input
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="0912-345-678"
                className="w-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-4 py-3 text-base text-slate-900 dark:text-slate-50 placeholder:text-slate-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-1 block">
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@co.com"
                className="w-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-4 py-3 text-base text-slate-900 dark:text-slate-50 placeholder:text-slate-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-1 block">
                LINE
              </label>
              <input
                type="text"
                value={lineId}
                onChange={(e) => setLineId(e.target.value)}
                placeholder="LINE ID"
                className="w-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-4 py-3 text-base text-slate-900 dark:text-slate-50 placeholder:text-slate-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
              />
            </div>
          </div>
          <div>
            <label className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-1 block">
              角色
            </label>
            <input
              type="text"
              value={role}
              onChange={(e) => setRole(e.target.value)}
              placeholder="例：決策者、技術窗口、使用者"
              className="w-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-4 py-3 text-base text-slate-900 dark:text-slate-50 placeholder:text-slate-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
            />
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
            {saving ? <Loader2 size={20} className="animate-spin mx-auto" /> : isEdit ? "儲存" : "建立"}
          </button>
        </div>
      </div>
    </div>
  );
}
