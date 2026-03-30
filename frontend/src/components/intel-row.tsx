"use client";

import { useState } from "react";
import Link from "next/link";
import { Check, X, Pencil, ExternalLink } from "lucide-react";
import { nxApi } from "@/lib/nexus-api";

export function IntelRow({
  intelId,
  title,
  date,
  editing,
  onUnlink,
  onTitleSaved,
}: {
  intelId: number;
  title: string;
  date?: string;
  editing: boolean;
  onUnlink: () => void;
  onTitleSaved: () => void;
}) {
  const [editingTitle, setEditingTitle] = useState(false);
  const [draft, setDraft] = useState("");
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    if (!draft.trim() || saving) return;
    setSaving(true);
    try {
      await nxApi.intel.update(intelId, { title: draft.trim() });
      setEditingTitle(false);
      onTitleSaved();
    } catch (err) {
      console.error("Failed to save intel title:", err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="flex items-start justify-between py-2 gap-2">
      <div className="flex-1 min-w-0">
        {editingTitle ? (
          <div className="flex items-center gap-1.5">
            <input
              type="text"
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") handleSave(); if (e.key === "Escape") setEditingTitle(false); }}
              className="flex-1 text-sm bg-slate-100 dark:bg-slate-800 border border-blue-500 rounded px-2 py-1 text-slate-900 dark:text-slate-50 focus:outline-none"
              autoFocus
              placeholder="情報標題..."
            />
            <button onClick={handleSave} disabled={saving} className="p-1 text-blue-500 hover:text-blue-600 cursor-pointer disabled:opacity-50"><Check size={14} /></button>
            <button onClick={() => setEditingTitle(false)} className="p-1 text-slate-400 hover:text-slate-500 cursor-pointer"><X size={14} /></button>
          </div>
        ) : (
          <div className="group">
            <Link
              href={`/intel/${intelId}`}
              className="text-sm text-slate-700 dark:text-slate-300 hover:text-blue-500 dark:hover:text-blue-400 line-clamp-2 transition-colors"
            >
              {title}
              <ExternalLink size={11} className="inline ml-1 opacity-0 group-hover:opacity-50 transition-opacity" />
            </Link>
          </div>
        )}
        <span className="text-[11px] text-slate-400 mt-1 block">
          {date ? new Date(date).toLocaleDateString("zh-TW") : ""}
        </span>
      </div>
      {editing && !editingTitle && (
        <div className="flex items-center gap-1 flex-shrink-0 mt-0.5">
          <button
            onClick={() => { setDraft(title); setEditingTitle(true); }}
            className="p-1 text-slate-400 hover:text-blue-500 hover:bg-blue-500/10 rounded cursor-pointer transition-colors"
            title="修改標題"
          >
            <Pencil size={13} />
          </button>
          <button
            onClick={onUnlink}
            className="p-1 text-red-400 hover:text-red-500 hover:bg-red-500/10 rounded cursor-pointer transition-colors"
            title="取消關聯"
          >
            <X size={14} />
          </button>
        </div>
      )}
    </div>
  );
}
