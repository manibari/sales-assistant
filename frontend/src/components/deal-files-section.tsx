"use client";

import { useState } from "react";
import { Check, Download, ExternalLink, FileCheck, Pencil, X } from "lucide-react";
import { nxApi, type NxDeal } from "@/lib/nexus-api";
import { FileUploadModal } from "@/components/file-upload-modal";

interface DealFilesSectionProps {
  deal: NxDeal;
  dealId: number;
  isClosed: boolean;
  onUpdated: () => void;
}

export function DealFilesSection({ deal, dealId, isClosed, onUpdated }: DealFilesSectionProps) {
  const [showFileUpload, setShowFileUpload] = useState(false);
  const [editingFileId, setEditingFileId] = useState<number | null>(null);
  const [editingFileName, setEditingFileName] = useState("");

  return (
    <>
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <FileCheck size={16} className="text-blue-500" />
            <span className="text-sm font-semibold text-slate-900 dark:text-slate-50">文件</span>
            <span className="text-xs text-slate-400">({deal.files?.length || 0})</span>
          </div>
          {!isClosed && (
            <button onClick={() => setShowFileUpload(true)} className="text-xs text-blue-500 cursor-pointer">
              + 新增
            </button>
          )}
        </div>

        <div className="divide-y divide-slate-100 dark:divide-slate-800">
          {deal.files && deal.files.length > 0 ? (
            deal.files.map((f) => {
              const isExternal = !!f.source_url;
              const isLocal = !isExternal && f.file_path && !f.file_path.startsWith("link://");
              const statusBadge =
                f.parse_status === "parsed"
                  ? { label: "已解析", cls: "bg-green-500/10 text-green-400" }
                  : f.parse_status === "failed"
                    ? { label: "解析失敗", cls: "bg-red-500/10 text-red-400" }
                    : isExternal
                      ? { label: "外部連結", cls: "bg-blue-500/10 text-blue-400" }
                      : { label: "已上傳", cls: "bg-slate-500/10 text-slate-400" };
              const href = isExternal ? f.source_url! : `/api/nx/documents/files/${f.id}/download`;

              return (
                <div key={f.id} className="flex items-center justify-between py-2">
                  <div className="flex-1 min-w-0">
                    {editingFileId === f.id ? (
                      <div className="flex items-center gap-1.5">
                        <input
                          type="text"
                          value={editingFileName}
                          onChange={(e) => setEditingFileName(e.target.value)}
                          onKeyDown={async (e) => {
                            if (e.key === "Enter") {
                              await nxApi.files.update(f.id, { file_name: editingFileName });
                              setEditingFileId(null);
                              onUpdated();
                            }
                            if (e.key === "Escape") setEditingFileId(null);
                          }}
                          className="flex-1 bg-slate-100 dark:bg-slate-800 border border-blue-500 rounded px-2 py-0.5 text-sm text-slate-900 dark:text-slate-50 focus:outline-none"
                          autoFocus
                        />
                        <button
                          onClick={async () => {
                            await nxApi.files.update(f.id, { file_name: editingFileName });
                            setEditingFileId(null);
                            onUpdated();
                          }}
                          className="p-1 bg-blue-500 text-white rounded cursor-pointer"
                        >
                          <Check size={12} />
                        </button>
                        <button onClick={() => setEditingFileId(null)} className="p-1 bg-slate-200 dark:bg-slate-700 rounded cursor-pointer">
                          <X size={12} />
                        </button>
                      </div>
                    ) : (
                      <div className="flex items-center gap-1.5">
                        <a
                          href={href}
                          target={isExternal ? "_blank" : "_self"}
                          rel={isExternal ? "noopener noreferrer" : undefined}
                          className="text-sm text-blue-500 hover:text-blue-400 hover:underline truncate flex items-center gap-1"
                        >
                          {f.file_name}
                          {isExternal ? <ExternalLink size={12} /> : isLocal ? <Download size={12} /> : null}
                        </a>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setEditingFileId(f.id);
                            setEditingFileName(f.file_name);
                          }}
                          className="p-0.5 text-slate-400 hover:text-blue-500 cursor-pointer"
                          title="編輯名稱"
                        >
                          <Pencil size={11} />
                        </button>
                      </div>
                    )}
                    {f.source_url && (
                      <span className="text-[11px] text-slate-400 truncate block">{f.source_url.slice(0, 40)}...</span>
                    )}
                  </div>
                  <div className="flex items-center gap-2 ml-2">
                    <span className="text-[11px] px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400">
                      {f.file_type === "proposal" ? "簡報" : f.file_type === "contract" ? "合約" : "附件"}
                    </span>
                    <span className={`text-[11px] px-2 py-0.5 rounded-full ${statusBadge.cls}`}>{statusBadge.label}</span>
                  </div>
                </div>
              );
            })
          ) : (
            <p className="text-xs text-slate-400 py-2">尚無文件</p>
          )}
        </div>
      </div>

      {showFileUpload && (
        <FileUploadModal dealId={dealId} onClose={() => setShowFileUpload(false)} onUploaded={onUpdated} />
      )}
    </>
  );
}
