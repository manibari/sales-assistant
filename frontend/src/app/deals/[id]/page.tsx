"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { TopBar } from "@/components/top-bar";
import {
  ChevronLeft,
  Check,
  X,
  AlertTriangle,
  Handshake,
  Zap,
  CircleDot,
  Calendar,
  Loader2,
  Pencil,
  Users,
} from "lucide-react";
import { nxApi, type NxDeal, type NxPartner, type NxIntel, type NxContact, type MeddicProgress } from "@/lib/nexus-api";
import { getIntelDisplayTitle } from "@/lib/intel-display";
import { formatBudget } from "@/lib/options";
import { STAGE_ORDER, STAGE_LABELS } from "@/lib/deal-constants";
import { ContactFormModal } from "@/components/contact-form-modal";
import { DealGantt } from "@/components/deal-gantt";
import { IntelSummaryModal } from "@/components/intel-summary-modal";
import { IntelRow } from "@/components/intel-row";
import { Section } from "@/components/collapsible-section";
import { DealStageStepper } from "@/components/deal-stage-stepper";
import { DealMeddic } from "@/components/deal-meddic";
import { DealCloseModal } from "@/components/deal-close-modal";
import { DealFilesSection } from "@/components/deal-files-section";
import { DealDocumentsSection } from "@/components/deal-documents-section";
import { CreateProjectModal } from "@/components/create-project-modal";
import { Briefcase } from "lucide-react";
import { DealAddPartnerModal } from "@/components/deal-add-partner-modal";
import { DealAddIntelModal } from "@/components/deal-add-intel-modal";
import { DealAddTbdModal } from "@/components/deal-add-tbd-modal";
import { useEditableField } from "@/hooks/use-editable-field";
import { TBD_TEMPLATES } from "@/lib/tbd-templates";
import Link from "next/link";

