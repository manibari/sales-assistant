"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { TopBar } from "@/components/top-bar";
import { ContactFormModal } from "@/components/contact-form-modal";
import { getIntelDisplayTitle } from "@/lib/intel-display";
import {
  ChevronLeft,
  Handshake,
  Check,
  X,
  Loader2,
  Users,
  Briefcase,
  Pencil,
  Zap,
  Trash2,
} from "lucide-react";
import {
  nxApi,
  type NxPartner,
  type NxContact,
  type NxDeal,
  type NxIntel,
} from "@/lib/nexus-api";

const TRUST_LEVELS = [
  { label: "未驗證", value: "unverified" },
  { label: "驗證中", value: "testing" },
  { label: "已驗證", value: "verified" },
  { label: "核心班底", value: "core_team" },
  { label: "SI 擔保", value: "si_backed" },
  { label: "不推薦", value: "demoted" },
];

const TRUST_COLORS: Record<string, string> = {
  unverified: "bg-amber-500/10 text-amber-400",
  testing: "bg-blue-500/10 text-blue-400",
  verified: "bg-green-500/10 text-green-400",
  core_team: "bg-green-500/10 text-green-400",
  si_backed: "bg-violet-500/10 text-violet-400",
  demoted: "bg-red-500/10 text-red-400",
};

const STAGE_LABELS: Record<string, string> = {
  L0: "L0 潛在",
  L1: "L1 接觸中",
  L2: "L2 需求確認",
  L3: "L3 報價",
  L4: "L4 簽約",
  closed: "已關閉",
};

