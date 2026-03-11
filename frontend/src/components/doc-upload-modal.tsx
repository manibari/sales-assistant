"use client";

import { useState } from "react";
import { X, Loader2, Link2, Check } from "lucide-react";
import { nxApi } from "@/lib/nexus-api";

interface DocUploadModalProps {
  docId: number;
  currentPath: string | null;
  onClose: () => void;
  onUploaded: () => void;
}

export function DocUploadModal({ docId, currentPath, onClose, onUploaded }: DocUploadModalProps) {
  const [filePath, setFilePath] = useState(currentPath || "");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async () => {
    if (!filePath.trim()) return;
    setSaving(true);
    setError("");
    try {
      await nxApi.documents.update(docId, { file_path: filePath.trim() });
      onUploaded();
    } catch {
      setError("上傳失敗，請重試");
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-slate-950/50 flex items-end md:items-center justify-center z-50">
      <div className="bg-white dark:bg-slate-900 rounded-t-2xl md:rounded-xl p-6 w-full max-w-md mx-auto space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-bold text-slate-900 dark:text-slate-50">
            {currentPath ? "更換文件" : "上傳文件"}
          </h3>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-200 cursor-pointer transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        <div>
          <label className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-1 block">
            文件路徑或連結
          </label>
          <div className="relative">
            <Link2 size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={filePath}
              onChange={(e) => setFilePath(e.target.value)}
              placeholder="貼上檔案路徑或 Google Drive 連結"
              className="w-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg pl-10 pr-4 py-3 text-base text-slate-900 dark:text-slate-50 placeholder:text-slate-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
              autoFocus
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
            disabled={!filePath.trim() || saving}
            className="flex-1 bg-blue-500 hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold px-4 py-3 rounded-lg min-h-[44px] active:scale-[0.98] transition-all cursor-pointer"
          >
            {saving ? <Loader2 size={20} className="animate-spin mx-auto" /> : "確認"}
          </button>
        </div>
      </div>
    </div>
  );
}
