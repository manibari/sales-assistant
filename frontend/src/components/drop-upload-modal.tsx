"use client";

import { useState, useEffect } from "react";
import { X, Loader2, File as FileIcon, Trash2 } from "lucide-react";
import { nxApi, type NxDeal } from "@/lib/nexus-api";

interface DropUploadModalProps {
  files: File[];
  clientId: number;
  onClose: () => void;
  onUploaded: () => void;
}

const FILE_CATEGORIES = [
  { label: "專案文件", value: "project" },
  { label: "合約文件", value: "contract" },
];

const FILE_TYPES = [
  { label: "簡報/方案", value: "proposal" },
  { label: "簡報", value: "presentation" },
  { label: "合約", value: "contract" },
  { label: "附件", value: "attachment" },
];

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function DropUploadModal({ files: initialFiles, clientId, onClose, onUploaded }: DropUploadModalProps) {
  const [fileList, setFileList] = useState(
    initialFiles.map((f) => ({ file: f, included: true })),
  );
  const [category, setCategory] = useState("project");
  const [fileType, setFileType] = useState("attachment");
  const [dealId, setDealId] = useState<number | null>(null);
  const [deals, setDeals] = useState<NxDeal[]>([]);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState("");

  useEffect(() => {
    nxApi.deals.listByClient(clientId).then(setDeals).catch(() => {});
  }, [clientId]);

  const includedFiles = fileList.filter((f) => f.included);

  const removeFile = (idx: number) => {
    setFileList((prev) => prev.map((f, i) => (i === idx ? { ...f, included: false } : f)));
  };

  const handleUpload = async () => {
    if (includedFiles.length === 0) return;
    setUploading(true);
    setError("");
    setProgress(0);

    const resolvedFileType = category === "contract" ? "contract" : fileType;

    try {
      for (let i = 0; i < includedFiles.length; i++) {
        const { file } = includedFiles[i];
        const formData = new FormData();
        formData.append("file", file);
        formData.append("client_id", String(clientId));
        formData.append("file_type", resolvedFileType);
        if (dealId) formData.append("deal_id", String(dealId));

        await nxApi.files.upload(formData);
        setProgress(i + 1);
      }
      onUploaded();
      onClose();
    } catch {
      setError("部分檔案上傳失敗，請重試");
      setUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-slate-950/50 flex items-end md:items-center justify-center z-50">
      <div className="bg-white dark:bg-slate-900 rounded-t-2xl md:rounded-xl p-6 w-full max-w-lg mx-auto space-y-4 max-h-[80vh] overflow-auto">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-bold text-slate-900 dark:text-slate-50">
            上傳 {includedFiles.length} 個檔案
          </h3>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-200 cursor-pointer transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {/* File list */}
        <div className="space-y-1 max-h-40 overflow-auto">
          {fileList.map((item, idx) =>
            item.included ? (
              <div
                key={idx}
                className="flex items-center gap-2 px-3 py-2 bg-slate-50 dark:bg-slate-800 rounded-lg"
              >
                <FileIcon size={14} className="text-blue-500 flex-shrink-0" />
                <span className="text-sm text-slate-700 dark:text-slate-300 truncate flex-1">
                  {item.file.name}
                </span>
                <span className="text-[11px] text-slate-400">{formatSize(item.file.size)}</span>
                <button
                  onClick={() => removeFile(idx)}
                  className="text-slate-400 hover:text-red-400 cursor-pointer"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            ) : null,
          )}
        </div>

        {/* Category */}
        <div>
          <label className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-2 block">
            分類
          </label>
          <div className="grid grid-cols-2 gap-2">
            {FILE_CATEGORIES.map((c) => (
              <button
                key={c.value}
                onClick={() => setCategory(c.value)}
                className={`min-h-[44px] px-3 py-2 text-sm font-medium rounded-lg border transition-colors cursor-pointer ${
                  category === c.value
                    ? "border-blue-500 bg-blue-500/10 text-blue-500"
                    : "bg-slate-100 dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200"
                }`}
              >
                {c.label}
              </button>
            ))}
          </div>
        </div>

        {/* File type (only for project files) */}
        {category === "project" && (
          <div>
            <label className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-2 block">
              檔案類型
            </label>
            <div className="grid grid-cols-2 gap-2">
              {FILE_TYPES.filter((t) => t.value !== "contract").map((ft) => (
                <button
                  key={ft.value}
                  onClick={() => setFileType(ft.value)}
                  className={`min-h-[40px] px-3 py-2 text-xs font-medium rounded-lg border transition-colors cursor-pointer ${
                    fileType === ft.value
                      ? "border-blue-500 bg-blue-500/10 text-blue-500"
                      : "bg-slate-100 dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200"
                  }`}
                >
                  {ft.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Deal association (optional) */}
        {category === "project" && deals.length > 0 && (
          <div>
            <label className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-1 block">
              關聯案件（選填）
            </label>
            <select
              value={dealId ?? ""}
              onChange={(e) => setDealId(e.target.value ? Number(e.target.value) : null)}
              className="w-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-4 py-2.5 text-sm text-slate-900 dark:text-slate-50 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
            >
              <option value="">不關聯</option>
              {deals.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name} ({d.stage})
                </option>
              ))}
            </select>
          </div>
        )}

        {error && <p className="text-xs text-red-400">{error}</p>}

        {/* Upload progress */}
        {uploading && (
          <div className="space-y-1">
            <div className="h-2 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
              <div
                className="h-full bg-blue-500 transition-all duration-300"
                style={{ width: `${(progress / includedFiles.length) * 100}%` }}
              />
            </div>
            <p className="text-xs text-slate-400 text-center">
              {progress} / {includedFiles.length}
            </p>
          </div>
        )}

        <button
          onClick={handleUpload}
          disabled={includedFiles.length === 0 || uploading}
          className="w-full bg-blue-500 hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold px-6 py-3 rounded-lg min-h-[44px] active:scale-[0.98] transition-all cursor-pointer"
        >
          {uploading ? (
            <Loader2 size={20} className="animate-spin mx-auto" />
          ) : (
            `上傳 ${includedFiles.length} 個檔案`
          )}
        </button>
      </div>
    </div>
  );
}
