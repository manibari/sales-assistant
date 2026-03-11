"use client";

import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { TopBar } from "@/components/top-bar";
import {
  Camera,
  Type,
  Paperclip,
  ArrowRight,
  Loader2,
  X,
  FileText,
  Link2,
} from "lucide-react";
import { nxApi } from "@/lib/nexus-api";

interface PendingFile {
  mode: "file" | "link";
  name: string;
  file?: File;
  url?: string;
  fileType: string;
}

export default function CapturePage() {
  const router = useRouter();
  const [inputText, setInputText] = useState("");
  const [loading, setLoading] = useState(false);
  const [pendingFiles, setPendingFiles] = useState<PendingFile[]>([]);
  const [showFilePanel, setShowFilePanel] = useState(false);
  const [linkUrl, setLinkUrl] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleAddFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setPendingFiles((prev) => [
      ...prev,
      { mode: "file", name: file.name, file, fileType: "attachment" },
    ]);
    setShowFilePanel(false);
    // Reset input so same file can be re-selected
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleAddLink = () => {
    if (!linkUrl.trim()) return;
    const fileName = linkUrl.includes("drive.google.com")
      ? "Google Drive 文件"
      : linkUrl.split("/").pop() || "連結文件";
    setPendingFiles((prev) => [
      ...prev,
      { mode: "link", name: fileName, url: linkUrl.trim(), fileType: "attachment" },
    ]);
    setLinkUrl("");
    setShowFilePanel(false);
  };

  const removeFile = (index: number) => {
    setPendingFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async () => {
    if (!inputText.trim()) return;
    setLoading(true);
    try {
      const intel = await nxApi.intel.create({
        raw_input: inputText.trim(),
        input_type: "text",
      });

      // Attach files to intel
      for (const pf of pendingFiles) {
        const body: Record<string, unknown> = {
          intel_id: intel.id,
          file_type: pf.fileType,
          file_name: pf.name,
          file_path:
            pf.mode === "link"
              ? `link://${pf.url}`
              : `/uploads/${pf.name}`,
        };
        if (pf.mode === "link") {
          body.source_url = pf.url;
        } else if (pf.file) {
          body.file_size = pf.file.size;
        }
        await fetch("/api/nx/documents/files", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });
      }

      // Navigate to Q&A flow with intel ID
      router.push(`/capture/qa?id=${intel.id}`);
    } catch (err) {
      console.error("Failed to create intel:", err);
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <TopBar title="新增情報" />
      <div className="flex-1 px-4 py-6 flex flex-col gap-6 max-w-2xl mx-auto w-full">
        {/* Input method tabs */}
        <div className="flex gap-2">
          <button className="flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-400 dark:text-slate-500 cursor-not-allowed min-h-[44px]">
            <Camera size={20} strokeWidth={1.5} />
            <span className="text-sm font-medium">拍照</span>
          </button>
          <button className="flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg bg-blue-500/10 border border-blue-500 text-blue-500 dark:text-blue-400 min-h-[44px] cursor-pointer">
            <Type size={20} strokeWidth={1.5} />
            <span className="text-sm font-medium">文字輸入</span>
          </button>
        </div>

        {/* Text input area */}
        <div className="flex-1 flex flex-col gap-3">
          <label className="text-xs font-medium text-slate-500 dark:text-slate-400">
            會議記錄 / 名片資訊 / 任何情報
          </label>
          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="貼上會議記錄、語音轉文字、名片資訊...&#10;&#10;例如：「今天去 A 食品拜訪陳副廠長，他提到今年重點是產線自動化，預算約 300K，希望先做 AOI。NDA 已簽。」"
            className="flex-1 min-h-[200px] w-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-4 py-3 text-base text-slate-900 dark:text-slate-50 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none transition-colors duration-200 resize-none"
          />
          <p className="text-[11px] text-slate-400 dark:text-slate-500">
            AI 會自動解析人物、組織、痛點、時程等資訊
          </p>
        </div>

        {/* Attached files list */}
        {pendingFiles.length > 0 && (
          <div className="flex flex-col gap-2">
            <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
              附件 ({pendingFiles.length})
            </span>
            {pendingFiles.map((pf, idx) => (
              <div
                key={idx}
                className="flex items-center gap-3 px-3 py-2 bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg"
              >
                {pf.mode === "link" ? (
                  <Link2 size={16} className="text-blue-500 shrink-0" />
                ) : (
                  <FileText size={16} className="text-slate-400 shrink-0" />
                )}
                <span className="text-sm text-slate-700 dark:text-slate-200 truncate flex-1">
                  {pf.name}
                </span>
                <button
                  onClick={() => removeFile(idx)}
                  className="p-1 text-slate-400 hover:text-red-400 cursor-pointer transition-colors"
                >
                  <X size={14} />
                </button>
              </div>
            ))}
          </div>
        )}

        {/* File panel (expandable) */}
        {showFilePanel && (
          <div className="bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 rounded-xl p-4 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-slate-700 dark:text-slate-200">
                新增附件
              </span>
              <button
                onClick={() => setShowFilePanel(false)}
                className="p-1 text-slate-400 hover:text-slate-200 cursor-pointer transition-colors"
              >
                <X size={16} />
              </button>
            </div>

            {/* Link input */}
            <div className="flex gap-2">
              <input
                type="url"
                value={linkUrl}
                onChange={(e) => setLinkUrl(e.target.value)}
                placeholder="貼上 Google Drive 或其他連結..."
                className="flex-1 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-900 dark:text-slate-50 placeholder:text-slate-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
                onKeyDown={(e) => e.key === "Enter" && handleAddLink()}
              />
              <button
                onClick={handleAddLink}
                disabled={!linkUrl.trim()}
                className="px-3 py-2 bg-blue-500 hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-medium rounded-lg cursor-pointer transition-colors"
              >
                <Link2 size={16} />
              </button>
            </div>

            {/* Divider */}
            <div className="flex items-center gap-3">
              <div className="flex-1 h-px bg-slate-200 dark:bg-slate-700" />
              <span className="text-[11px] text-slate-400">或</span>
              <div className="flex-1 h-px bg-slate-200 dark:bg-slate-700" />
            </div>

            {/* File picker */}
            <label className="flex items-center justify-center gap-2 p-4 border-2 border-dashed border-slate-300 dark:border-slate-700 rounded-xl cursor-pointer hover:border-blue-500 transition-colors">
              <FileText size={20} className="text-slate-400" />
              <span className="text-sm text-slate-400">
                從裝置選擇檔案
              </span>
              <span className="text-[11px] text-slate-500">
                PDF, PPT, DOCX
              </span>
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.ppt,.pptx,.docx,.doc,.xlsx,.xls,.jpg,.jpeg,.png"
                onChange={handleAddFile}
                className="hidden"
              />
            </label>
          </div>
        )}

        {/* Add file button */}
        {!showFilePanel && (
          <button
            onClick={() => setShowFilePanel(true)}
            className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg border border-dashed border-slate-300 dark:border-slate-700 text-slate-400 dark:text-slate-500 hover:border-blue-500 hover:text-blue-500 dark:hover:text-blue-400 transition-colors cursor-pointer"
          >
            <Paperclip size={16} strokeWidth={1.5} />
            <span className="text-sm font-medium">附加文件</span>
          </button>
        )}

        {/* Submit button */}
        <button
          onClick={handleSubmit}
          disabled={!inputText.trim() || loading}
          className="w-full flex items-center justify-center gap-2 bg-blue-500 hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold px-6 py-3 rounded-lg min-h-[44px] active:scale-[0.98] transition-all duration-200 cursor-pointer"
        >
          {loading ? (
            <Loader2 size={20} className="animate-spin" />
          ) : (
            <>
              <span>送出情報</span>
              {pendingFiles.length > 0 && (
                <span className="bg-white/20 text-xs px-1.5 py-0.5 rounded">
                  +{pendingFiles.length} 檔案
                </span>
              )}
              <ArrowRight size={20} strokeWidth={1.5} />
            </>
          )}
        </button>
      </div>
    </div>
  );
}
