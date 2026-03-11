"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { TopBar } from "@/components/top-bar";
import {
  ChevronLeft,
  ChevronUp,
  ChevronDown,
  Check,
  X,
  AlertTriangle,
  Handshake,
  Zap,
  CircleDot,
  FileCheck,
  Calendar,
  Loader2,
  Pencil,
  ExternalLink,
  Download,
  Users,
} from "lucide-react";
import { nxApi, type NxDeal, type NxPartner, type NxIntel, type NxContact, type MeddicProgress } from "@/lib/nexus-api";
import { formatBudget } from "@/lib/options";
import { FileUploadModal } from "@/components/file-upload-modal";
import { ContactFormModal } from "@/components/contact-form-modal";
import { DealGantt } from "@/components/deal-gantt";
import Link from "next/link";

const TRUST_LABELS: Record<string, string> = {
  unverified: "未驗證", testing: "驗證中", verified: "已驗證",
  core_team: "核心班底", si_backed: "SI 擔保", demoted: "不推薦",
};

const STAGE_ORDER = ["L0", "L1", "L2", "L3", "L4"];
const STAGE_LABELS: Record<string, string> = {
  L0: "L0 潛在",
  L1: "L1 接觸中",
  L2: "L2 需求確認",
  L3: "L3 報價",
  L4: "L4 簽約",
  closed: "已關閉",
};

const MEDDIC_LABELS: Record<string, string> = {
  metrics: "Metrics (量化指標)",
  economic_buyer: "Economic Buyer (經濟決策者)",
  decision_criteria: "Decision Criteria (決策標準)",
  decision_process: "Decision Process (決策流程)",
  identify_pain: "Identify Pain (痛點辨識)",
  champion: "Champion (內部擁護者)",
};

const CLOSE_REASONS = [
  { label: "預算不足", value: "budget" },
  { label: "時程不合", value: "timing" },
  { label: "選擇競品", value: "competitor" },
  { label: "需求消失", value: "no_need" },
  { label: "其他", value: "other" },
];

