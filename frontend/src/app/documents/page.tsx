"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import { TopBar } from "@/components/top-bar";
import Link from "next/link";
import {
  FileCheck,
  AlertTriangle,
  Clock,
  Loader2,
  Upload,
  CheckCircle,
  List,
  Building2,
  ChevronDown,
  ChevronRight,
} from "lucide-react";
import { nxApi, type NxDocument } from "@/lib/nexus-api";
import { DocUploadModal } from "@/components/doc-upload-modal";

type DocWithClient = NxDocument & { client_name?: string };

type ViewMode = "flat" | "grouped";

function daysUntilExpiry(expiryDate: string | null): number | null {
  if (!expiryDate) return null;
  const diff = new Date(expiryDate).getTime() - Date.now();
  return Math.ceil(diff / (1000 * 60 * 60 * 24));
}

function ExpiryBadge({ days }: { days: number | null }) {
  if (days === null) return <span className="text-xs text-slate-400">--</span>;
  if (days < 0)
    return (
      <span className="inline-flex items-center gap-1 text-xs font-medium text-red-500 bg-red-50 dark:bg-red-900/20 px-2 py-0.5 rounded-full">
        <AlertTriangle size={12} /> 已過期
      </span>
    );
  if (days <= 30)
    return (
      <span className="inline-flex items-center gap-1 text-xs font-medium text-amber-600 bg-amber-50 dark:bg-amber-900/20 px-2 py-0.5 rounded-full">
        <Clock size={12} /> {days} 天後到期
      </span>
    );
  return (
    <span className="text-xs text-green-600 dark:text-green-400">
      {days} 天後到期
    </span>
  );
}

const STATUS_LABELS: Record<string, string> = {
  draft: "草稿",
  sent: "已送出",
  signed: "已簽署",
  expired: "已過期",
  terminated: "已終止",
};

interface ClientGroup {
  clientId: number;
  clientName: string;
  docs: DocWithClient[];
  hasNda: boolean;
  hasMou: boolean;
  ndaSigned: boolean;
  mouSigned: boolean;
  hasExpiring: boolean;
  hasExpired: boolean;
}

function buildClientGroups(docs: DocWithClient[]): ClientGroup[] {
  const map = new Map<number, DocWithClient[]>();
  for (const doc of docs) {
    const list = map.get(doc.client_id) || [];
    list.push(doc);
    map.set(doc.client_id, list);
  }
  const groups: ClientGroup[] = [];
  for (const [clientId, clientDocs] of map) {
    const ndaDocs = clientDocs.filter((d) => d.doc_type === "nda");
    const mouDocs = clientDocs.filter((d) => d.doc_type === "mou");
    const hasExpiring = clientDocs.some((d) => {
      const days = daysUntilExpiry(d.expiry_date);
      return days !== null && days >= 0 && days <= 30;
    });
    const hasExpired = clientDocs.some((d) => {
      const days = daysUntilExpiry(d.expiry_date);
      return days !== null && days < 0;
    });
    groups.push({
      clientId,
      clientName: clientDocs[0].client_name || `客戶 #${clientId}`,
      docs: clientDocs,
      hasNda: ndaDocs.length > 0,
      hasMou: mouDocs.length > 0,
      ndaSigned: ndaDocs.some((d) => d.status === "signed"),
      mouSigned: mouDocs.some((d) => d.status === "signed"),
      hasExpiring,
      hasExpired,
    });
  }
  // Sort: problems first (expired > expiring > normal), then alphabetical
  groups.sort((a, b) => {
    if (a.hasExpired !== b.hasExpired) return a.hasExpired ? -1 : 1;
    if (a.hasExpiring !== b.hasExpiring) return a.hasExpiring ? -1 : 1;
    return a.clientName.localeCompare(b.clientName);
  });
  return groups;
}

function DocStatusChip({ label, signed, exists }: { label: string; signed: boolean; exists: boolean }) {
  if (!exists)
    return (
      <span className="text-[11px] px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-400">
        {label} ✗
      </span>
    );
  if (signed)
    return (
      <span className="text-[11px] px-2 py-0.5 rounded-full bg-green-500/10 text-green-400">
        {label} ✓
      </span>
    );
  return (
    <span className="text-[11px] px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-500">
      {label} …
    </span>
  );
}

