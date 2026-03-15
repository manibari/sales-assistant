"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { DropZone } from "@/components/drop-zone";
import { DropUploadModal } from "@/components/drop-upload-modal";
import { FileUploadModal } from "@/components/file-upload-modal";
import { DocUploadModal } from "@/components/doc-upload-modal";
import {
  ArrowLeft,
  Loader2,
  Plus,
  Upload,
  FileText,
  FolderOpen,
  ExternalLink,
  CheckCircle,
  Clock,
  AlertTriangle,
  Brain,
  XCircle,
  Search,
} from "lucide-react";
import { KnowledgePanel } from "@/components/knowledge-panel";
import {
  nxApi,
  type NxFile,
  type NxDocument,
  type NxKnowledge,
  type ClientDocDetail,
} from "@/lib/nexus-api";

type Tab = "project" | "contract" | "knowledge";

const FILE_TYPE_LABELS: Record<string, string> = {
  proposal: "提案",
  presentation: "簡報",
  contract: "合約",
  attachment: "附件",
};

const STATUS_LABELS: Record<string, string> = {
  draft: "草稿",
  sent: "已送出",
  signed: "已簽署",
  expired: "已過期",
  terminated: "已終止",
};

function daysUntilExpiry(expiryDate: string | null): number | null {
  if (!expiryDate) return null;
  const diff = new Date(expiryDate).getTime() - Date.now();
  return Math.ceil(diff / (1000 * 60 * 60 * 24));
}

function formatSize(bytes: number | null): string {
  if (!bytes) return "--";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return "--";
  return new Date(dateStr).toLocaleDateString("zh-TW");
}