export default function PartnerDetailPage() {
  const params = useParams();
  const router = useRouter();
  const partnerId = Number(params.id);

  const [partner, setPartner] = useState<NxPartner | null>(null);
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

  const loadData = useCallback(() => {
    Promise.all([
      nxApi.partners.get(partnerId),
      nxApi.contacts.list("partner", partnerId),
      nxApi.deals.listByPartner(partnerId),
      nxApi.intel.byEntity("partner", partnerId),
    ])
      .then(([p, ct, d, intel]) => {
        setPartner(p);
        setContacts(ct);
        setDeals(d);
        setLinkedIntel(intel);
        setNotesValue(p.notes || "");
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [partnerId]);

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
    if (!editField || !partner) return;
    setSaving(true);
    try {
      await nxApi.partners.update(partnerId, { [editField]: editValue } as Partial<NxPartner>);
      cancelEdit();
      loadData();
    } catch (err) {
      console.error("Failed to save:", err);
    } finally {
      setSaving(false);
    }
  };

  const handleTrustChange = async (newLevel: string) => {
    setSaving(true);
    try {
      await nxApi.partners.update(partnerId, { trust_level: newLevel } as Partial<NxPartner>);
      loadData();
    } catch (err) {
      console.error("Failed to update trust level:", err);
    } finally {
      setSaving(false);
    }
  };

  const saveNotes = async () => {
    setSaving(true);
    try {
      await nxApi.partners.update(partnerId, { notes: notesValue } as Partial<NxPartner>);
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

  if (!partner) {
    return (
      <div className="flex flex-col h-full">
        <TopBar title="Partner Detail" />
        <div className="flex-1 flex items-center justify-center text-slate-500">找不到此夥伴</div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <TopBar title={partner.name}>
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
                <div className="w-10 h-10 rounded-lg bg-green-500/10 flex items-center justify-center flex-shrink-0">
                  <Handshake size={20} className="text-green-500" />
                </div>
                <div className="flex-1 min-w-0">
                  <span
                    className={`text-xs px-2.5 py-1 rounded-full font-medium ${
                      TRUST_COLORS[partner.trust_level] || "bg-slate-700 text-slate-400"
                    }`}
                  >
                    {TRUST_LEVELS.find((t) => t.value === partner.trust_level)?.label || partner.trust_level}
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
                  onClick={() => startEdit("name", partner.name)}
                  className="text-lg font-semibold text-slate-900 dark:text-slate-50 cursor-pointer hover:text-blue-500 transition-colors"
                  title="Click to edit name"
                >
                  {partner.name}
                </h2>
              )}

              <div className="flex gap-4 mt-3 text-xs text-slate-400 dark:text-slate-500">
                {partner.team_size && <span>團隊: {partner.team_size} 人</span>}
              </div>

              {/* Trust level dropdown */}
              <div className="mt-4">
                <label className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-1 block">
                  信任等級
                </label>
                <select
                  value={partner.trust_level}
                  onChange={(e) => handleTrustChange(e.target.value)}
                  disabled={saving}
                  className="w-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-900 dark:text-slate-50 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none cursor-pointer"
                >
                  {TRUST_LEVELS.map((t) => (
                    <option key={t.value} value={t.value}>
                      {t.label}
                    </option>
                  ))}
                </select>
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
                        setNotesValue(partner.notes || "");
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
                  {partner.notes || "尚無備註"}
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
                  刪除此夥伴
                </button>
              ) : (
                <div className="flex items-center gap-2 bg-red-500/5 border border-red-500/20 rounded-lg p-3">
                  <span className="text-xs text-red-400 flex-1">確定刪除？相關聯絡人不會被刪除。</span>
                  <button
                    onClick={async () => {
                      await nxApi.partners.delete(partnerId);
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
              <div className="flex items-center gap-2 mb-3">
                <Briefcase size={16} className="text-blue-500" />
                <span className="text-sm font-semibold text-slate-900 dark:text-slate-50">
                  相關商機
                </span>
                <span className="text-xs text-slate-400">({deals.length})</span>
              </div>
              <div className="divide-y divide-slate-100 dark:divide-slate-800">
                {deals.length > 0 ? (
                  deals.map((d) => (
                    <Link
                      key={d.id}
                      href={`/deals/${d.id}?from=partner&orgId=${partnerId}`}
                      className="flex items-center justify-between py-2 hover:bg-slate-50 dark:hover:bg-slate-800/50 -mx-1 px-1 rounded transition-colors"
                    >
                      <div className="min-w-0 flex-1">
                        <span className="text-sm text-slate-700 dark:text-slate-300">
                          {d.client_name && (
                            <span className="text-slate-400 dark:text-slate-500">{d.client_name} — </span>
                          )}
                          {d.name}
                        </span>
                      </div>
                      <span
                        className={`text-[11px] px-2 py-0.5 rounded-full font-medium flex-shrink-0 ml-2 ${
                          d.status === "closed"
                            ? "bg-slate-700 text-slate-400"
                            : "bg-blue-500/10 text-blue-400"
                        }`}
                      >
                        {STAGE_LABELS[d.stage] || d.stage}
                      </span>
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
                <Zap size={16} className="text-amber-500" />
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
                              : i.status === "draft"
                                ? "bg-amber-500/10 text-amber-400"
                                : "bg-slate-500/10 text-slate-400"
                          }`}
                        >
                          {i.status === "confirmed" ? "已確認" : i.status === "draft" ? "草稿" : i.status}
                        </span>
                        <span className="text-[11px] text-slate-400">
                          {new Date(i.created_at).toLocaleDateString("zh-TW")}
                        </span>
                      </div>
                    </Link>
                  ))
                ) : (
                  <p className="text-xs text-slate-400 py-2">尚無相關情報</p>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {showContactModal && (
        <ContactFormModal
          orgType="partner"
          orgId={partnerId}
          onClose={() => setShowContactModal(false)}
          onCreated={loadData}
        />
      )}

      {editContact && (
        <ContactFormModal
          orgType="partner"
          orgId={partnerId}
          contact={editContact}
          onClose={() => setEditContact(null)}
          onCreated={loadData}
        />
      )}
    </div>
  );
}
