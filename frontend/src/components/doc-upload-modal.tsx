"use client";

import { useState } from "react";
import { X, Loader2, Link2, Upload, FileCheck } from "lucide-react";
import { nxApi } from "@/lib/nexus-api";

interface DocUploadModalProps {
  docId: number;
  currentPath: string | null;
  onClose: () => void;
  onUploaded: () => void;
}

export function DocUploadModal({ docId, currentPath, onClose, onUploaded }: DocUploadModalProps) {
  const [tab, setTab] = useState<"link" | "file">("link");
  const [filePath, setFilePath] = useState(currentPath || "");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const handleLinkSubmit = async () => {
    if (!filePath.trim()) return;
    setSaving(true);
    setError("");
    try {
      await nxApi.documents.update(docId, { file_path: filePath.trim() });
      onUploaded();
    } catch {
      setError("儲存失敗，請重試");
      setSaving(false);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) setSelectedFile(file);
  };

  const handleFileUpload = async () => {
    if (!selectedFile) return;
    setSaving(true);
    setError("");
    try {
      await nxApi.documents.uploadContractFile(docId, selectedFile);
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
            {currentPath ? "更換合約文件" : "上傳合約文件"}
          </h3>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-200 cursor-pointer transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {/* Tab toggle */}
        <div className="flex gap-2">
          <button
            onClick={() => setTab("link")}
            className={`flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium border transition-colors cursor-pointer ${
              tab === "link"
                ? "border-blue-500 bg-blue-500/10 text-blue-500"
                : "bg-slate-100 dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-500"
            }`}
          >
            <Link2 size={16} />
            貼上連結
          </button>
          <button
            onClick={() => setTab("file")}
            className={`flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium border transition-colors cursor-pointer ${
              tab === "file"
                ? "border-blue-500 bg-blue-500/10 text-blue-500"
                : "bg-slate-100 dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-500"
            }`}
          >
            <Upload size={16} />
            上傳檔案
          </button>
        </div>

        {/* Link input */}
        {tab === "link" && (
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
        )}

        {/* File picker */}
        {tab === "file" && (
          <div>
            {selectedFile ? (
              <div className="flex items-center gap-2 p-3 bg-slate-100 dark:bg-slate-800 rounded-lg">
                <FileCheck size={16} className="text-green-500 flex-shrink-0" />
                <span className="text-sm text-slate-700 dark:text-slate-300 truncate flex-1">
                  {selectedFile.name}
                </span>
                <button
                  onClick={() => setSelectedFile(null)}
                  className="text-slate-400 hover:text-red-400 cursor-pointer"
                >
                  <X size={14} />
                </button>
              </div>
            ) : (
              <label className="flex flex-col items-center justify-center gap-2 p-8 border-2 border-dashed border-slate-300 dark:border-slate-700 rounded-xl cursor-pointer hover:border-blue-500 transition-colors">
                <Upload size={24} className="text-slate-400" />
                <span className="text-sm text-slate-400">點擊選擇合約檔案</span>
                <span className="text-[11px] text-slate-500">PDF, DOCX</span>
                <input
                  type="file"
                  accept=".pdf,.docx,.doc"
                  onChange={handleFileSelect}
                  className="hidden"
                />
              </label>
            )}
          </div>
        )}

        {error && <p className="text-xs text-red-400">{error}</p>}

        <div className="flex gap-2">
          <button
            onClick={onClose}
            className="flex-1 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-700 font-medium px-4 py-3 rounded-lg min-h-[44px] cursor-pointer transition-colors"
          >
            取消
          </button>
          {tab === "link" ? (
            <button
              onClick={handleLinkSubmit}
              disabled={!filePath.trim() || saving}
              className="flex-1 bg-blue-500 hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold px-4 py-3 rounded-lg min-h-[44px] active:scale-[0.98] transition-all cursor-pointer"
            >
              {saving ? <Loader2 size={20} className="animate-spin mx-auto" /> : "確認"}
            </button>
          ) : (
            <button
              onClick={handleFileUpload}
              disabled={!selectedFile || saving}
              className="flex-1 bg-blue-500 hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold px-4 py-3 rounded-lg min-h-[44px] active:scale-[0.98] transition-all cursor-pointer"
            >
              {saving ? <Loader2 size={20} className="animate-spin mx-auto" /> : "上傳"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