export default function ClientDocumentsPage() {
  const params = useParams();
  const router = useRouter();
  const clientId = Number(params.clientId);

  const [tab, setTab] = useState<Tab>("project");
  const [data, setData] = useState<ClientDocDetail | null>(null);
  const [clientName, setClientName] = useState("");
  const [loading, setLoading] = useState(true);
  const [droppedFiles, setDroppedFiles] = useState<File[] | null>(null);
  const [showFileUpload, setShowFileUpload] = useState(false);
  const [uploadDocId, setUploadDocId] = useState<number | null>(null);

  const loadData = useCallback(async () => {
    try {
      const [docData, client] = await Promise.all([
        nxApi.documents.byClient(clientId),
        nxApi.clients.get(clientId),
      ]);
      setData(docData);
      setClientName(client.name);
    } catch (err) {
      console.error("Failed to load client documents:", err);
    } finally {
      setLoading(false);
    }
  }, [clientId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleFilesDropped = (files: File[]) => {
    setDroppedFiles(files);
  };

  const uploadDoc =
    uploadDocId !== null
      ? data?.contract_docs.find((d) => d.id === uploadDocId) ?? null
      : null;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 size={24} className="animate-spin text-blue-500" />
      </div>
    );
  }

  const projectFiles = data?.project_files ?? [];
  const contractFiles = data?.contract_files ?? [];
  const contractDocs = data?.contract_docs ?? [];

  return (
    <DropZone onFilesDropped={handleFilesDropped}>
      <div className="flex flex-col h-full">
        <div className="h-14 px-4 flex items-center gap-3 border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
          <button
            onClick={() => router.push("/documents")}
            className="p-1.5 text-slate-400 hover:text-slate-200 cursor-pointer transition-colors"
          >
            <ArrowLeft size={20} />
          </button>
          <h1 className="text-xl font-bold text-slate-900 dark:text-slate-50 truncate">
            {clientName || `公司 #${clientId}`}
          </h1>
        </div>

        <div className="flex-1 px-4 py-4 overflow-auto max-w-2xl lg:max-w-4xl mx-auto w-full space-y-3">
          {/* Tabs */}
          <div className="flex gap-2">
            <button
              onClick={() => setTab("project")}
              className={`flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium border transition-colors cursor-pointer ${
                tab === "project"
                  ? "border-blue-500 bg-blue-500/10 text-blue-500"
                  : "bg-slate-100 dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-500"
              }`}
            >
              <FolderOpen size={16} />
              專案文件
              <span className="text-[11px] opacity-70">({projectFiles.length})</span>
            </button>
            <button
              onClick={() => setTab("contract")}
              className={`flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium border transition-colors cursor-pointer ${
                tab === "contract"
                  ? "border-blue-500 bg-blue-500/10 text-blue-500"
                  : "bg-slate-100 dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-500"
              }`}
            >
              <FileText size={16} />
              合約文件
              <span className="text-[11px] opacity-70">({contractDocs.length})</span>
            </button>
            <button
              onClick={() => setTab("knowledge")}
              className={`flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium border transition-colors cursor-pointer ${
                tab === "knowledge"
                  ? "border-blue-500 bg-blue-500/10 text-blue-500"
                  : "bg-slate-100 dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-500"
              }`}
            >
              <Brain size={16} />
              知識庫
            </button>
          </div>

          {/* Project files tab */}
          {tab === "project" && (
            <div className="space-y-2">
              <div className="flex justify-end">
                <button
                  onClick={() => setShowFileUpload(true)}
                  className="flex items-center gap-1.5 text-xs font-medium px-3 py-2 rounded-lg border border-blue-500/30 text-blue-500 hover:bg-blue-500/10 cursor-pointer transition-colors"
                >
                  <Plus size={14} />
                  新增文件
                </button>
              </div>

              {projectFiles.length === 0 ? (
                <EmptyState message="尚無專案文件，拖拉檔案或點擊新增" />
              ) : (
                projectFiles.map((file) => (
                  <ProjectFileRow key={file.id} file={file} onRenamed={loadData} />
                ))
              )}
            </div>
          )}

          {/* Contract tab */}
          {tab === "contract" && (
            <div className="space-y-2">
              {contractDocs.length === 0 && contractFiles.length === 0 ? (
                <EmptyState message="尚無合約文件" />
              ) : (
                <>
                  {contractDocs.map((doc) => (
                    <ContractDocRow
                      key={`doc-${doc.id}`}
                      doc={doc}
                      onUpload={() => setUploadDocId(doc.id)}
                    />
                  ))}
                  {contractFiles.map((file) => (
                    <ProjectFileRow key={`file-${file.id}`} file={file} onRenamed={loadData} />
                  ))}
                </>
              )}
            </div>
          )}

          {/* Knowledge tab */}
          {tab === "knowledge" && (
            <KnowledgeTab clientId={clientId} />
          )}
        </div>
      </div>

      {/* Drop upload modal */}
      {droppedFiles && (
        <DropUploadModal
          files={droppedFiles}
          clientId={clientId}
          onClose={() => setDroppedFiles(null)}
          onUploaded={() => {
            setDroppedFiles(null);
            loadData();
          }}
        />
      )}

      {/* File upload modal */}
      {showFileUpload && (
        <FileUploadModal
          clientId={clientId}
          onClose={() => setShowFileUpload(false)}
          onUploaded={() => {
            setShowFileUpload(false);
            loadData();
          }}
        />
      )}

      {/* Doc upload modal (contract) */}
      {uploadDocId !== null && uploadDoc && (
        <DocUploadModal
          docId={uploadDocId}
          currentPath={uploadDoc.file_path}
          onClose={() => setUploadDocId(null)}
          onUploaded={() => {
            setUploadDocId(null);
            loadData();
          }}
        />
      )}
    </DropZone>
  );
}

function ParseStatusBadge({
  status,
  onClick,
}: {
  status: string;
  onClick?: () => void;
}) {
  if (status === "skipped" || status === "pending" && !onClick) return null;

  const config: Record<string, { icon: React.ReactNode; label: string; color: string }> = {
    pending: { icon: <Clock size={10} />, label: "待解析", color: "text-slate-400" },
    parsing: { icon: <Loader2 size={10} className="animate-spin" />, label: "解析中", color: "text-blue-500" },
    done: { icon: <Brain size={10} />, label: "知識庫", color: "text-green-500" },
    partial: { icon: <AlertTriangle size={10} />, label: "部分完成", color: "text-amber-500" },
    failed: { icon: <XCircle size={10} />, label: "失敗", color: "text-red-500" },
    empty: { icon: <FileText size={10} />, label: "空檔案", color: "text-slate-400" },
  };

  const c = config[status];
  if (!c) return null;

  const Tag = onClick ? "button" : "span";
  return (
    <Tag
      onClick={onClick}
      className={`inline-flex items-center gap-1 text-[10px] ${c.color} ${onClick ? "cursor-pointer hover:opacity-80" : ""}`}
    >
      {c.icon}
      {c.label}
    </Tag>
  );
}