export default function DocumentsPage() {
  const [docs, setDocs] = useState<DocWithClient[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploadDocId, setUploadDocId] = useState<number | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>("grouped");
  const [collapsed, setCollapsed] = useState<Set<number>>(new Set());

  const loadDocs = useCallback(async () => {
    try {
      const all = await nxApi.documents.listAll();
      setDocs(all);
    } catch (err) {
      console.error("Failed to load documents:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDocs();
  }, [loadDocs]);

  const groups = useMemo(() => buildClientGroups(docs), [docs]);

  const toggleCollapse = (clientId: number) => {
    setCollapsed((prev) => {
      const next = new Set(prev);
      if (next.has(clientId)) next.delete(clientId);
      else next.add(clientId);
      return next;
    });
  };

  const uploadDoc = uploadDocId !== null ? docs.find((d) => d.id === uploadDocId) : null;

  const signedCount = docs.filter((d) => d.status === "signed").length;
  const warningCount = docs.filter((d) => {
    const days = daysUntilExpiry(d.expiry_date);
    return days !== null && days <= 30;
  }).length;
  const missingClients = groups.filter((g) => !g.ndaSigned && !g.mouSigned).length;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 size={24} className="animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <TopBar title="文件追蹤" />

      <div className="flex-1 px-4 py-4 overflow-auto max-w-2xl lg:max-w-4xl mx-auto w-full space-y-3">
        {/* Summary */}
        <div className="grid grid-cols-4 gap-3">
          <SummaryCard label="全部" value={docs.length} color="text-slate-700 dark:text-slate-200" />
          <SummaryCard label="已簽署" value={signedCount} color="text-green-600 dark:text-green-400" />
          <SummaryCard label="需注意" value={warningCount} color="text-amber-600 dark:text-amber-400" />
          <SummaryCard label="缺件客戶" value={missingClients} color="text-red-600 dark:text-red-400" />
        </div>

        {/* View toggle */}
        <div className="flex items-center justify-end gap-1">
          <button
            onClick={() => setViewMode("flat")}
            className={`p-1.5 rounded-lg cursor-pointer transition-colors ${
              viewMode === "flat"
                ? "bg-blue-500/10 text-blue-500"
                : "text-slate-400 hover:text-slate-300"
            }`}
            title="全部列表"
          >
            <List size={16} />
          </button>
          <button
            onClick={() => setViewMode("grouped")}
            className={`p-1.5 rounded-lg cursor-pointer transition-colors ${
              viewMode === "grouped"
                ? "bg-blue-500/10 text-blue-500"
                : "text-slate-400 hover:text-slate-300"
            }`}
            title="按客戶分組"
          >
            <Building2 size={16} />
          </button>
        </div>

        {/* Document list */}
        {docs.length === 0 ? (
          <div className="text-center py-12 text-slate-400 text-sm">
            尚無 NDA/MOU 文件
          </div>
        ) : viewMode === "flat" ? (
          <div className="space-y-2">
            {docs.map((doc) => (
              <DocRow key={doc.id} doc={doc} onUpload={() => setUploadDocId(doc.id)} />
            ))}
          </div>
        ) : (
          <div className="space-y-2">
            {groups.map((group) => {
              const isCollapsed = collapsed.has(group.clientId);
              return (
                <div
                  key={group.clientId}
                  className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl overflow-hidden"
                >
                  {/* Group header */}
                  <button
                    onClick={() => toggleCollapse(group.clientId)}
                    className="w-full flex items-center justify-between px-4 py-3 hover:bg-slate-50 dark:hover:bg-slate-800/50 cursor-pointer transition-colors"
                  >
                    <div className="flex items-center gap-2">
                      {isCollapsed ? (
                        <ChevronRight size={16} className="text-slate-400 flex-shrink-0" />
                      ) : (
                        <ChevronDown size={16} className="text-slate-400 flex-shrink-0" />
                      )}
                      <Link
                        href={`/contacts/clients/${group.clientId}`}
                        onClick={(e) => e.stopPropagation()}
                        className="text-sm font-semibold text-slate-900 dark:text-slate-50 hover:text-blue-500 transition-colors"
                      >
                        {group.clientName}
                      </Link>
                      <span className="text-xs text-slate-400">({group.docs.length})</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <DocStatusChip label="NDA" exists={group.hasNda} signed={group.ndaSigned} />
                      <DocStatusChip label="MOU" exists={group.hasMou} signed={group.mouSigned} />
                      {group.hasExpired && (
                        <span className="text-[11px] px-2 py-0.5 rounded-full bg-red-500/10 text-red-400 font-medium">
                          已過期
                        </span>
                      )}
                      {!group.hasExpired && group.hasExpiring && (
                        <span className="text-[11px] px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-500 font-medium">
                          即將到期
                        </span>
                      )}
                    </div>
                  </button>

                  {/* Group body */}
                  {!isCollapsed && (
                    <div className="border-t border-slate-100 dark:border-slate-800 divide-y divide-slate-100 dark:divide-slate-800">
                      {group.docs.map((doc) => (
                        <DocRow key={doc.id} doc={doc} onUpload={() => setUploadDocId(doc.id)} compact />
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Upload modal */}
      {uploadDocId !== null && uploadDoc && (
        <DocUploadModal
          docId={uploadDocId}
          currentPath={uploadDoc.file_path}
          onClose={() => setUploadDocId(null)}
          onUploaded={() => {
            setUploadDocId(null);
            loadDocs();
          }}
        />
      )}
    </div>
  );
}

function DocRow({
  doc,
  onUpload,
  compact,
}: {
  doc: DocWithClient;
  onUpload: () => void;
  compact?: boolean;
}) {
  const days = daysUntilExpiry(doc.expiry_date);
  return (
    <div className={compact ? "px-4 py-3" : "bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4"}>
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <FileCheck size={16} className="text-blue-500 flex-shrink-0 mt-0.5" />
          <div>
            {!compact && (
              <p className="text-sm font-medium text-slate-900 dark:text-slate-50">
                {doc.client_name || `客戶 #${doc.client_id}`}
              </p>
            )}
            <p className={`text-xs text-slate-500 ${compact ? "" : "mt-0.5"}`}>
              {doc.doc_type.toUpperCase()} · {STATUS_LABELS[doc.status] || doc.status}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <ExpiryBadge days={days} />
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
      <div className="mt-2 flex gap-4 text-xs text-slate-400">
        {doc.sign_date && <span>簽署: {doc.sign_date}</span>}
        {doc.expiry_date && <span>到期: {doc.expiry_date}</span>}
        {doc.file_path && (
          <span className="text-green-500 flex items-center gap-1">
            <CheckCircle size={10} />
            {doc.file_path.split("/").pop()}
          </span>
        )}
      </div>
    </div>
  );
}

function SummaryCard({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color: string;
}) {
  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-3 text-center">
      <p className={`text-xl font-bold ${color}`}>{value}</p>
      <p className="text-xs text-slate-500 mt-0.5">{label}</p>
    </div>
  );
}
