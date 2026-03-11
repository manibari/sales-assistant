"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { TopBar } from "@/components/top-bar";
import {
  ChevronLeft,
  Check,
  X,
  Loader2,
  Pencil,
  ExternalLink,
  Zap,
  TrendingUp,
} from "lucide-react";
import { nxApi, type NxSubsidy, type NxClient, type NxPartner, type NxDeal } from "@/lib/nexus-api";
import Link from "next/link";

const STAGE_ORDER = [
  "draft", "evaluating", "applying", "under_review",
  "approved", "rejected", "executing", "completed",
];

const STAGE_LABELS: Record<string, string> = {
  draft: "草稿",
  evaluating: "評估中",
  applying: "申請中",
  under_review: "審查中",
  approved: "核定",
  rejected: "未通過",
  executing: "執行中",
  completed: "結案",
};

const STAGE_COLORS: Record<string, string> = {
  draft: "bg-slate-400",
  evaluating: "bg-blue-400",
  applying: "bg-cyan-400",
  under_review: "bg-amber-400",
  approved: "bg-green-500",
  rejected: "bg-red-500",
  executing: "bg-purple-400",
  completed: "bg-slate-500",
};

const TYPE_OPTIONS = [
  { label: "SBIR", value: "sbir" },
  { label: "SIIR", value: "siir" },
  { label: "地方型", value: "local" },
  { label: "其他", value: "other" },
];