export default function DealDetailPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const dealId = Number(params.id);

  const fromType = searchParams.get("from");
  const orgId = searchParams.get("orgId");
  const backHref = fromType && orgId ? `/contacts/${fromType}s/${orgId}` : "/deals";

  const [deal, setDeal] = useState<NxDeal | null>(null);
  const [loading, setLoading] = useState(true);
  const [showCloseModal, setShowCloseModal] = useState(false);
  const [advancing, setAdvancing] = useState(false);
  const [showAddPartner, setShowAddPartner] = useState(false);
  const [showAddIntel, setShowAddIntel] = useState(false);
  const [showSummaryModal, setShowSummaryModal] = useState(false);
  const [showAddTbd, setShowAddTbd] = useState(false);
  const [showTbdTemplates, setShowTbdTemplates] = useState(false);
  const [allUsers, setAllUsers] = useState<{ id: number; name: string }[]>([]);
  const [editingOwner, setEditingOwner] = useState(false);
  const [ownerValue, setOwnerValue] = useState<number | null>(null);
  const [editingPresales, setEditingPresales] = useState(false);
  const [presalesValue, setPresalesValue] = useState<number | null>(null);
  const [existingProjectId, setExistingProjectId] = useState<number | null>(null);
  const [showCreateProject, setShowCreateProject] = useState(false);
  const [selectedTemplates, setSelectedTemplates] = useState<Set<string>>(new Set());
  const [addingTemplates, setAddingTemplates] = useState(false);
  const [editingSection, setEditingSection] = useState<string | null>(null);
  const [allPartners, setAllPartners] = useState<NxPartner[]>([]);
  const [allIntels, setAllIntels] = useState<NxIntel[]>([]);
  const [contacts, setContacts] = useState<NxContact[]>([]);
  const [showContactModal, setShowContactModal] = useState(false);
  const [editContact, setEditContact] = useState<NxContact | null>(null);

  const loadDeal = useCallback(() => {
    nxApi.deals
      .get(dealId)
      .then((d) => {
        setDeal(d);
        if (d.client_id) {
          nxApi.contacts.list("client", d.client_id).then(setContacts).catch(console.error);
        }
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [dealId]);

  useEffect(() => { loadDeal(); }, [loadDeal]);
  useEffect(() => { nxApi.deals.listUsers().then(setAllUsers).catch(() => {}); }, []);
  useEffect(() => {
    nxApi.projects
      .getByDeal(dealId)
      .then((p) => setExistingProjectId(p.id))
      .catch(() => setExistingProjectId(null));
  }, [dealId]);

  const { editField, editValue, setEditValue, saving, startEdit, cancelEdit, saveField, handleKeyDown } =
    useEditableField({ dealId, onSaved: loadDeal });

  const handleStageClick = async (targetStage: string) => {
    if (!deal) return;
    const currentIdx = STAGE_ORDER.indexOf(deal.stage);
    const targetIdx = STAGE_ORDER.indexOf(targetStage);
    if (currentIdx < 0 || targetIdx < 0 || currentIdx === targetIdx) return;

    const isForward = targetIdx > currentIdx;
    if (isForward && deal.meddic_progress?.missing.length && currentIdx >= 1) {
      alert(`需先完成 MEDDIC：${deal.meddic_progress.missing.join(", ")}`);
      return;
    }
    if (!isForward && !confirm(`確定要將階段從 ${STAGE_LABELS[deal.stage]} 退回到 ${STAGE_LABELS[targetStage]}？`)) return;

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

  const handleClose = async (reason: string, outcome: "won" | "lost", notes?: string) => {
    try {
      await nxApi.deals.close(dealId, reason, outcome, notes);
      setShowCloseModal(false);
      loadDeal();
    } catch (err) {
      console.error("Failed to close:", err);
    }
  };

  const handleDeleteDeal = async () => {
    if (!deal || !confirm(`確定要刪除商機「${deal.name}」？此操作無法復原，會議、提醒等關聯資料也會一併刪除。`)) return;
    try {
      await nxApi.deals.delete(deal.id);
      router.push("/deals");
    } catch (err) {
      console.error(err);
      alert("刪除失敗");
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

  const progress: MeddicProgress = deal.meddic_progress || { completed: 0, total: 6, missing: [] };
  const isClosed = deal.status === "won" || deal.status === "lost" || deal.status === "closed";
  const isHold = deal.stage === "HOLD";
  const isInactive = isClosed || isHold;

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
        <div className="lg:grid lg:grid-cols-5 lg:gap-6 space-y-4 lg:space-y-0">

          {/* Left column (3/5) — header + MEDDIC */}
          <div className="lg:col-span-3 space-y-4">

            {/* Header card */}
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-5">
              <div className="flex items-center justify-between mb-3">
                <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${isClosed ? "bg-red-500/10 text-red-400" : isHold ? "bg-gray-500/10 text-gray-400" : "bg-blue-500/10 text-blue-400"}`}>
                  {STAGE_LABELS[deal.stage] || deal.stage}
                </span>
                {deal.idle_days !== undefined && deal.idle_days > 0 && !isClosed && (
                  <span className={`text-[11px] flex items-center gap-1 ${deal.idle_days > 14 ? "text-red-400" : "text-slate-400"}`}>
                    {deal.idle_days > 14 && <AlertTriangle size={12} />}
                    {deal.idle_days} 天未動
                  </span>
                )}
              </div>

              {/* Editable deal name */}
              {editField === "name" ? (
                <div className="flex items-center gap-2 mt-1">
                  <input type="text" value={editValue} onChange={(e) => setEditValue(e.target.value)} onKeyDown={handleKeyDown}
                    className="flex-1 bg-slate-100 dark:bg-slate-800 border border-blue-500 rounded-lg px-3 py-1.5 text-lg font-semibold text-slate-900 dark:text-slate-50 focus:ring-1 focus:ring-blue-500 focus:outline-none" autoFocus />
                  <button onClick={saveField} disabled={saving} className="p-1.5 bg-blue-500 text-white rounded-lg cursor-pointer disabled:opacity-50"><Check size={16} /></button>
                  <button onClick={cancelEdit} className="p-1.5 bg-slate-200 dark:bg-slate-700 rounded-lg cursor-pointer"><X size={16} /></button>
                </div>
              ) : (
                <h2 onClick={() => !isClosed && startEdit("name", deal.name)}
                  className={`text-lg font-semibold text-slate-900 dark:text-slate-50 ${!isClosed ? "cursor-pointer hover:text-blue-500 transition-colors" : ""}`}
                  title={!isClosed ? "點擊編輯名稱" : undefined}>
                  {deal.name}
                </h2>
              )}
              <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">{deal.client_name} · {deal.client_industry || "—"}</p>

              {/* Owner + Presales */}
              <div className="flex items-center gap-3 mt-1.5 flex-wrap">
                {/* 業務 */}
                <div className="flex items-center gap-1.5">
                  <Users size={12} className="text-slate-400 flex-shrink-0" />
                  {editingOwner ? (
                    <div className="flex items-center gap-1">
                      <select
                        value={ownerValue ?? ""}
                        onChange={(e) => setOwnerValue(e.target.value ? Number(e.target.value) : null)}
                        autoFocus
                        className="text-xs bg-slate-100 dark:bg-slate-800 border border-blue-500 rounded px-2 py-0.5 text-slate-900 dark:text-slate-50 focus:outline-none"
                      >
                        <option value="">未指定</option>
                        {allUsers.map((u) => (
                          <option key={u.id} value={u.id}>{u.name}</option>
                        ))}
                      </select>
                      <button
                        onClick={async () => {
                          await nxApi.deals.update(dealId, { owner_id: ownerValue } as Partial<NxDeal>);
                          setEditingOwner(false);
                          loadDeal();
                        }}
                        className="p-0.5 text-blue-500 cursor-pointer"
                      ><Check size={12} /></button>
                      <button onClick={() => setEditingOwner(false)} className="p-0.5 text-slate-400 cursor-pointer"><X size={12} /></button>
                    </div>
                  ) : (
                    <span
                      onClick={() => { if (!isClosed) { setOwnerValue(deal.owner_id ?? null); setEditingOwner(true); } }}
                      className={`text-xs ${isClosed ? "text-slate-400" : "text-slate-400 cursor-pointer hover:text-blue-400 transition-colors"}`}
                      title={!isClosed ? "點擊指定業務" : undefined}
                    >
                      業務：{deal.owner_name ?? "未指定"}
                    </span>
                  )}
                </div>

                {/* 技術業務 */}
                <div className="flex items-center gap-1.5">
                  {editingPresales ? (
                    <div className="flex items-center gap-1">
                      <select
                        value={presalesValue ?? ""}
                        onChange={(e) => setPresalesValue(e.target.value ? Number(e.target.value) : null)}
                        autoFocus
                        className="text-xs bg-slate-100 dark:bg-slate-800 border border-blue-500 rounded px-2 py-0.5 text-slate-900 dark:text-slate-50 focus:outline-none"
                      >
                        <option value="">未指定</option>
                        {allUsers.map((u) => (
                          <option key={u.id} value={u.id}>{u.name}</option>
                        ))}
                      </select>
                      <button
                        onClick={async () => {
                          await nxApi.deals.update(dealId, { presales_id: presalesValue } as Partial<NxDeal>);
                          setEditingPresales(false);
                          loadDeal();
                        }}
                        className="p-0.5 text-blue-500 cursor-pointer"
                      ><Check size={12} /></button>
                      <button onClick={() => setEditingPresales(false)} className="p-0.5 text-slate-400 cursor-pointer"><X size={12} /></button>
                    </div>
                  ) : (
                    <span
                      onClick={() => { if (!isClosed) { setPresalesValue(deal.presales_id ?? null); setEditingPresales(true); } }}
                      className={`text-xs ${isClosed ? "text-slate-400" : "text-slate-400 cursor-pointer hover:text-blue-400 transition-colors"}`}
                      title={!isClosed ? "點擊指定技術業務" : undefined}
                    >
                      技術：{deal.presales_name ?? "未指定"}
                    </span>
                  )}
                </div>
              </div>

              {/* Editable budget & timeline */}
              <div className="flex gap-4 mt-3 text-xs text-slate-400 dark:text-slate-500">
                {editField === "budget_amount" ? (
                  <div className="flex items-center gap-1">
                    <span>預算:</span>
                    <input type="number" value={editValue} onChange={(e) => setEditValue(e.target.value)} onKeyDown={handleKeyDown} placeholder="金額 (元)"
                      className="w-28 bg-slate-100 dark:bg-slate-800 border border-blue-500 rounded px-2 py-0.5 text-xs text-slate-900 dark:text-slate-50 focus:outline-none" autoFocus />
                    <button onClick={saveField} disabled={saving} className="p-0.5 text-blue-500 cursor-pointer"><Check size={12} /></button>
                    <button onClick={cancelEdit} className="p-0.5 text-slate-400 cursor-pointer"><X size={12} /></button>
                  </div>
                ) : (
                  <span onClick={() => !isClosed && startEdit("budget_amount", String(deal.budget_amount || ""))}
                    className={!isClosed ? "cursor-pointer hover:text-blue-400 transition-colors" : ""}
                    title={!isClosed ? "點擊編輯預算" : undefined}>
                    預算: {formatBudget(deal.budget_amount)}
                  </span>
                )}
                {editField === "timeline" ? (
                  <div className="flex items-center gap-1">
                    <span>時程:</span>
                    <input type="text" value={editValue} onChange={(e) => setEditValue(e.target.value)} onKeyDown={handleKeyDown}
                      className="w-28 bg-slate-100 dark:bg-slate-800 border border-blue-500 rounded px-2 py-0.5 text-xs text-slate-900 dark:text-slate-50 focus:outline-none" autoFocus />
                    <button onClick={saveField} disabled={saving} className="p-0.5 text-blue-500 cursor-pointer"><Check size={12} /></button>
                    <button onClick={cancelEdit} className="p-0.5 text-slate-400 cursor-pointer"><X size={12} /></button>
                  </div>
                ) : (
                  <span onClick={() => !isClosed && startEdit("timeline", deal.timeline || "")}
                    className={!isClosed ? "cursor-pointer hover:text-blue-400 transition-colors" : ""}
                    title={!isClosed ? "點擊編輯時程" : undefined}>
                    時程: {deal.timeline || "—"}
                  </span>
                )}
              </div>

              {/* Reopen closed deal */}
              {isClosed && (
                <div className="mt-4">
                  <p className="text-xs text-slate-400 mb-2">關閉原因: {deal.close_reason || "—"}{deal.close_notes ? ` — ${deal.close_notes}` : ""}</p>
                  <button onClick={async () => {
                    if (!confirm("確定要重新開啟此商機？將回到 L0 階段。")) return;
                    setAdvancing(true);
                    try {
                      await nxApi.deals.update(dealId, { status: "active", stage: "L0" } as Partial<NxDeal>);
                      loadDeal();
                    } catch (err) { console.error("Failed to reopen:", err); } finally { setAdvancing(false); }
                  }} disabled={advancing}
                    className="w-full bg-blue-500 hover:bg-blue-600 text-white font-semibold px-4 py-2.5 rounded-lg text-sm min-h-[44px] active:scale-[0.98] transition-all cursor-pointer disabled:opacity-50">
                    {advancing ? "處理中..." : "重新開啟案件"}
                  </button>
                </div>
              )}

              {/* Resume held deal */}
              {isHold && !isClosed && (
                <div className="mt-4">
                  {deal.close_notes && <p className="text-xs text-slate-400 mb-2">擱置備註: {deal.close_notes}</p>}
                  <button onClick={async () => {
                    if (!confirm("確定要解除擱置？將回到 L0 階段。")) return;
                    setAdvancing(true);
                    try {
                      await nxApi.deals.unhold(dealId, "L0");
                      loadDeal();
                    } catch (err) { console.error("Failed to unhold:", err); } finally { setAdvancing(false); }
                  }} disabled={advancing}
                    className="w-full bg-blue-500 hover:bg-blue-600 text-white font-semibold px-4 py-2.5 rounded-lg text-sm min-h-[44px] active:scale-[0.98] transition-all cursor-pointer disabled:opacity-50">
                    {advancing ? "處理中..." : "解除擱置"}
                  </button>
                </div>
              )}

              {/* Stage stepper */}
              {!isInactive && (
                <DealStageStepper
                  currentStage={deal.stage}
                  advancing={advancing}
                  onStageClick={handleStageClick}
                  onClose={() => setShowCloseModal(true)}
                  onHold={async () => {
                    const notes = prompt("擱置備註（可留空）：");
                    if (notes === null) return;
                    setAdvancing(true);
                    try {
                      await nxApi.deals.hold(dealId, notes || undefined);
                      loadDeal();
                    } catch (err) { console.error("Failed to hold:", err); } finally { setAdvancing(false); }
                  }}
                  onDelete={handleDeleteDeal}
                />
              )}
            </div>

            {/* Deal Gantt */}
            {deal.created_at && (
              <DealGantt dealId={dealId} dealCreatedAt={deal.created_at} currentStage={deal.stage} onDealUpdated={loadDeal} />
            )}

            {/* MEDDIC Progress */}
            <DealMeddic dealId={dealId} meddicJson={deal.meddic_json} progress={progress} isClosed={isClosed} onUpdated={loadDeal} />
          </div>

          {/* Right column (2/5) — related data */}
          <div className="lg:col-span-2 space-y-4">

            {/* Partners */}
            <Section
              title="搭配夥伴" icon={<Handshake size={16} className="text-green-500" />} count={deal.partners?.length}
              editing={editingSection === "partners"}
              onToggleEdit={!isClosed ? () => setEditingSection(editingSection === "partners" ? null : "partners") : undefined}
              onAdd={editingSection === "partners" ? async () => {
                setShowAddPartner(true);
                try { setAllPartners(await nxApi.partners.list()); } catch (err) { console.error(err); }
              } : undefined}
            >
              {deal.partners && deal.partners.length > 0 ? (
                deal.partners.map((p) => (
                  <div key={p.id} className="flex items-center justify-between py-2">
                    <div className="flex-1 min-w-0">
                      <span className="text-sm text-slate-900 dark:text-slate-50">{p.partner_name}</span>
                      {p.role && <span className="text-xs text-slate-400 ml-2">({p.role})</span>}
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-[11px] px-2 py-0.5 rounded-full bg-green-500/10 text-green-400">{p.trust_level}</span>
                      {editingSection === "partners" && (
                        <button onClick={async () => {
                          if (!confirm(`確定移除「${p.partner_name}」？`)) return;
                          try { await nxApi.deals.removePartner(dealId, p.partner_id); loadDeal(); } catch (err) { console.error(err); }
                        }} className="p-1 text-red-400 hover:text-red-500 hover:bg-red-500/10 rounded cursor-pointer transition-colors">
                          <X size={14} />
                        </button>
                      )}
                    </div>
                  </div>
                ))
              ) : <p className="text-xs text-slate-400">尚無配對夥伴</p>}
            </Section>

            {/* Contacts */}
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Users size={16} className="text-violet-500" />
                  <span className="text-sm font-semibold text-slate-900 dark:text-slate-50">關鍵人物</span>
                  <span className="text-xs text-slate-400">({contacts.length})</span>
                </div>
                {!isClosed && <button onClick={() => setShowContactModal(true)} className="text-xs text-blue-500 cursor-pointer">+ 新增</button>}
              </div>
              <div className="divide-y divide-slate-100 dark:divide-slate-800">
                {contacts.length > 0 ? (
                  contacts.map((c) => (
                    <div key={c.id} onClick={() => setEditContact(c)} className="py-2 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800/50 -mx-1 px-1 rounded transition-colors">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-slate-900 dark:text-slate-50">{c.name}</span>
                        <div className="flex items-center gap-1.5">
                          {c.role && <span className="text-[11px] px-2 py-0.5 rounded-full bg-violet-500/10 text-violet-400">{c.role}</span>}
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
                ) : <p className="text-xs text-slate-400 py-2">尚無聯絡人</p>}
              </div>
            </div>

            {/* Related Intel */}
            <Section
              title="相關情報" icon={<Zap size={16} className="text-cyan-500" />} count={deal.intel?.length}
              editing={editingSection === "intel"}
              onToggleEdit={!isClosed ? () => setEditingSection(editingSection === "intel" ? null : "intel") : undefined}
              onAdd={editingSection === "intel" ? async () => {
                setShowAddIntel(true);
                try { setAllIntels(await nxApi.intel.list()); } catch (err) { console.error(err); }
              } : undefined}
            >
              {deal.intel && deal.intel.length > 0 ? (
                deal.intel.map((i) => {
                  const ii = i as unknown as { id: number; intel_id?: number; raw_input: string; intel_created_at?: string };
                  const realId = ii.intel_id ?? ii.id;
                  return (
                    <IntelRow key={realId} intelId={realId} title={getIntelDisplayTitle(i, 80)} date={ii.intel_created_at}
                      editing={editingSection === "intel"}
                      onUnlink={async () => {
                        if (!confirm("確定取消關聯此情報？")) return;
                        try { await nxApi.deals.unlinkIntel(dealId, realId); loadDeal(); } catch (err) { console.error(err); }
                      }}
                      onTitleSaved={loadDeal} />
                  );
                })
              ) : <p className="text-xs text-slate-400">尚無關聯情報</p>}
              {deal.intel && deal.intel.length >= 2 && (
                <button onClick={() => setShowSummaryModal(true)}
                  className="mt-2 w-full py-2 text-xs font-medium text-cyan-500 hover:text-cyan-400 hover:bg-cyan-500/5 rounded-lg cursor-pointer transition-colors">
                  彙整 {deal.intel.length} 筆情報
                </button>
              )}
            </Section>

            {/* TBDs */}
            <Section
              title="TBD 清單" icon={<CircleDot size={16} className="text-amber-500" />} count={deal.tbds?.length}
              editing={editingSection === "tbds"}
              onToggleEdit={!isClosed ? () => {
                setEditingSection(editingSection === "tbds" ? null : "tbds");
                setShowTbdTemplates(false);
              } : undefined}
              onAdd={editingSection === "tbds" ? () => setShowAddTbd(true) : undefined}
            >
              {/* Stage-based template panel */}
              {editingSection === "tbds" && TBD_TEMPLATES[deal.stage] && (
                <div className="mb-3">
                  <button
                    onClick={() => {
                      if (!showTbdTemplates) {
                        // Pre-select all templates not already in TBD list
                        const existing = new Set((deal.tbds ?? []).map((t) => t.question));
                        const available = TBD_TEMPLATES[deal.stage].filter((q) => !existing.has(q));
                        setSelectedTemplates(new Set(available));
                      }
                      setShowTbdTemplates((v) => !v);
                    }}
                    className="text-xs text-amber-500 hover:text-amber-600 font-medium cursor-pointer flex items-center gap-1"
                  >
                    <CircleDot size={12} />
                    {showTbdTemplates ? "收起範本" : `從 ${deal.stage} 範本新增`}
                  </button>
                  {showTbdTemplates && (
                    <div className="mt-2 border border-amber-500/20 rounded-lg bg-amber-500/5 p-3 space-y-2">
                      {TBD_TEMPLATES[deal.stage].map((q) => {
                        const alreadyExists = (deal.tbds ?? []).some((t) => t.question === q);
                        const checked = selectedTemplates.has(q);
                        return (
                          <label key={q} className={`flex items-center gap-2 cursor-pointer ${alreadyExists ? "opacity-40" : ""}`}>
                            <input
                              type="checkbox"
                              checked={checked && !alreadyExists}
                              disabled={alreadyExists}
                              onChange={() => {
                                setSelectedTemplates((prev) => {
                                  const next = new Set(prev);
                                  if (next.has(q)) next.delete(q); else next.add(q);
                                  return next;
                                });
                              }}
                              className="rounded border-slate-300 text-amber-500 focus:ring-amber-500"
                            />
                            <span className="text-xs text-slate-700 dark:text-slate-300">{q}</span>
                            {alreadyExists && <span className="text-[10px] text-slate-400">已存在</span>}
                          </label>
                        );
                      })}
                      <button
                        disabled={selectedTemplates.size === 0 || addingTemplates}
                        onClick={async () => {
                          setAddingTemplates(true);
                          for (const q of selectedTemplates) {
                            if (!(deal.tbds ?? []).some((t) => t.question === q)) {
                              await nxApi.tbd.create({ question: q, linked_type: "deal", linked_id: dealId, source: "template" });
                            }
                          }
                          setAddingTemplates(false);
                          setShowTbdTemplates(false);
                          setSelectedTemplates(new Set());
                          loadDeal();
                        }}
                        className="mt-1 w-full py-1.5 text-xs font-medium bg-amber-500 hover:bg-amber-600 disabled:opacity-50 text-white rounded-lg cursor-pointer transition-colors"
                      >
                        {addingTemplates ? "加入中..." : `加入已選取（${selectedTemplates.size} 項）`}
                      </button>
                    </div>
                  )}
                </div>
              )}
              {deal.tbds && deal.tbds.length > 0 ? (
                deal.tbds.map((t) => (
                  <div key={t.id} className="flex items-center justify-between py-2">
                    <span className="text-sm text-slate-700 dark:text-slate-300">{t.question}</span>
                    <button onClick={async () => { await nxApi.tbd.resolve(t.id); loadDeal(); }} className="text-xs text-green-500 cursor-pointer">解決</button>
                  </div>
                ))
              ) : <p className="text-xs text-slate-400">無待確認事項</p>}
            </Section>

            {/* Deal Documents (RFQ/Quote/SOW/PO) */}
            {deal.client_id && (
              <DealDocumentsSection
                dealId={dealId}
                clientId={deal.client_id}
                isClosed={isClosed}
              />
            )}

            {/* Files */}
            <DealFilesSection deal={deal} dealId={dealId} isClosed={isClosed} onUpdated={loadDeal} />

            {/* Won deal → create / view delivery project */}
            {(deal.status === "won" || (deal.status === "closed" && (deal as { outcome?: string }).outcome === "won")) && (
              existingProjectId ? (
                <Link
                  href={`/projects/${existingProjectId}`}
                  className="flex items-center gap-3 bg-white dark:bg-slate-900 border border-indigo-500/30 rounded-xl p-4 cursor-pointer hover:border-indigo-500/60 transition-colors"
                >
                  <Briefcase size={20} className="text-indigo-500" />
                  <span className="text-sm font-medium text-slate-900 dark:text-slate-50">
                    前往交付專案
                  </span>
                </Link>
              ) : (
                <button
                  onClick={() => setShowCreateProject(true)}
                  className="w-full flex items-center gap-3 bg-white dark:bg-slate-900 border border-dashed border-indigo-500/40 rounded-xl p-4 cursor-pointer hover:border-indigo-500 hover:bg-indigo-500/5 transition-colors"
                >
                  <Briefcase size={20} className="text-indigo-500" />
                  <span className="text-sm font-medium text-slate-900 dark:text-slate-50">
                    建立交付專案
                  </span>
                </button>
              )
            )}

            {/* Next action */}
            {!isClosed && (
              <Link href="/calendar"
                className="flex items-center gap-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4 cursor-pointer hover:border-slate-300 dark:hover:border-slate-600 transition-colors">
                <Calendar size={20} className="text-blue-500" />
                <span className="text-sm font-medium text-slate-900 dark:text-slate-50">排下次會議</span>
              </Link>
            )}
          </div>
        </div>
      </div>

      {/* Modals */}
      {showAddPartner && deal && (
        <DealAddPartnerModal dealId={dealId} deal={deal} allPartners={allPartners}
          onClose={() => { setShowAddPartner(false); }} onAdded={loadDeal} />
      )}
      {showAddIntel && deal && (
        <DealAddIntelModal dealId={dealId} deal={deal} allIntels={allIntels}
          onClose={() => setShowAddIntel(false)} onLinked={loadDeal} />
      )}
      {showAddTbd && (
        <DealAddTbdModal dealId={dealId} onClose={() => setShowAddTbd(false)} onCreated={loadDeal} />
      )}
      {showCreateProject && deal && (
        <CreateProjectModal
          dealId={dealId}
          defaultName={deal.name}
          onClose={() => setShowCreateProject(false)}
        />
      )}
      {showSummaryModal && deal?.intel && (
        <IntelSummaryModal
          intelIds={deal.intel.map((i) => { const ii = i as unknown as { intel_id?: number }; return ii.intel_id ?? i.id; })}
          onClose={() => setShowSummaryModal(false)}
          onSaveAsIntel={async (summary) => {
            const newIntel = await nxApi.intel.create({ raw_input: summary, input_type: "text" });
            await nxApi.deals.linkIntel(dealId, newIntel.id);
            await nxApi.intel.update(newIntel.id, { title: `${deal.name} 情報彙整`, status: "confirmed" });
            loadDeal();
          }}
        />
      )}
      {showContactModal && deal && (
        <ContactFormModal orgType="client" orgId={deal.client_id} onClose={() => setShowContactModal(false)} onCreated={loadDeal} />
      )}
      {editContact && deal && (
        <ContactFormModal orgType="client" orgId={deal.client_id} contact={editContact} onClose={() => setEditContact(null)} onCreated={loadDeal} />
      )}
      {showCloseModal && (
        <DealCloseModal onClose={() => setShowCloseModal(false)} onConfirm={handleClose} />
      )}
    </div>
  );
}