export default function DealDetailPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const dealId = Number(params.id);

  // Back navigation: return to originating contact page if available
  const fromType = searchParams.get("from"); // "client" | "partner"
  const orgId = searchParams.get("orgId");
  const backHref = fromType && orgId ? `/contacts/${fromType}s/${orgId}` : "/deals";

  const [deal, setDeal] = useState<NxDeal | null>(null);
  const [loading, setLoading] = useState(true);
  const [meddicOpen, setMeddicOpen] = useState(false);
  const [editingMeddic, setEditingMeddic] = useState<string | null>(null);
  const [meddicValue, setMeddicValue] = useState("");
  const [showCloseModal, setShowCloseModal] = useState(false);
  const [closeReason, setCloseReason] = useState("");
  const [closeNotes, setCloseNotes] = useState("");
  const [advancing, setAdvancing] = useState(false);
  const [showFileUpload, setShowFileUpload] = useState(false);
  const [showAddPartner, setShowAddPartner] = useState(false);
  const [showAddIntel, setShowAddIntel] = useState(false);
  const [showAddTbd, setShowAddTbd] = useState(false);
  const [editingSection, setEditingSection] = useState<string | null>(null);
  const [allPartners, setAllPartners] = useState<NxPartner[]>([]);
  const [allIntels, setAllIntels] = useState<NxIntel[]>([]);
  const [tbdQuestion, setTbdQuestion] = useState("");
  const [partnerRole, setPartnerRole] = useState("");
  const [contacts, setContacts] = useState<NxContact[]>([]);
  const [showContactModal, setShowContactModal] = useState(false);
  const [editContact, setEditContact] = useState<NxContact | null>(null);
  const [editField, setEditField] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");
  const [saving, setSaving] = useState(false);
  const [editingFileId, setEditingFileId] = useState<number | null>(null);
  const [editingFileName, setEditingFileName] = useState("");

  const startEdit = (field: string, currentValue: string) => {
    setEditField(field);
    setEditValue(currentValue || "");
  };

  const cancelEdit = () => {
    setEditField(null);
    setEditValue("");
  };

  const saveField = async () => {
    if (!editField || !deal) return;
    setSaving(true);
    try {
      let value: string | number | null = editValue;
      if (editField === "budget_amount") {
        const n = parseFloat(editValue);
        value = isNaN(n) ? null : n;
      }
      await nxApi.deals.update(dealId, { [editField]: value } as Partial<NxDeal>);
      cancelEdit();
      loadDeal();
    } catch (err) {
      console.error("Failed to save:", err);
    } finally {
      setSaving(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") saveField();
    if (e.key === "Escape") cancelEdit();
  };

  const loadDeal = useCallback(() => {
    nxApi.deals
      .get(dealId)
      .then((d) => {
        setDeal(d);
        // Load contacts for this deal's client
        if (d.client_id) {
          nxApi.contacts.list("client", d.client_id).then(setContacts).catch(console.error);
        }
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [dealId]);

  useEffect(() => {
    loadDeal();
  }, [loadDeal]);

  const handleStageClick = async (targetStage: string) => {
    if (!deal) return;
    const currentIdx = STAGE_ORDER.indexOf(deal.stage);
    const targetIdx = STAGE_ORDER.indexOf(targetStage);
    if (currentIdx < 0 || targetIdx < 0 || currentIdx === targetIdx) return;

    const isForward = targetIdx > currentIdx;

    // MEDDIC gate only on forward movement past L1
    if (isForward) {
      const progress = deal.meddic_progress;
      if (progress && progress.missing.length > 0 && currentIdx >= 1) {
        alert(`需先完成 MEDDIC：${progress.missing.join(", ")}`);
        setMeddicOpen(true);
        return;
      }
    }

    // Confirm backward movement
    if (!isForward) {
      const ok = confirm(`確定要將階段從 ${STAGE_LABELS[deal.stage]} 退回到 ${STAGE_LABELS[targetStage]}？`);
      if (!ok) return;
    }

    setAdvancing(true);
    try {
      await nxApi.deals.advance(dealId, targetStage);
      loadDeal();
    } catch (err) {
      console.error("Failed to change stage:", err);
    } finally {
      setAdvancing(false);
    }
  };

  const handleClose = async () => {
    if (!closeReason) return;
    try {
      await nxApi.deals.close(dealId, closeReason, closeNotes || undefined);
      setShowCloseModal(false);
      loadDeal();
    } catch (err) {
      console.error("Failed to close:", err);
    }
  };

  const handleMeddicSave = async (key: string) => {
    if (!deal) return;
    const current = deal.meddic_json ? JSON.parse(deal.meddic_json) : {};
    current[key] = meddicValue;
    try {
      await nxApi.deals.update(dealId, { meddic_json: JSON.stringify(current) } as Partial<NxDeal>);
      setEditingMeddic(null);
      setMeddicValue("");
      loadDeal();
    } catch (err) {
      console.error("Failed to save MEDDIC:", err);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 size={24} className="animate-spin text-blue-500" />
      </div>
    );
  }

  if (!deal) {
    return (
      <div className="flex flex-col h-full">
        <TopBar title="商機詳情" />
        <div className="flex-1 flex items-center justify-center text-slate-500">找不到此商機</div>
      </div>
    );
  }

  const meddic: Record<string, string | null> = deal.meddic_json
    ? JSON.parse(deal.meddic_json)
    : {};
  const progress: MeddicProgress = deal.meddic_progress || {
    completed: 0,
    total: 6,
    missing: [],
  };
  const isClosed = deal.status === "closed";

  return (
    <div className="flex flex-col h-full">
      <TopBar title={deal.name}>
        <Link
          href={backHref}
          className="p-2 rounded-lg text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer transition-colors"
        >
          <ChevronLeft size={20} />
        </Link>
      </TopBar>

      <div className="flex-1 px-4 lg:px-6 py-4 overflow-auto max-w-2xl lg:max-w-6xl mx-auto w-full">
        {/* Desktop: 2-column layout */}
        <div className="lg:grid lg:grid-cols-5 lg:gap-6 space-y-4 lg:space-y-0">
        {/* Left column (3/5) — header + MEDDIC */}
        <div className="lg:col-span-3 space-y-4">
        {/* Header card */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-5">
          <div className="flex items-center justify-between mb-3">
            <span
              className={`text-xs px-2.5 py-1 rounded-full font-medium ${
                isClosed
                  ? "bg-slate-700 text-slate-400"
                  : "bg-blue-500/10 text-blue-400"
              }`}
            >
              {STAGE_LABELS[deal.stage] || deal.stage}
            </span>
            {deal.idle_days !== undefined && deal.idle_days > 0 && !isClosed && (
              <span
                className={`text-[11px] flex items-center gap-1 ${
                  deal.idle_days > 14 ? "text-red-400" : "text-slate-400"
                }`}
              >
                {deal.idle_days > 14 && <AlertTriangle size={12} />}
                {deal.idle_days} 天未動
              </span>
            )}
          </div>
          {/* Editable deal name */}
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
              onClick={() => !isClosed && startEdit("name", deal.name)}
              className={`text-lg font-semibold text-slate-900 dark:text-slate-50 ${!isClosed ? "cursor-pointer hover:text-blue-500 transition-colors" : ""}`}
              title={!isClosed ? "點擊編輯名稱" : undefined}
            >
              {deal.name}
            </h2>
          )}
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            {deal.client_name} · {deal.client_industry || "—"}
          </p>

          {/* Editable budget & timeline */}
          <div className="flex gap-4 mt-3 text-xs text-slate-400 dark:text-slate-500">
            {editField === "budget_amount" ? (
              <div className="flex items-center gap-1">
                <span>預算:</span>
                <input
                  type="number"
                  value={editValue}
                  onChange={(e) => setEditValue(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="金額 (元)"
                  className="w-28 bg-slate-100 dark:bg-slate-800 border border-blue-500 rounded px-2 py-0.5 text-xs text-slate-900 dark:text-slate-50 focus:outline-none"
                  autoFocus
                />
                <button onClick={saveField} disabled={saving} className="p-0.5 text-blue-500 cursor-pointer"><Check size={12} /></button>
                <button onClick={cancelEdit} className="p-0.5 text-slate-400 cursor-pointer"><X size={12} /></button>
              </div>
            ) : (
              <span
                onClick={() => !isClosed && startEdit("budget_amount", String(deal.budget_amount || ""))}
                className={!isClosed ? "cursor-pointer hover:text-blue-400 transition-colors" : ""}
                title={!isClosed ? "點擊編輯預算" : undefined}
              >
                預算: {formatBudget(deal.budget_amount)}
              </span>
            )}
            {editField === "timeline" ? (
              <div className="flex items-center gap-1">
                <span>時程:</span>
                <input
                  type="text"
                  value={editValue}
                  onChange={(e) => setEditValue(e.target.value)}
                  onKeyDown={handleKeyDown}
                  className="w-28 bg-slate-100 dark:bg-slate-800 border border-blue-500 rounded px-2 py-0.5 text-xs text-slate-900 dark:text-slate-50 focus:outline-none"
                  autoFocus
                />
                <button onClick={saveField} disabled={saving} className="p-0.5 text-blue-500 cursor-pointer"><Check size={12} /></button>
                <button onClick={cancelEdit} className="p-0.5 text-slate-400 cursor-pointer"><X size={12} /></button>
              </div>
            ) : (
              <span
                onClick={() => !isClosed && startEdit("timeline", deal.timeline || "")}
                className={!isClosed ? "cursor-pointer hover:text-blue-400 transition-colors" : ""}
                title={!isClosed ? "點擊編輯時程" : undefined}
              >
                時程: {deal.timeline || "—"}
              </span>
            )}
          </div>

          {/* Reopen closed deal */}
          {isClosed && (
            <div className="mt-4">
              <p className="text-xs text-slate-400 mb-2">
                關閉原因: {deal.close_reason || "—"}{deal.close_notes ? ` — ${deal.close_notes}` : ""}
              </p>
              <button
                onClick={async () => {
                  if (!confirm("確定要重新開啟此商機？將回到 L0 階段。")) return;
                  setAdvancing(true);
                  try {
                    await nxApi.deals.update(dealId, { status: "active", stage: "L0" } as Partial<NxDeal>);
                    loadDeal();
                  } catch (err) {
                    console.error("Failed to reopen:", err);
                  } finally {
                    setAdvancing(false);
                  }
                }}
                disabled={advancing}
                className="w-full bg-blue-500 hover:bg-blue-600 text-white font-semibold px-4 py-2.5 rounded-lg text-sm min-h-[44px] active:scale-[0.98] transition-all cursor-pointer disabled:opacity-50"
              >
                {advancing ? "處理中..." : "重新開啟案件"}
              </button>
            </div>
          )}

          {/* Stage stepper */}
          {!isClosed && (
            <div className="mt-4 space-y-3">
              <div className="flex items-center gap-1">
                {STAGE_ORDER.map((s, i) => {
                  const currentIdx = STAGE_ORDER.indexOf(deal.stage);
                  const isActive = i === currentIdx;
                  const isPast = i < currentIdx;
                  return (
                    <button
                      key={s}
                      onClick={() => {
                        if (i !== currentIdx && !advancing) handleStageClick(s);
                      }}
                      disabled={advancing || i === currentIdx}
                      className={`flex-1 py-2 text-xs font-medium rounded-lg cursor-pointer transition-all disabled:cursor-default ${
                        isActive
                          ? "bg-blue-500 text-white"
                          : isPast
                          ? "bg-blue-500/10 text-blue-400 hover:bg-blue-500/20"
                          : "bg-slate-100 dark:bg-slate-800 text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700"
                      }`}
                    >
                      {advancing ? "…" : STAGE_LABELS[s]?.split(" ")[0] || s}
                    </button>
                  );
                })}
              </div>
              <button
                onClick={() => setShowCloseModal(true)}
                className="w-full px-4 py-2.5 rounded-lg text-sm font-medium bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 min-h-[44px] cursor-pointer transition-colors"
              >
                關閉案件
              </button>
            </div>
          )}
        </div>

        {/* Deal Gantt */}
        {deal.created_at && (
          <DealGantt
            dealId={dealId}
            dealCreatedAt={deal.created_at}
            currentStage={deal.stage}
            intel={deal.intel}
            onDealUpdated={loadDeal}
          />
        )}

        {/* MEDDIC Progress */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl overflow-hidden">
          <button
            onClick={() => setMeddicOpen(!meddicOpen)}
            className="w-full flex items-center justify-between p-4 cursor-pointer"
          >
            <div className="flex items-center gap-3">
              <span className="text-sm font-semibold text-slate-900 dark:text-slate-50">
                MEDDIC 進度
              </span>
              <span className="text-xs text-slate-400">
                {progress.completed}/{progress.total}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-20 h-1.5 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-green-500 rounded-full transition-all"
                  style={{
                    width: `${(progress.completed / progress.total) * 100}%`,
                  }}
                />
              </div>
              {meddicOpen ? (
                <ChevronUp size={16} className="text-slate-400" />
              ) : (
                <ChevronDown size={16} className="text-slate-400" />
              )}
            </div>
          </button>
          {meddicOpen && (
            <div className="border-t border-slate-200 dark:border-slate-700 divide-y divide-slate-200 dark:divide-slate-700">
              {Object.entries(MEDDIC_LABELS).map(([key, label]) => {
                const value = meddic[key];
                const isEditing = editingMeddic === key;
                return (
                  <div key={key} className="px-4 py-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {value ? (
                          <Check size={14} className="text-green-500" />
                        ) : (
                          <CircleDot size={14} className="text-slate-400" />
                        )}
                        <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
                          {label}
                        </span>
                      </div>
                      {!isEditing && !isClosed && (
                        <button
                          onClick={() => {
                            setEditingMeddic(key);
                            setMeddicValue(value || "");
                          }}
                          className="text-xs text-blue-500 cursor-pointer"
                        >
                          {value ? "編輯" : "填寫"}
                        </button>
                      )}
                    </div>
                    {value && !isEditing && (
                      <p className="text-sm text-slate-700 dark:text-slate-300 mt-1 ml-6">
                        {value}
                      </p>
                    )}
                    {isEditing && (
                      <div className="mt-2 ml-6 flex gap-2">
                        <input
                          type="text"
                          value={meddicValue}
                          onChange={(e) => setMeddicValue(e.target.value)}
                          className="flex-1 bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-900 dark:text-slate-50 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
                          placeholder="輸入內容..."
                          autoFocus
                        />
                        <button
                          onClick={() => handleMeddicSave(key)}
                          className="p-2 bg-blue-500 text-white rounded-lg cursor-pointer"
                        >
                          <Check size={16} />
                        </button>
                        <button
                          onClick={() => setEditingMeddic(null)}
                          className="p-2 bg-slate-200 dark:bg-slate-700 rounded-lg cursor-pointer"
                        >
                          <X size={16} />
                        </button>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        </div>
        {/* Right column (2/5) — related data */}
        <div className="lg:col-span-2 space-y-4">
        {/* Partners */}
        <Section
          title="搭配夥伴"
          icon={<Handshake size={16} className="text-green-500" />}
          count={deal.partners?.length}
          editing={editingSection === "partners"}
          onToggleEdit={!isClosed ? () => setEditingSection(editingSection === "partners" ? null : "partners") : undefined}
          onAdd={editingSection === "partners" ? async () => {
            setShowAddPartner(true);
            try {
              const partners = await nxApi.partners.list();
              setAllPartners(partners);
            } catch (err) { console.error(err); }
          } : undefined}
        >
          {deal.partners && deal.partners.length > 0 ? (
            deal.partners.map((p) => (
              <div
                key={p.id}
                className="flex items-center justify-between py-2"
              >
                <div className="flex-1 min-w-0">
                  <span className="text-sm text-slate-900 dark:text-slate-50">
                    {p.partner_name}
                  </span>
                  {p.role && (
                    <span className="text-xs text-slate-400 ml-2">({p.role})</span>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[11px] px-2 py-0.5 rounded-full bg-green-500/10 text-green-400">
                    {p.trust_level}
                  </span>
                  {editingSection === "partners" && (
                    <button
                      onClick={async () => {
                        if (!confirm(`確定移除「${p.partner_name}」？`)) return;
                        try {
                          await nxApi.deals.removePartner(dealId, p.partner_id);
                          loadDeal();
                        } catch (err) { console.error(err); }
                      }}
                      className="p-1 text-red-400 hover:text-red-500 hover:bg-red-500/10 rounded cursor-pointer transition-colors"
                    >
                      <X size={14} />
                    </button>
                  )}
                </div>
              </div>
            ))
          ) : (
            <p className="text-xs text-slate-400">尚無配對夥伴</p>
          )}
        </Section>

        {/* Contacts (key people) */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Users size={16} className="text-violet-500" />
              <span className="text-sm font-semibold text-slate-900 dark:text-slate-50">
                關鍵人物
              </span>
              <span className="text-xs text-slate-400">({contacts.length})</span>
            </div>
            {!isClosed && (
              <button
                onClick={() => setShowContactModal(true)}
                className="text-xs text-blue-500 cursor-pointer"
              >
                + 新增
              </button>
            )}
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
                  </div>
                </div>
              ))
            ) : (
              <p className="text-xs text-slate-400 py-2">尚無聯絡人</p>
            )}
          </div>
        </div>

        {/* Related Intel */}
        <Section
          title="相關情報"
          icon={<Zap size={16} className="text-cyan-500" />}
          count={deal.intel?.length}
          editing={editingSection === "intel"}
          onToggleEdit={!isClosed ? () => setEditingSection(editingSection === "intel" ? null : "intel") : undefined}
          onAdd={editingSection === "intel" ? async () => {
            setShowAddIntel(true);
            try {
              const intels = await nxApi.intel.list();
              setAllIntels(intels);
            } catch (err) { console.error(err); }
          } : undefined}
        >
          {deal.intel && deal.intel.length > 0 ? (
            deal.intel.map((i: { id: number; raw_input: string; intel_created_at?: string }) => (
              <div key={i.id} className="flex items-start justify-between py-2 gap-2">
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-slate-700 dark:text-slate-300 line-clamp-2">
                    {i.raw_input}
                  </p>
                  <span className="text-[11px] text-slate-400 mt-1">
                    {i.intel_created_at
                      ? new Date(i.intel_created_at).toLocaleDateString("zh-TW")
                      : ""}
                  </span>
                </div>
                {editingSection === "intel" && (
                  <button
                    onClick={async () => {
                      if (!confirm("確定取消關聯此情報？")) return;
                      try {
                        await nxApi.deals.unlinkIntel(dealId, i.id);
                        loadDeal();
                      } catch (err) { console.error(err); }
                    }}
                    className="p-1 text-red-400 hover:text-red-500 hover:bg-red-500/10 rounded cursor-pointer transition-colors flex-shrink-0 mt-0.5"
                  >
                    <X size={14} />
                  </button>
                )}
              </div>
            ))
          ) : (
            <p className="text-xs text-slate-400">尚無關聯情報</p>
          )}
        </Section>

        {/* TBDs */}
        <Section
          title="TBD 清單"
          icon={<CircleDot size={16} className="text-amber-500" />}
          count={deal.tbds?.length}
          editing={editingSection === "tbds"}
          onToggleEdit={!isClosed ? () => setEditingSection(editingSection === "tbds" ? null : "tbds") : undefined}
          onAdd={editingSection === "tbds" ? () => setShowAddTbd(true) : undefined}
        >
          {deal.tbds && deal.tbds.length > 0 ? (
            deal.tbds.map((t) => (
              <div
                key={t.id}
                className="flex items-center justify-between py-2"
              >
                <span className="text-sm text-slate-700 dark:text-slate-300">
                  {t.question}
                </span>
                <button
                  onClick={async () => {
                    await nxApi.tbd.resolve(t.id);
                    loadDeal();
                  }}
                  className="text-xs text-green-500 cursor-pointer"
                >
                  解決
                </button>
              </div>
            ))
          ) : (
            <p className="text-xs text-slate-400">無待確認事項</p>
          )}
        </Section>

        {/* Files */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <FileCheck size={16} className="text-blue-500" />
              <span className="text-sm font-semibold text-slate-900 dark:text-slate-50">
                文件
              </span>
              <span className="text-xs text-slate-400">
                ({deal.files?.length || 0})
              </span>
            </div>
            {!isClosed && (
              <button
                onClick={() => setShowFileUpload(true)}
                className="text-xs text-blue-500 cursor-pointer"
              >
                + 新增
              </button>
            )}
          </div>
          <div className="divide-y divide-slate-100 dark:divide-slate-800">
            {deal.files && deal.files.length > 0 ? (
              deal.files.map((f) => {
                const isExternal = !!f.source_url;
                const isLocal = !isExternal && f.file_path && !f.file_path.startsWith("link://");
                const statusBadge = f.parse_status === "parsed"
                  ? { label: "已解析", cls: "bg-green-500/10 text-green-400" }
                  : f.parse_status === "failed"
                    ? { label: "解析失敗", cls: "bg-red-500/10 text-red-400" }
                    : isExternal
                      ? { label: "外部連結", cls: "bg-blue-500/10 text-blue-400" }
                      : { label: "已上傳", cls: "bg-slate-500/10 text-slate-400" };
                const href = isExternal
                  ? f.source_url!
                  : `/api/nx/documents/files/${f.id}/download`;
                return (
                  <div
                    key={f.id}
                    className="flex items-center justify-between py-2"
                  >
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
                                loadDeal();
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
                              loadDeal();
                            }}
                            className="p-1 bg-blue-500 text-white rounded cursor-pointer"
                          >
                            <Check size={12} />
                          </button>
                          <button
                            onClick={() => setEditingFileId(null)}
                            className="p-1 bg-slate-200 dark:bg-slate-700 rounded cursor-pointer"
                          >
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
                        <span className="text-[11px] text-slate-400 truncate block">
                          {f.source_url.slice(0, 40)}...
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-2 ml-2">
                      <span className="text-[11px] px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400">
                        {f.file_type === "proposal" ? "簡報" : f.file_type === "contract" ? "合約" : "附件"}
                      </span>
                      <span className={`text-[11px] px-2 py-0.5 rounded-full ${statusBadge.cls}`}>
                        {statusBadge.label}
                      </span>
                    </div>
                  </div>
                );
              })
            ) : (
              <p className="text-xs text-slate-400 py-2">尚無文件</p>
            )}
          </div>
        </div>

        {/* Next action */}
        {!isClosed && (
          <Link
            href={`/calendar`}
            className="flex items-center gap-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4 cursor-pointer hover:border-slate-300 dark:hover:border-slate-600 transition-colors"
          >
            <Calendar size={20} className="text-blue-500" />
            <span className="text-sm font-medium text-slate-900 dark:text-slate-50">
              排下次會議
            </span>
          </Link>
        )}
        </div>
        </div>
      </div>

      {/* File upload modal */}
      {showFileUpload && (
        <FileUploadModal
          dealId={dealId}
          onClose={() => setShowFileUpload(false)}
          onUploaded={loadDeal}
        />
      )}

      {/* Add Partner modal */}
      {showAddPartner && (
        <div className="fixed inset-0 bg-slate-950/50 flex items-end md:items-center justify-center z-50">
          <div className="bg-white dark:bg-slate-900 rounded-t-2xl md:rounded-xl p-6 w-full max-w-md mx-auto space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold text-slate-900 dark:text-slate-50">新增搭配夥伴</h3>
              <button onClick={() => { setShowAddPartner(false); setPartnerRole(""); }} className="p-1.5 text-slate-400 hover:text-slate-200 cursor-pointer transition-colors"><X size={20} /></button>
            </div>
            <div>
              <label className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-1 block">角色 (選填)</label>
              <input
                type="text"
                value={partnerRole}
                onChange={(e) => setPartnerRole(e.target.value)}
                placeholder="例：系統整合、硬體供應"
                className="w-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-4 py-3 text-sm text-slate-900 dark:text-slate-50 placeholder:text-slate-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
              />
            </div>
            <div className="max-h-72 overflow-auto divide-y divide-slate-100 dark:divide-slate-800">
              {allPartners.length === 0 ? (
                <p className="text-sm text-slate-400 py-4 text-center">載入中...</p>
              ) : (
                allPartners
                  .filter((p) => !(deal?.partners || []).some((dp) => dp.partner_id === p.id))
                  .map((p) => (
                    <button
                      key={p.id}
                      onClick={async () => {
                        try {
                          await nxApi.deals.addPartner(dealId, p.id, partnerRole || undefined);
                          setShowAddPartner(false);
                          setPartnerRole("");
                          loadDeal();
                        } catch (err) { console.error(err); }
                      }}
                      className="w-full flex items-center justify-between py-3 px-1 hover:bg-slate-50 dark:hover:bg-slate-800/50 rounded transition-colors cursor-pointer text-left"
                    >
                      <span className="text-sm text-slate-900 dark:text-slate-50">{p.name}</span>
                      <span className="text-[11px] px-2 py-0.5 rounded-full bg-green-500/10 text-green-400">
                        {TRUST_LABELS[p.trust_level] || p.trust_level}
                      </span>
                    </button>
                  ))
              )}
              {allPartners.length > 0 && allPartners.filter((p) => !(deal?.partners || []).some((dp) => dp.partner_id === p.id)).length === 0 && (
                <p className="text-sm text-slate-400 py-4 text-center">所有夥伴已配對</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Add Intel modal */}
      {showAddIntel && (
        <div className="fixed inset-0 bg-slate-950/50 flex items-end md:items-center justify-center z-50">
          <div className="bg-white dark:bg-slate-900 rounded-t-2xl md:rounded-xl p-6 w-full max-w-md mx-auto space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold text-slate-900 dark:text-slate-50">關聯情報</h3>
              <button onClick={() => setShowAddIntel(false)} className="p-1.5 text-slate-400 hover:text-slate-200 cursor-pointer transition-colors"><X size={20} /></button>
            </div>
            <div className="max-h-72 overflow-auto divide-y divide-slate-100 dark:divide-slate-800">
              {allIntels.length === 0 ? (
                <p className="text-sm text-slate-400 py-4 text-center">載入中...</p>
              ) : (
                allIntels
                  .filter((i) => !(deal?.intel || []).some((di: { id: number }) => di.id === i.id || di.id === (i as unknown as { intel_id?: number }).intel_id))
                  .map((i) => (
                    <button
                      key={i.id}
                      onClick={async () => {
                        try {
                          await nxApi.deals.linkIntel(dealId, i.id);
                          setShowAddIntel(false);
                          loadDeal();
                        } catch (err) { console.error(err); }
                      }}
                      className="w-full py-3 px-1 hover:bg-slate-50 dark:hover:bg-slate-800/50 rounded transition-colors cursor-pointer text-left"
                    >
                      <p className="text-sm text-slate-900 dark:text-slate-50 line-clamp-2">{i.raw_input}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className={`text-[11px] px-2 py-0.5 rounded-full font-medium ${i.status === "confirmed" ? "bg-green-500/10 text-green-400" : "bg-amber-500/10 text-amber-400"}`}>
                          {i.status === "confirmed" ? "已確認" : "草稿"}
                        </span>
                        <span className="text-[11px] text-slate-400">{new Date(i.created_at).toLocaleDateString("zh-TW")}</span>
                      </div>
                    </button>
                  ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* Add TBD modal */}
      {showAddTbd && (
        <div className="fixed inset-0 bg-slate-950/50 flex items-end md:items-center justify-center z-50">
          <div className="bg-white dark:bg-slate-900 rounded-t-2xl md:rounded-xl p-6 w-full max-w-md mx-auto space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold text-slate-900 dark:text-slate-50">新增 TBD</h3>
              <button onClick={() => { setShowAddTbd(false); setTbdQuestion(""); }} className="p-1.5 text-slate-400 hover:text-slate-200 cursor-pointer transition-colors"><X size={20} /></button>
            </div>
            <div>
              <label className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-1 block">待確認事項</label>
              <textarea
                value={tbdQuestion}
                onChange={(e) => setTbdQuestion(e.target.value)}
                placeholder="例：客戶預算是否含稅？"
                className="w-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-4 py-3 text-sm text-slate-900 dark:text-slate-50 placeholder:text-slate-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none resize-none h-24"
                autoFocus
              />
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => { setShowAddTbd(false); setTbdQuestion(""); }}
                className="flex-1 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-700 font-medium px-4 py-3 rounded-lg min-h-[44px] cursor-pointer transition-colors"
              >
                取消
              </button>
              <button
                onClick={async () => {
                  if (!tbdQuestion.trim()) return;
                  try {
                    await nxApi.tbd.create({ question: tbdQuestion.trim(), linked_type: "deal", linked_id: dealId, source: "manual" });
                    setShowAddTbd(false);
                    setTbdQuestion("");
                    loadDeal();
                  } catch (err) { console.error(err); }
                }}
                disabled={!tbdQuestion.trim()}
                className="flex-1 bg-blue-500 hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold px-4 py-3 rounded-lg min-h-[44px] active:scale-[0.98] transition-all cursor-pointer"
              >
                建立
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Contact form modals */}
      {showContactModal && deal && (
        <ContactFormModal
          orgType="client"
          orgId={deal.client_id}
          onClose={() => setShowContactModal(false)}
          onCreated={loadDeal}
        />
      )}
      {editContact && deal && (
        <ContactFormModal
          orgType="client"
          orgId={deal.client_id}
          contact={editContact}
          onClose={() => setEditContact(null)}
          onCreated={loadDeal}
        />
      )}

      {/* Close modal */}
      {showCloseModal && (
        <div className="fixed inset-0 bg-slate-950/50 flex items-end md:items-center justify-center z-50">
          <div className="bg-white dark:bg-slate-900 rounded-t-2xl md:rounded-xl p-6 w-full max-w-md mx-auto space-y-4">
            <h3 className="text-lg font-bold text-slate-900 dark:text-slate-50">
              關閉商機
            </h3>
            <p className="text-sm text-slate-500">選擇關閉原因：</p>
            <div className="grid grid-cols-2 gap-2">
              {CLOSE_REASONS.map((r) => (
                <button
                  key={r.value}
                  onClick={() => setCloseReason(r.value)}
                  className={`min-h-[44px] px-3 py-2 text-sm font-medium rounded-lg border transition-colors cursor-pointer ${
                    closeReason === r.value
                      ? "border-red-500 bg-red-500/10 text-red-400"
                      : "bg-slate-100 dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200"
                  }`}
                >
                  {r.label}
                </button>
              ))}
            </div>
            <textarea
              value={closeNotes}
              onChange={(e) => setCloseNotes(e.target.value)}
              placeholder="備註 (optional)"
              className="w-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-4 py-3 text-sm text-slate-900 dark:text-slate-50 placeholder:text-slate-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none resize-none h-20"
            />
            <div className="flex gap-2">
              <button
                onClick={() => setShowCloseModal(false)}
                className="flex-1 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-700 font-medium px-4 py-3 rounded-lg min-h-[44px] cursor-pointer transition-colors"
              >
                取消
              </button>
              <button
                onClick={handleClose}
                disabled={!closeReason}
                className="flex-1 bg-red-500 hover:bg-red-600 disabled:opacity-50 text-white font-semibold px-4 py-3 rounded-lg min-h-[44px] cursor-pointer transition-all"
              >
                確定關閉
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function Section({
  title,
  icon,
  count,
  editing,
  onToggleEdit,
  onAdd,
  children,
}: {
  title: string;
  icon: React.ReactNode;
  count?: number;
  editing?: boolean;
  onToggleEdit?: () => void;
  onAdd?: () => void;
  children: React.ReactNode;
}) {
  return (
    <div className={`bg-white dark:bg-slate-900 border rounded-xl p-4 transition-colors ${editing ? "border-blue-500/50" : "border-slate-200 dark:border-slate-700"}`}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          {icon}
          <span className="text-sm font-semibold text-slate-900 dark:text-slate-50">
            {title}
          </span>
          {count !== undefined && (
            <span className="text-xs text-slate-400">({count})</span>
          )}
        </div>
        {onToggleEdit && (
          <button
            onClick={onToggleEdit}
            className={`text-xs cursor-pointer transition-colors ${editing ? "text-blue-500 font-medium" : "text-slate-400 hover:text-blue-500"}`}
          >
            {editing ? "完成" : "編輯"}
          </button>
        )}
      </div>
      <div className="divide-y divide-slate-100 dark:divide-slate-800">
        {children}
      </div>
      {editing && onAdd && (
        <button
          onClick={onAdd}
          className="mt-3 w-full py-2 text-xs text-blue-500 border border-dashed border-blue-500/30 rounded-lg hover:bg-blue-500/5 cursor-pointer transition-colors"
        >
          + 新增
        </button>
      )}
    </div>
  );
}
