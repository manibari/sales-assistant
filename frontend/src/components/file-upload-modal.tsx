"use client";

import { useState } from "react";
import { X, Link2, Upload, Loader2 } from "lucide-react";
import { nxApi } from "@/lib/nexus-api";

interface FileUploadModalProps {
  dealId: number;
  onClose: () => void;
  onUploaded: () => void;
}

export function FileUploadModal({ dealId, onClose, onUploaded }: FileUploadModalProps) {
  const [tab, setTab] = useState<"link" | "file">("link");
  const [url, setUrl] = useState("");
  const [fileType, setFileType] = useState("proposal");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const FILE_TYPES = [
    { label: "簡報/方案", value: "proposal" },
    { label: "合約 (NDA/MOU)", value: "contract" },
    { label: "其他附件", value: "attachment" },
  ];

  const handleLinkSubmit = async () => {
    if (!url.trim()) return;
    setSaving(true);
    setError("");
    try {
      // Extract filename from URL
      const fileName = url.includes("drive.google.com")
        ? "Google Drive 文件"
        : url.split("/").pop() || "連結文件";
      await nxApi.deals.update(dealId, {}); // touch deal
      // Create file record
      const res = await fetch("/api/nx/documents/files", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          deal_id: dealId,
          file_type: fileType,
          file_name: fileName,
          file_path: `link://${url}`,
          source_url: url,
        }),
      });
      if (!res.ok) throw new Error("Failed to save");
      onUploaded();
      onClose();
    } catch (err) {
      setError("儲存失敗，請確認連結是否正確");
    } finally {
      setSaving(false);
    }
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setSaving(true);
    setError("");
    try {
      // In production, this would upload to storage. For now, create metadata record.
      const res = await fetch("/api/nx/documents/files", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          deal_id: dealId,
          file_type: fileType,
          file_name: file.name,
          file_path: `/uploads/${file.name}`,
          file_size: file.size,
        }),
      });
      if (!res.ok) throw new Error("Failed to save");
      onUploaded();
      onClose();
    } catch (err) {
      setError("上傳失敗");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-slate-950/50 flex items-end md:items-center justify-center z-50">
      <div className="bg-white dark:bg-slate-900 rounded-t-2xl md:rounded-xl p-6 w-full max-w-md mx-auto space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-bold text-slate-900 dark:text-slate-50">
            新增文件
          </h3>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-200 cursor-pointer transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {/* File type selection */}
        <div>
          <label className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-2 block">
            文件類型
          </label>
          <div className="grid grid-cols-3 gap-2">
            {FILE_TYPES.map((ft) => (
              <button
                key={ft.value}
                onClick={() => setFileType(ft.value)}
                className={`min-h-[44px] px-3 py-2 text-xs font-medium rounded-lg border transition-colors cursor-pointer ${
                  fileType === ft.value
                    ? "border-blue-500 bg-blue-500/10 text-blue-500 dark:text-blue-400"
                    : "bg-slate-100 dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200"
                }`}
              >
                {ft.label}
              </button>
            ))}
          </div>
        </div>

        {/* Upload method tabs */}
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
            從裝置選擇
          </button>
        </div>

        {/* Link input */}
        {tab === "link" && (
          <div>
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="貼上 Google Drive 連結或其他 URL..."
              className="w-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-4 py-3 text-base text-slate-900 dark:text-slate-50 placeholder:text-slate-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
            />
            <p className="text-[11px] text-slate-400 mt-1">
              支援 Google Drive、Dropbox 或直接下載連結
            </p>
          </div>
        )}

        {/* File picker */}
        {tab === "file" && (
          <div>
            <label className="flex flex-col items-center justify-center gap-2 p-8 border-2 border-dashed border-slate-300 dark:border-slate-700 rounded-xl cursor-pointer hover:border-blue-500 transition-colors">
              <Upload size={24} className="text-slate-400" />
              <span className="text-sm text-slate-400">
                點擊選擇檔案
              </span>
              <span className="text-[11px] text-slate-500">
                PDF, PPT, PPTX, DOCX
              </span>
              <input
                type="file"
                accept=".pdf,.ppt,.pptx,.docx,.doc"
                onChange={handleFileSelect}
                className="hidden"
              />
            </label>
          </div>
        )}

        {error && (
          <p className="text-xs text-red-400">{error}</p>
        )}

        {/* Submit for link */}
        {tab === "link" && (
          <button
            onClick={handleLinkSubmit}
            disabled={!url.trim() || saving}
            className="w-full bg-blue-500 hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold px-6 py-3 rounded-lg min-h-[44px] active:scale-[0.98] transition-all cursor-pointer"
          >
            {saving ? <Loader2 size={20} className="animate-spin mx-auto" /> : "儲存"}
          </button>
        )}

        {saving && tab === "file" && (
          <div className="flex items-center justify-center py-2">
            <Loader2 size={20} className="animate-spin text-blue-500" />
            <span className="text-sm text-slate-400 ml-2">上傳中...</span>
          </div>
        )}
      </div>
    </div>
  );
}