function ProjectFileRow({ file, onRenamed }: { file: NxFile; onRenamed?: () => void }) {
  const isLink = file.source_url || file.file_path.startsWith("link://");
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState(file.file_name);
  const [saving, setSaving] = useState(false);
  const [showKnowledge, setShowKnowledge] = useState(false);

  const isParseable = /\.(pdf|pptx|docx)$/i.test(file.file_name);
  const canExpand = isParseable && (file.parse_status === "done" || file.parse_status === "partial" || file.parse_status === "failed");

  const handleSave = async () => {
    const trimmed = name.trim();
    if (!trimmed || trimmed === file.file_name) {
      setName(file.file_name);
      setEditing(false);
      return;
    }
    setSaving(true);
    try {
      await nxApi.files.update(file.id, { file_name: trimmed });
      setEditing(false);
      onRenamed?.();
    } catch {
      setName(file.file_name);
      setEditing(false);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl overflow-hidden">
      <div className="p-4">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2 min-w-0 flex-1">
            <FileText size={16} className="text-blue-500 flex-shrink-0" />
            <div className="min-w-0">
              {editing ? (
                <input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  onBlur={handleSave}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") handleSave();
                    if (e.key === "Escape") { setName(file.file_name); setEditing(false); }
                  }}
                  disabled={saving}
                  autoFocus
                  className="text-sm font-medium text-slate-900 dark:text-slate-50 bg-slate-100 dark:bg-slate-800 border border-blue-500 rounded px-2 py-0.5 w-full focus:outline-none"
                />
              ) : (
                <p
                  className="text-sm font-medium text-slate-900 dark:text-slate-50 truncate cursor-pointer hover:text-blue-500 transition-colors"
                  onClick={() => setEditing(true)}
                  title="點擊改名"
                >
                  {file.file_name}
                </p>
              )}
              <div className="flex items-center gap-2 mt-0.5">
                <span className="text-[11px] px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-500">
                  {FILE_TYPE_LABELS[file.file_type] || file.file_type}
                </span>
                {file.deal_name && (
                  <span className="text-[11px] text-slate-400 truncate">
                    {file.deal_name}
                  </span>
                )}
                {isParseable && (
                  <ParseStatusBadge
                    status={file.parse_status}
                    onClick={canExpand ? () => setShowKnowledge(!showKnowledge) : undefined}
                  />
                )}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            <span className="text-[11px] text-slate-400">
              {formatSize(file.file_size)}
            </span>
            <span className="text-[11px] text-slate-400">
              {formatDate(file.created_at)}
            </span>
            {isLink && (
              <a
                href={file.source_url || file.file_path.replace("link://", "")}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-500 hover:text-blue-400"
                onClick={(e) => e.stopPropagation()}
              >
                <ExternalLink size={14} />
              </a>
            )}
          </div>
        </div>
      </div>
      {showKnowledge && (
        <KnowledgePanel
          fileId={file.id}
          parseStatus={file.parse_status}
          onReparsed={onRenamed}
        />
      )}
    </div>
  );
}

