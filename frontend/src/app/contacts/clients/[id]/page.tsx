"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { TopBar } from "@/components/top-bar";
import { ContactFormModal } from "@/components/contact-form-modal";
import { DocUploadModal } from "@/components/doc-upload-modal";
import { getIntelDisplayTitle } from "@/lib/intel-display";
import { formatBudget } from "@/lib/options";
import {
  ChevronLeft,
  Building2,
  Check,
  X,
  Loader2,
  Users,
  Briefcase,
  FileText,
  Pencil,
  Upload,
  Zap,
  Trash2,
} from "lucide-react";
import {
  nxApi,
  type NxClient,
  type NxContact,
  type NxDeal,
  type NxDocument,
  type IntelEntity,
  type NxIntel,
} from "@/lib/nexus-api";

const STAGE_LABELS: Record<string, string> = {
  L0: "L0 潛在",
  L1: "L1 接觸中",
  L2: "L2 需求確認",
  L3: "L3 報價",
  L4: "L4 簽約",
  closed: "已關閉",
};

const DOC_STATUS_COLORS: Record<string, string> = {
  draft: "bg-amber-500/10 text-amber-400",
  active: "bg-green-500/10 text-green-400",
  expired: "bg-red-500/10 text-red-400",
};

export default function ClientDetailPage() {
  const params = useParams();
  const router = useRouter();
  const clientId = Number(params.id);

  const [client, setClient] = useState<NxClient | null>(null);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [contacts, setContacts] = useState<NxContact[]>([]);
  const [deals, setDeals] = useState<NxDeal[]>([]);
  const [linkedIntel, setLinkedIntel] = useState<NxIntel[]>([]);
  const [loading, setLoading] = useState(true);
  const [showContactModal, setShowContactModal] = useState(false);
  const [editContact, setEditContact] = useState<NxContact | null>(null);
  const [editField, setEditField] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");
  const [saving, setSaving] = useState(false);
  const [notesValue, setNotesValue] = useState("");
  const [editingNotes, setEditingNotes] = useState(false);
  const [uploadDoc, setUploadDoc] = useState<NxDocument | null>(null);
  const [showNewDeal, setShowNewDeal] = useState(false);
  const [newDealName, setNewDealName] = useState("");
  const [creatingDeal, setCreatingDeal] = useState(false);

  const loadData = useCallback(() => {
    Promise.all([
      nxApi.clients.get(clientId),
      nxApi.contacts.list("client", clientId),
      nxApi.deals.listByClient(clientId),
      nxApi.intel.byEntity("client", clientId),
    ])
      .then(([c, ct, d, intels]) => {
        setClient(c);
        setContacts(ct);
        setDeals(d);
        setLinkedIntel(intels);
        setNotesValue(c.notes || "");
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [clientId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const startEdit = (field: string, currentValue: string) => {
    setEditField(field);
    setEditValue(currentValue || "");
  };

  const cancelEdit = () => {
    setEditField(null);
    setEditValue("");
  };

  const saveField = async () => {
    if (!editField || !client) return;
    setSaving(true);
    try {
      await nxApi.clients.update(clientId, { [editField]: editValue } as Partial<NxClient>);
      cancelEdit();
      loadData();
    } catch (err) {
      console.error("Failed to save:", err);
    } finally {
      setSaving(false);
    }
  };

  const saveNotes = async () => {
    setSaving(true);
    try {
      await nxApi.clients.update(clientId, { notes: notesValue } as Partial<NxClient>);
      setEditingNotes(false);
      loadData();
    } catch (err) {
      console.error("Failed to save notes:", err);
    } finally {
      setSaving(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") saveField();
    if (e.key === "Escape") cancelEdit();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 size={24} className="animate-spin text-blue-500" />
      </div>
    );
  }

  if (!client) {
    return (
      <div className="flex flex-col h-full">
        <TopBar title="客戶詳情" />
        <div className="flex-1 flex items-center justify-center text-slate-500">找不到此客戶</div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <TopBar title={client.name}>
        <Link
          href="/contacts"
          className="p-2 rounded-lg text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer transition-colors"
        >
          <ChevronLeft size={20} />
        </Link>
      </TopBar>

      <div className="flex-1 px-4 lg:px-6 py-4 overflow-auto max-w-2xl lg:max-w-6xl mx-auto w-full">
        <div className="lg:grid lg:grid-cols-5 lg:gap-6 space-y-4 lg:space-y-0">
          {/* Left column (3/5) */}
          <div className="lg:col-span-3 space-y-4">
            {/* Header card */}
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-5">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center flex-shrink-0">
                  <Building2 size={20} className="text-blue-500" />
                </div>
                <div className="flex-1 min-w-0">
                  <span
                    className={`text-xs px-2.5 py-1 rounded-full font-medium ${
                      client.status === "active"
                        ? "bg-green-500/10 text-green-400"
                        : "bg-slate-700 text-slate-400"
                    }`}
                  >
                    {client.status === "active" ? "活躍" : client.status}
                  </span>
                </div>
              </div>

              {/* Editable name */}
              {editField === "name" ? (
                <div className="flex items-center gap-2 mt-1">
                  <input
                    type="text"
                    value={editValue}
                    onChange={(e) => setEditValue(e.target.value)}
                    onKeyDown={handleKeyDown}
                    className="flex-1 bg-slate-100 dark:bg-slate-800 border border-blue-500 rounded-lg px-3 py-1.5 text-lg font-semibold text-slate-900 dark:text-slate-50 focus:ring-1 focus:ring-blue-500 focus:outline-none"
                    autoFocus
                  />
                  <button onClick={saveField} disabled={saving} className="p-1.5 bg-blue-500 text-white rounded-lg cursor-pointer disabled:opacity-50"><Check size={16} /></button>
                  <button onClick={cancelEdit} className="p-1.5 bg-slate-200 dark:bg-slate-700 rounded-lg cursor-pointer"><X size={16} /></button>
                </div>
              ) : (
                <h2
                  onClick={() => startEdit("name", client.name)}
                  className="text-lg font-semibold text-slate-900 dark:text-slate-50 cursor-pointer hover:text-blue-500 transition-colors"
                  title="Click to edit name"
                >
                  {client.name}
                </h2>
              )}

              <div className="flex gap-4 mt-3 text-xs text-slate-400 dark:text-slate-500">
                <span
                  onClick={() => startEdit("industry", client.industry || "")}
                  className="cursor-pointer hover:text-blue-500 transition-colors"
                  title="Click to edit industry"
                >
                  產業: {client.industry || "—"}
                </span>
                <span>預算: {formatBudget(client.deal_budget_total)}</span>
              </div>
            </div>

            {/* NDA/MOU Documents */}
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-3">
                <FileText size={16} className="text-blue-500" />
                <span className="text-sm font-semibold text-slate-900 dark:text-slate-50">
                  NDA / MOU
                </span>
                <span className="text-xs text-slate-400">
                  ({client.documents?.length || 0})
                </span>
              </div>
              <div className="divide-y divide-slate-100 dark:divide-slate-800">
                {client.documents && client.documents.length > 0 ? (
                  client.documents.map((doc: NxDocument) => (
                    <div key={doc.id} className="flex items-center justify-between py-2">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-sm text-slate-700 dark:text-slate-300">
                            {doc.doc_type === "nda" ? "NDA" : doc.doc_type === "mou" ? "MOU" : doc.doc_type.toUpperCase()}
                          </span>
                          {doc.file_path && (
                            <Check size={14} className="text-green-400 flex-shrink-0" />
                          )}
                        </div>
                        <div className="text-[11px] text-slate-400 mt-0.5">
                          {doc.sign_date && <span>簽約 {doc.sign_date}</span>}
                          {doc.expiry_date && <span className="ml-2">到期 {doc.expiry_date}</span>}
                          {doc.file_path && (
                            <span className="ml-2 text-green-400/70 truncate max-w-[200px] inline-block align-bottom">
                              {doc.file_path.split("/").pop()}
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-2 flex-shrink-0 ml-2">
                        <button
                          onClick={() => setUploadDoc(doc)}
                          className="text-[11px] px-2 py-1 rounded-lg bg-blue-500/10 text-blue-400 hover:bg-blue-500/20 cursor-pointer transition-colors flex items-center gap-1"
                        >
                          <Upload size={12} />
                          {doc.file_path ? "更換" : "上傳"}
                        </button>
                        <span
                          className={`text-[11px] px-2 py-0.5 rounded-full font-medium ${
                            DOC_STATUS_COLORS[doc.status] || "bg-slate-700 text-slate-400"
                          }`}
                        >
                          {doc.status === "draft" ? "草稿" : doc.status === "active" ? "生效中" : doc.status === "expired" ? "已到期" : doc.status}
                        </span>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-slate-400 py-2">尚無 NDA/MOU</p>
                )}
              </div>
            </div>

            {/* Notes */}
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4">
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-semibold text-slate-900 dark:text-slate-50">
                  備註
                </span>
                {!editingNotes && (
                  <button
                    onClick={() => setEditingNotes(true)}
                    className="text-xs text-blue-500 cursor-pointer flex items-center gap-1"
                  >
                    <Pencil size={12} /> 編輯
                  </button>
                )}
              </div>
              {editingNotes ? (
                <div className="space-y-2">
                  <textarea
                    value={notesValue}
                    onChange={(e) => setNotesValue(e.target.value)}
                    className="w-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-4 py-3 text-sm text-slate-900 dark:text-slate-50 placeholder:text-slate-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none resize-none h-24"
                    placeholder="備註..."
                    autoFocus
                  />
                  <div className="flex gap-2 justify-end">
                    <button
                      onClick={() => {
                        setEditingNotes(false);
                        setNotesValue(client.notes || "");
                      }}
                      className="px-3 py-1.5 text-xs bg-slate-200 dark:bg-slate-700 rounded-lg cursor-pointer"
                    >
                      取消
                    </button>
                    <button
                      onClick={saveNotes}
                      disabled={saving}
                      className="px-3 py-1.5 text-xs bg-blue-500 text-white rounded-lg cursor-pointer disabled:opacity-50"
                    >
                      儲存
                    </button>
                  </div>
                </div>
              ) : (
                <p className="text-sm text-slate-600 dark:text-slate-400 whitespace-pre-wrap">
                  {client.notes || "尚無備註"}
                </p>
              )}
            </div>

            {/* Delete */}
            <div className="pt-2">
              {!confirmDelete ? (
                <button
                  onClick={() => setConfirmDelete(true)}
                  className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-red-400 cursor-pointer transition-colors"
                >
                  <Trash2 size={14} />
                  刪除此客戶
                </button>
              ) : (
                <div className="flex items-center gap-2 bg-red-500/5 border border-red-500/20 rounded-lg p-3">
                  <span className="text-xs text-red-400 flex-1">確定刪除？相關案件與聯絡人不會被刪除。</span>
                  <button
                    onClick={async () => {
                      await nxApi.clients.delete(clientId);
                      router.push("/contacts");
                    }}
                    className="px-3 py-1.5 text-xs bg-red-500 text-white rounded-lg cursor-pointer font-medium"
                  >
                    確認刪除
                  </button>
                  <button
                    onClick={() => setConfirmDelete(false)}
                    className="px-3 py-1.5 text-xs bg-slate-200 dark:bg-slate-700 rounded-lg cursor-pointer"
                  >
                    取消
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Right column (2/5) */}
          <div className="lg:col-span-2 space-y-4">
            {/* Contacts */}
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Users size={16} className="text-violet-500" />
                  <span className="text-sm font-semibold text-slate-900 dark:text-slate-50">
                    聯絡人
                  </span>
                  <span className="text-xs text-slate-400">({contacts.length})</span>
                </div>
                <button
                  onClick={() => setShowContactModal(true)}
                  className="text-xs text-blue-500 cursor-pointer"
                >
                  + 新增
                </button>
              </div>
              <div className="divide-y divide-slate-100 dark:divide-slate-800">
                {contacts.length > 0 ? (
                  contacts.map((c) => (
                    <div
                      key={c.id}
                      onClick={() => setEditContact(c)}
                      className="py-2 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800/50 -mx-1 px-1 rounded transition-colors"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-slate-900 dark:text-slate-50">
                          {c.name}
                        </span>
                        <div className="flex items-center gap-1.5">
                          {c.role && (
                            <span className="text-[11px] px-2 py-0.5 rounded-full bg-violet-500/10 text-violet-400">
                              {c.role}
                            </span>
                          )}
                          <Pencil size={12} className="text-slate-400" />
                        </div>
                      </div>
                      <div className="text-[11px] text-slate-400 mt-0.5 space-x-2">
                        {c.title && <span>{c.title}</span>}
                        {c.phone && <span>{c.phone}</span>}
                        {c.email && <span>{c.email}</span>}
                        {c.line_id && <span>LINE: {c.line_id}</span>}
                      </div>
                      {c.updated_at && (
                        <div className="text-[10px] text-slate-400/60 mt-0.5">
                          最後更新：{new Date(c.updated_at).toLocaleDateString("zh-TW")}
                        </div>
                      )}
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-slate-400 py-2">尚無聯絡人</p>
                )}
              </div>
            </div>

            {/* Related Deals */}
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Briefcase size={16} className="text-blue-500" />
                  <span className="text-sm font-semibold text-slate-900 dark:text-slate-50">
                    相關商機
                  </span>
                  <span className="text-xs text-slate-400">({deals.length})</span>
                </div>
                <button
                  onClick={() => {
                    setNewDealName(client?.name || "");
                    setShowNewDeal(true);
                  }}
                  className="text-xs text-blue-500 cursor-pointer"
                >
                  + 新增
                </button>
              </div>
              {showNewDeal && (
                <div className="mb-3 p-3 rounded-lg bg-slate-50 dark:bg-slate-800 space-y-2">
                  <input
                    type="text"
                    value={newDealName}
                    onChange={(e) => setNewDealName(e.target.value)}
                    placeholder="商機名稱"
                    className="w-full text-sm px-3 py-1.5 rounded-md border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100"
                    autoFocus
                    onKeyDown={(e) => {
                      if (e.key === "Escape") setShowNewDeal(false);
                    }}
                  />
                  <div className="flex gap-2 justify-end">
                    <button
                      onClick={() => setShowNewDeal(false)}
                      className="text-xs px-3 py-1 rounded-md border border-slate-200 dark:border-slate-600 text-slate-500"
                    >
                      取消
                    </button>
                    <button
                      disabled={!newDealName.trim() || creatingDeal}
                      onClick={async () => {
                        setCreatingDeal(true);
                        try {
                          await nxApi.deals.create({
                            name: newDealName.trim(),
                            client_id: clientId,
                          });
                          setShowNewDeal(false);
                          setNewDealName("");
                          loadData();
                        } catch (err) {
                          console.error(err);
                        } finally {
                          setCreatingDeal(false);
                        }
                      }}
                      className="text-xs px-3 py-1 rounded-md bg-blue-600 text-white disabled:opacity-50"
                    >
                      {creatingDeal ? "建立中..." : "建立商機"}
                    </button>
                  </div>
                </div>
              )}
              <div className="divide-y divide-slate-100 dark:divide-slate-800">
                {deals.length > 0 ? (
                  deals.map((d) => (
                    <Link
                      key={d.id}
                      href={`/deals/${d.id}?from=client&orgId=${clientId}`}
                      className="block py-2 hover:bg-slate-50 dark:hover:bg-slate-800/50 -mx-1 px-1 rounded transition-colors"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-slate-700 dark:text-slate-300">
                          {d.name}
                        </span>
                        <span
                          className={`text-[11px] px-2 py-0.5 rounded-full font-medium ${
                            d.status === "closed"
                              ? "bg-slate-700 text-slate-400"
                              : "bg-blue-500/10 text-blue-400"
                          }`}
                        >
                          {STAGE_LABELS[d.stage] || d.stage}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 mt-1 flex-wrap">
                        {d.budget_amount && (
                          <span className="text-[11px] text-slate-400">
                            {formatBudget(d.budget_amount)}
                          </span>
                        )}
                        {d.partners?.map((p) => (
                          <span
                            key={p.partner_name}
                            className="text-[11px] px-2 py-0.5 rounded-full bg-green-500/10 text-green-400"
                          >
                            {p.partner_name}{p.role ? ` (${p.role})` : ""}
                          </span>
                        ))}
                      </div>
                    </Link>
                  ))
                ) : (
                  <p className="text-xs text-slate-400 py-2">尚無相關商機</p>
                )}
              </div>
            </div>
            {/* Related Intel */}
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-3">
                <Zap size={16} className="text-cyan-500" />
                <span className="text-sm font-semibold text-slate-900 dark:text-slate-50">
                  相關情報
                </span>
                <span className="text-xs text-slate-400">({linkedIntel.length})</span>
              </div>
              <div className="divide-y divide-slate-100 dark:divide-slate-800">
                {linkedIntel.length > 0 ? (
                  linkedIntel.map((i) => (
                    <Link
                      key={i.id}
                      href={`/intel/${i.id}`}
                      className="block py-2 hover:bg-slate-50 dark:hover:bg-slate-800/50 -mx-1 px-1 rounded transition-colors"
                    >
                      <p className="text-sm text-slate-700 dark:text-slate-300 line-clamp-2">
                        {getIntelDisplayTitle(i, 80)}
                      </p>
                      <div className="flex items-center gap-2 mt-1">
                        <span
                          className={`text-[11px] px-2 py-0.5 rounded-full font-medium ${
                            i.status === "confirmed"
                              ? "bg-green-500/10 text-green-400"
                              : "bg-amber-500/10 text-amber-400"
                          }`}
                        >
                          {i.status === "confirmed" ? "已確認" : "草稿"}
                        </span>
                        <span className="text-[11px] text-slate-400">
                          {new Date(i.created_at).toLocaleDateString("zh-TW")}
                        </span>
                      </div>
                    </Link>
                  ))
                ) : (
                  <p className="text-xs text-slate-400 py-2">尚無關聯情報</p>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {showContactModal && (
        <ContactFormModal
          orgType="client"
          orgId={clientId}
          onClose={() => setShowContactModal(false)}
          onCreated={loadData}
        />
      )}

      {editContact && (
        <ContactFormModal
          orgType="client"
          orgId={clientId}
          contact={editContact}
          onClose={() => setEditContact(null)}
          onCreated={loadData}
        />
      )}

      {uploadDoc && (
        <DocUploadModal
          docId={uploadDoc.id}
          currentPath={uploadDoc.file_path}
          onClose={() => setUploadDoc(null)}
          onUploaded={() => {
            setUploadDoc(null);
            loadData();
          }}
        />
      )}
    </div>
  );
}