export default function SubsidyDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = Number(params.id);

  const [subsidy, setSubsidy] = useState<NxSubsidy | null>(null);
  const [loading, setLoading] = useState(true);
  const [editField, setEditField] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");
  const [saving, setSaving] = useState(false);

  // For linking deals
  const [allDeals, setAllDeals] = useState<NxDeal[]>([]);
  const [showLinkDeal, setShowLinkDeal] = useState(false);

  // For client/partner selector
  const [clients, setClients] = useState<NxClient[]>([]);
  const [partners, setPartners] = useState<NxPartner[]>([]);

  const load = useCallback(() => {
    nxApi.subsidies.get(id).then(setSubsidy).catch(console.error).finally(() => setLoading(false));
  }, [id]);

  useEffect(() => {
    load();
    nxApi.clients.list().then(setClients).catch(console.error);
    nxApi.partners.list().then(setPartners).catch(console.error);
  }, [load]);

  const handleSave = async (field: string, value: string) => {
    setSaving(true);
    try {
      const updated = await nxApi.subsidies.update(id, { [field]: value || null } as Partial<NxSubsidy>);
      setSubsidy((prev) => (prev ? { ...prev, ...updated } : prev));
    } catch (err) {
      console.error("Save failed:", err);
    }
    setSaving(false);
    setEditField(null);
  };

  const handleAdvance = async (stage: string) => {
    try {
      const updated = await nxApi.subsidies.advance(id, stage);
      setSubsidy((prev) => (prev ? { ...prev, ...updated } : prev));
    } catch (err) {
      console.error("Advance failed:", err);
    }
  };

  const handleLinkDeal = async (dealId: number) => {
    try {
      await nxApi.subsidies.linkDeal(id, dealId);
      load();
      setShowLinkDeal(false);
    } catch (err) {
      console.error("Link deal failed:", err);
    }
  };

  const handleUnlinkDeal = async (dealId: number) => {
    try {
      await nxApi.subsidies.unlinkDeal(id, dealId);
      load();
    } catch (err) {
      console.error("Unlink deal failed:", err);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 size={24} className="animate-spin text-blue-500" />
      </div>
    );
  }

  if (!subsidy) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-slate-400">
        <p>找不到補助案</p>
        <Link href="/subsidies" className="text-blue-500 mt-2 text-sm">
          返回列表
        </Link>
      </div>
    );
  }

  const linkedDealIds = new Set((subsidy.deals || []).map((d) => d.deal_id));

  return (
    <div className="flex flex-col h-full">
      <TopBar title={subsidy.name}>
        <Link
          href="/subsidies"
          className="p-2 rounded-lg text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer transition-colors"
        >
          <ChevronLeft size={20} />
        </Link>
      </TopBar>

      <div className="flex-1 px-4 lg:px-6 py-4 overflow-auto">
        <div className="max-w-5xl mx-auto lg:grid lg:grid-cols-5 lg:gap-6">
          {/* Left column 3/5 */}
          <div className="lg:col-span-3 space-y-6">
            {/* Stage pipeline */}
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4">
              <div className="flex gap-1">
                {STAGE_ORDER.map((stage) => {
                  const isCurrent = subsidy.stage === stage;
                  const currentIdx = STAGE_ORDER.indexOf(subsidy.stage);
                  const stageIdx = STAGE_ORDER.indexOf(stage);
                  const isPast = stageIdx < currentIdx;
                  return (
                    <button
                      key={stage}
                      onClick={() => handleAdvance(stage)}
                      className={`flex-1 py-2 text-[10px] font-medium rounded transition-colors cursor-pointer ${
                        isCurrent
                          ? `${STAGE_COLORS[stage]} text-white`
                          : isPast
                            ? "bg-slate-200 dark:bg-slate-700 text-slate-500 dark:text-slate-400"
                            : "bg-slate-100 dark:bg-slate-800 text-slate-400 dark:text-slate-500 hover:bg-slate-200 dark:hover:bg-slate-700"
                      }`}
                      title={STAGE_LABELS[stage]}
                    >
                      {STAGE_LABELS[stage]}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Editable fields */}
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4 space-y-4">
              <EditableField
                label="名稱"
                value={subsidy.name}
                field="name"
                editField={editField}
                editValue={editValue}
                saving={saving}
                onEdit={(f, v) => { setEditField(f); setEditValue(v); }}
                onSave={handleSave}
                onCancel={() => setEditField(null)}
                setEditValue={setEditValue}
              />
              <EditableField label="來源" value={subsidy.source} field="source" editField={editField} editValue={editValue} saving={saving} onEdit={(f, v) => { setEditField(f); setEditValue(v); }} onSave={handleSave} onCancel={() => setEditField(null)} setEditValue={setEditValue} />
              <EditableField label="主辦機關" value={subsidy.agency} field="agency" editField={editField} editValue={editValue} saving={saving} onEdit={(f, v) => { setEditField(f); setEditValue(v); }} onSave={handleSave} onCancel={() => setEditField(null)} setEditValue={setEditValue} />

              {/* program_type select */}
              <div>
                <label className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-1 block">計畫類型</label>
                <select
                  value={subsidy.program_type}
                  onChange={(e) => handleSave("program_type", e.target.value)}
                  className="w-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-900 dark:text-slate-50 focus:border-blue-500 focus:outline-none transition-colors"
                >
                  {TYPE_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>

              {/* Deadline with countdown */}
              <div>
                <label className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-1 block">截止日（計算用）</label>
                {editField === "deadline_date" ? (
                  <div className="flex gap-2">
                    <input type="date" value={editValue} onChange={(e) => setEditValue(e.target.value)} className="flex-1 bg-slate-100 dark:bg-slate-800 border border-blue-500 rounded-lg px-3 py-2 text-sm text-slate-900 dark:text-slate-50 focus:outline-none" autoFocus />
                    <button onClick={() => handleSave("deadline_date", editValue)} disabled={saving} className="p-2 text-green-500 hover:bg-green-500/10 rounded-lg cursor-pointer"><Check size={16} /></button>
                    <button onClick={() => setEditField(null)} className="p-2 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg cursor-pointer"><X size={16} /></button>
                  </div>
                ) : (
                  <div className="flex items-center gap-2 group">
                    {subsidy.deadline_date ? (
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-slate-900 dark:text-slate-50">{subsidy.deadline_date}</span>
                        {subsidy.days_left != null && subsidy.days_left >= 0 && (
                          <span className={`text-xs px-2 py-0.5 rounded-full font-bold ${
                            subsidy.days_left <= 14 ? "bg-red-500 text-white" :
                            subsidy.days_left <= 30 ? "bg-red-500/15 text-red-500" :
                            subsidy.days_left <= 60 ? "bg-amber-500/15 text-amber-500" :
                            "bg-green-500/10 text-green-500"
                          }`}>
                            {subsidy.days_left === 0 ? "今天截止" : `剩 ${subsidy.days_left} 天`}
                          </span>
                        )}
                        {subsidy.days_left != null && subsidy.days_left < 0 && (
                          <span className="text-xs px-2 py-0.5 rounded-full bg-slate-500/10 text-slate-400">已截止</span>
                        )}
                      </div>
                    ) : (
                      <span className="text-sm text-slate-400">—</span>
                    )}
                    <button onClick={() => { setEditField("deadline_date"); setEditValue(subsidy.deadline_date || ""); }} className="opacity-0 group-hover:opacity-100 p-1 text-slate-400 hover:text-blue-500 cursor-pointer transition-opacity"><Pencil size={14} /></button>
                  </div>
                )}
              </div>
              <EditableField label="截止日（原始說明）" value={subsidy.deadline} field="deadline" editField={editField} editValue={editValue} saving={saving} onEdit={(f, v) => { setEditField(f); setEditValue(v); }} onSave={handleSave} onCancel={() => setEditField(null)} setEditValue={setEditValue} />
              <EditableField label="補助額度" value={subsidy.funding_amount} field="funding_amount" editField={editField} editValue={editValue} saving={saving} onEdit={(f, v) => { setEditField(f); setEditValue(v); }} onSave={handleSave} onCancel={() => setEditField(null)} setEditValue={setEditValue} />
              <EditableField label="申請資格" value={subsidy.eligibility} field="eligibility" multiline editField={editField} editValue={editValue} saving={saving} onEdit={(f, v) => { setEditField(f); setEditValue(v); }} onSave={handleSave} onCancel={() => setEditField(null)} setEditValue={setEditValue} />
              <EditableField label="申請範疇" value={subsidy.scope} field="scope" multiline editField={editField} editValue={editValue} saving={saving} onEdit={(f, v) => { setEditField(f); setEditValue(v); }} onSave={handleSave} onCancel={() => setEditField(null)} setEditValue={setEditValue} />
              <EditableField label="申請文件" value={subsidy.required_docs} field="required_docs" multiline editField={editField} editValue={editValue} saving={saving} onEdit={(f, v) => { setEditField(f); setEditValue(v); }} onSave={handleSave} onCancel={() => setEditField(null)} setEditValue={setEditValue} />

              {/* Reference URL */}
              <div>
                <label className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-1 block">參考連結</label>
                {editField === "reference_url" ? (
                  <div className="flex gap-2">
                    <input
                      type="url"
                      value={editValue}
                      onChange={(e) => setEditValue(e.target.value)}
                      className="flex-1 bg-slate-100 dark:bg-slate-800 border border-blue-500 rounded-lg px-3 py-2 text-sm text-slate-900 dark:text-slate-50 focus:outline-none"
                      autoFocus
                    />
                    <button onClick={() => handleSave("reference_url", editValue)} disabled={saving} className="p-2 text-green-500 hover:bg-green-500/10 rounded-lg cursor-pointer"><Check size={16} /></button>
                    <button onClick={() => setEditField(null)} className="p-2 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg cursor-pointer"><X size={16} /></button>
                  </div>
                ) : (
                  <div className="flex items-center gap-2 group">
                    {subsidy.reference_url ? (
                      <a href={subsidy.reference_url} target="_blank" rel="noopener noreferrer" className="text-sm text-blue-500 hover:underline truncate flex items-center gap-1">
                        {subsidy.reference_url} <ExternalLink size={12} />
                      </a>
                    ) : (
                      <span className="text-sm text-slate-400">—</span>
                    )}
                    <button onClick={() => { setEditField("reference_url"); setEditValue(subsidy.reference_url || ""); }} className="opacity-0 group-hover:opacity-100 p-1 text-slate-400 hover:text-blue-500 cursor-pointer transition-opacity"><Pencil size={14} /></button>
                  </div>
                )}
              </div>

              <EditableField label="備註" value={subsidy.notes} field="notes" multiline editField={editField} editValue={editValue} saving={saving} onEdit={(f, v) => { setEditField(f); setEditValue(v); }} onSave={handleSave} onCancel={() => setEditField(null)} setEditValue={setEditValue} />

              {/* Client selector */}
              <div>
                <label className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-1 block">關聯客戶</label>
                <select
                  value={subsidy.client_id ?? ""}
                  onChange={(e) => handleSave("client_id", e.target.value)}
                  className="w-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-900 dark:text-slate-50 focus:border-blue-500 focus:outline-none transition-colors"
                >
                  <option value="">無</option>
                  {clients.map((c) => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
              </div>

              {/* Partner selector */}
              <div>
                <label className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-1 block">關聯夥伴</label>
                <select
                  value={subsidy.partner_id ?? ""}
                  onChange={(e) => handleSave("partner_id", e.target.value)}
                  className="w-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-900 dark:text-slate-50 focus:border-blue-500 focus:outline-none transition-colors"
                >
                  <option value="">無</option>
                  {partners.map((p) => (
                    <option key={p.id} value={p.id}>{p.name}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Right column 2/5 */}
          <div className="lg:col-span-2 space-y-4 mt-6 lg:mt-0">
            {/* Linked deals */}
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-50 flex items-center gap-2">
                  <TrendingUp size={16} /> 關聯商機
                </h3>
                <button
                  onClick={() => {
                    if (!showLinkDeal) nxApi.deals.list().then(setAllDeals).catch(console.error);
                    setShowLinkDeal(!showLinkDeal);
                  }}
                  className="text-xs text-blue-500 hover:underline cursor-pointer"
                >
                  {showLinkDeal ? "取消" : "連結"}
                </button>
              </div>
              {showLinkDeal && (
                <div className="mb-3 max-h-40 overflow-auto border border-slate-200 dark:border-slate-700 rounded-lg">
                  {allDeals.filter((d) => !linkedDealIds.has(d.id)).map((d) => (
                    <button
                      key={d.id}
                      onClick={() => handleLinkDeal(d.id)}
                      className="w-full text-left px-3 py-2 text-sm hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer border-b border-slate-100 dark:border-slate-800 last:border-b-0"
                    >
                      {d.name} <span className="text-xs text-slate-400">({d.client_name})</span>
                    </button>
                  ))}
                </div>
              )}
              {(subsidy.deals || []).length === 0 ? (
                <p className="text-xs text-slate-400">尚無關聯商機</p>
              ) : (
                <div className="space-y-2">
                  {(subsidy.deals || []).map((d) => (
                    <div key={d.deal_id} className="flex items-center justify-between gap-2 px-3 py-2 bg-slate-50 dark:bg-slate-800 rounded-lg">
                      <Link href={`/deals/${d.deal_id}`} className="text-sm text-blue-500 hover:underline truncate">
                        {d.deal_name}
                      </Link>
                      <button onClick={() => handleUnlinkDeal(d.deal_id)} className="text-xs text-red-400 hover:text-red-500 cursor-pointer">
                        <X size={14} />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Related intel */}
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4">
              <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-50 flex items-center gap-2 mb-3">
                <Zap size={16} /> 相關情報
              </h3>
              {(subsidy.intel || []).length === 0 ? (
                <p className="text-xs text-slate-400">無相關情報</p>
              ) : (
                <div className="space-y-2">
                  {(subsidy.intel || []).map((i) => (
                    <Link
                      key={i.id}
                      href={`/intel/${i.id}`}
                      className="block px-3 py-2 bg-slate-50 dark:bg-slate-800 rounded-lg text-sm text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors truncate"
                    >
                      #{i.id} {i.raw_input.slice(0, 60)}
                    </Link>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function EditableField({
  label,
  value,
  field,
  inputType = "text",
  multiline = false,
  editField,
  editValue,
  saving,
  onEdit,
  onSave,
  onCancel,
  setEditValue,
}: {
  label: string;
  value: string | null;
  field: string;
  inputType?: string;
  multiline?: boolean;
  editField: string | null;
  editValue: string;
  saving: boolean;
  onEdit: (field: string, value: string) => void;
  onSave: (field: string, value: string) => void;
  onCancel: () => void;
  setEditValue: (v: string) => void;
}) {
  const isEditing = editField === field;

  if (isEditing) {
    return (
      <div>
        <label className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-1 block">{label}</label>
        <div className="flex gap-2">
          {multiline ? (
            <textarea
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              rows={3}
              className="flex-1 bg-slate-100 dark:bg-slate-800 border border-blue-500 rounded-lg px-3 py-2 text-sm text-slate-900 dark:text-slate-50 focus:outline-none resize-none"
              autoFocus
            />
          ) : (
            <input
              type={inputType}
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              className="flex-1 bg-slate-100 dark:bg-slate-800 border border-blue-500 rounded-lg px-3 py-2 text-sm text-slate-900 dark:text-slate-50 focus:outline-none"
              autoFocus
              onKeyDown={(e) => { if (e.key === "Enter") onSave(field, editValue); if (e.key === "Escape") onCancel(); }}
            />
          )}
          <button onClick={() => onSave(field, editValue)} disabled={saving} className="p-2 text-green-500 hover:bg-green-500/10 rounded-lg cursor-pointer"><Check size={16} /></button>
          <button onClick={onCancel} className="p-2 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg cursor-pointer"><X size={16} /></button>
        </div>
      </div>
    );
  }

  return (
    <div>
      <label className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-1 block">{label}</label>
      <div className="flex items-start gap-2 group">
        <p className={`text-sm flex-1 ${value ? "text-slate-900 dark:text-slate-50" : "text-slate-400"} ${multiline ? "whitespace-pre-wrap" : ""}`}>
          {value || "—"}
        </p>
        <button
          onClick={() => onEdit(field, value || "")}
          className="opacity-0 group-hover:opacity-100 p-1 text-slate-400 hover:text-blue-500 cursor-pointer transition-opacity flex-shrink-0"
        >
          <Pencil size={14} />
        </button>
      </div>
    </div>
  );
}