function ContractDocRow({
  doc,
  onUpload,
}: {
  doc: NxDocument;
  onUpload: () => void;
}) {
  const days = daysUntilExpiry(doc.expiry_date);
  const isExpired = days !== null && days < 0;
  const isExpiring = days !== null && days >= 0 && days <= 30;

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0 flex-1">
          <FileText
            size={16}
            className={`flex-shrink-0 ${
              isExpired ? "text-red-500" : isExpiring ? "text-amber-500" : "text-blue-500"
            }`}
          />
          <div className="min-w-0">
            <p className="text-sm font-medium text-slate-900 dark:text-slate-50 truncate">
              {doc.doc_type.toUpperCase()}
              {doc.file_path && (
                <span className="text-slate-400 font-normal ml-2">
                  {doc.file_path.split("/").pop()}
                </span>
              )}
            </p>
            <div className="flex items-center gap-2 mt-0.5">
              <span
                className={`text-[11px] px-2 py-0.5 rounded-full ${
                  doc.status === "signed"
                    ? "bg-green-500/10 text-green-400"
                    : "bg-slate-100 dark:bg-slate-800 text-slate-500"
                }`}
              >
                {STATUS_LABELS[doc.status] || doc.status}
              </span>
              {isExpired && (
                <span className="inline-flex items-center gap-1 text-[11px] text-red-400">
                  <AlertTriangle size={10} /> 已過期
                </span>
              )}
              {!isExpired && isExpiring && (
                <span className="inline-flex items-center gap-1 text-[11px] text-amber-500">
                  <Clock size={10} /> {days} 天到期
                </span>
              )}
              {doc.sign_date && (
                <span className="text-[11px] text-slate-400">簽署 {doc.sign_date}</span>
              )}
              {doc.expiry_date && (
                <span className="text-[11px] text-slate-400">到期 {doc.expiry_date}</span>
              )}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <button
            onClick={onUpload}
            className={`flex items-center gap-1 text-xs px-2.5 py-1 rounded-lg border cursor-pointer transition-colors ${
              doc.file_path
                ? "border-green-500/30 text-green-500 hover:bg-green-500/10"
                : "border-blue-500/30 text-blue-500 hover:bg-blue-500/10"
            }`}
          >
            {doc.file_path ? (
              <>
                <CheckCircle size={12} />
                更換
              </>
            ) : (
              <>
                <Upload size={12} />
                上傳
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

function KnowledgeTab({ clientId }: { clientId: number }) {
  const [chunks, setChunks] = useState<NxKnowledge[]>([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [searching, setSearching] = useState(false);
  const [expandedChunk, setExpandedChunk] = useState<number | null>(null);

  useEffect(() => {
    nxApi.knowledge
      .byClient(clientId)
      .then(setChunks)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [clientId]);

  const handleSearch = async () => {
    const q = query.trim();
    if (q.length < 2) {
      // Reload all
      setLoading(true);
      nxApi.knowledge
        .byClient(clientId)
        .then(setChunks)
        .catch(console.error)
        .finally(() => setLoading(false));
      return;
    }
    setSearching(true);
    try {
      const results = await nxApi.knowledge.search(q, clientId);
      setChunks(results);
    } catch (err) {
      console.error("Search failed:", err);
    } finally {
      setSearching(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 size={20} className="animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Search bar */}
      <div className="flex gap-2">
        <div className="flex-1 relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            placeholder="搜尋知識庫..."
            className="w-full pl-8 pr-3 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-50 focus:outline-none focus:border-blue-500"
          />
        </div>
        <button
          onClick={handleSearch}
          disabled={searching}
          className="flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-lg bg-blue-500 text-white hover:bg-blue-600 cursor-pointer transition-colors disabled:opacity-50"
        >
          {searching ? <Loader2 size={14} className="animate-spin" /> : <Search size={14} />}
          搜尋
        </button>
      </div>

      {chunks.length === 0 ? (
        <EmptyState message="尚無知識段落，請先上傳 PDF / PPTX / DOCX 文件" />
      ) : (
        <div className="space-y-1">
          <p className="text-xs text-slate-400">{chunks.length} 段知識</p>
          {chunks.map((chunk) => (
            <div
              key={chunk.id}
              className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg p-3"
            >
              <button
                onClick={() => setExpandedChunk(expandedChunk === chunk.id ? null : chunk.id)}
                className="w-full text-left cursor-pointer"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0 flex-1">
                    <p className="text-xs text-slate-700 dark:text-slate-300 line-clamp-2">
                      {chunk.summary || chunk.content.slice(0, 150)}
                    </p>
                    <div className="flex items-center gap-2 mt-1">
                      {chunk.file_name && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-500">
                          {chunk.file_name}
                        </span>
                      )}
                      {chunk.tags?.map((tag, i) => (
                        <span
                          key={i}
                          className="text-[10px] px-1.5 py-0.5 rounded-full bg-blue-500/10 text-blue-500"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                  {chunk.metadata && (
                    <span className="text-[10px] text-slate-400 flex-shrink-0">
                      {(chunk.metadata as Record<string, unknown>).page_number
                        ? `p.${(chunk.metadata as Record<string, unknown>).page_number}`
                        : (chunk.metadata as Record<string, unknown>).slide_number
                          ? `#${(chunk.metadata as Record<string, unknown>).slide_number}`
                          : ""}
                    </span>
                  )}
                </div>
              </button>
              {expandedChunk === chunk.id && (
                <div className="mt-2 p-3 bg-slate-50 dark:bg-slate-800 rounded-lg text-xs text-slate-600 dark:text-slate-400 whitespace-pre-wrap max-h-60 overflow-auto">
                  {chunk.content}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function EmptyState({ message }: { message: string }) {
  return (
    <div className="text-center py-12 text-slate-400 text-sm">{message}</div>
  );
}
