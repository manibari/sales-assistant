"use client";

import { useState, useEffect, useCallback } from "react";
import { FileText, Plus, ChevronDown, ChevronRight, Check, X, Trash2 } from "lucide-react";
import { nxApi, type NxDocument, type NxMilestone } from "@/lib/nexus-api";

const DOC_TYPE_LABELS: Record<string, string> = {
  rfq: "RFQ 需求書",
  quote: "報價單",
  sow: "SOW 工作說明書",
  po: "PO 採購單",
  contract: "合約",
};

const DOC_STATUS_LABELS: Record<string, string> = {
  pending: "草稿",
  sent: "已送出",
  signed: "已簽署",
  expired: "已過期",
  terminated: "已終止",
};

const DOC_TYPES = ["rfq", "quote", "sow", "po", "contract"] as const;

function formatAmount(amount: number | null) {
  if (amount == null) return null;
  if (amount >= 1_000_000) return `${(amount / 1_000_000).toFixed(1)}M`;
  if (amount >= 1_000) return `${(amount / 1_000).toFixed(0)}K`;
  return String(amount);
}

function formatDate(d: string | null) {
  if (!d) return "--";
  return new Date(d).toLocaleDateString("zh-TW");
}

// --- Milestone Editor ---

function MilestoneEditor({
  milestones,
  totalAmount,
  onChange,
}: {
  milestones: NxMilestone[];
  totalAmount: number;
  onChange: (ms: NxMilestone[]) => void;
}) {
  const addRow = () =>
    onChange([
      ...milestones,
      { name: "", pct: 0, amount: 0, condition: null, due_date: null, invoice_id: null },
    ]);

  const removeRow = (i: number) => onChange(milestones.filter((_, idx) => idx !== i));

  const update = (i: number, field: keyof NxMilestone, value: string | number | null) => {
    const next = milestones.map((m, idx) => {
      if (idx !== i) return m;
      if (field === "pct") {
        const pct = Number(value) || 0;
        return { ...m, pct, amount: Math.round((pct / 100) * totalAmount) };
      }
      return { ...m, [field]: value };
    });
    onChange(next);
  };

  const totalPct = milestones.reduce((s, m) => s + (m.pct || 0), 0);

  return (
    <div className="space-y-2">
      <div className="grid grid-cols-[1fr_60px_80px_100px_auto] gap-1.5 text-[11px] text-slate-400 px-1">
        <span>里程碑名稱</span>
        <span>%</span>
        <span>金額</span>
        <span>預計日期</span>
        <span />
      </div>
      {milestones.map((m, i) => (
        <div key={i} className="grid grid-cols-[1fr_60px_80px_100px_auto] gap-1.5 items-center">
          <input
            value={m.name}
            onChange={(e) => update(i, "name", e.target.value)}
            placeholder={`里程碑 ${i + 1}`}
            className="text-xs px-2 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-50 focus:outline-none focus:border-blue-500"
          />
          <input
            type="number"
            value={m.pct || ""}
            onChange={(e) => update(i, "pct", e.target.value)}
            placeholder="0"
            min={0}
            max={100}
            className="text-xs px-2 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-50 focus:outline-none focus:border-blue-500 text-right"
          />
          <input
            type="number"
            value={m.amount || ""}
            onChange={(e) => update(i, "amount", Number(e.target.value))}
            placeholder="0"
            className="text-xs px-2 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-50 focus:outline-none focus:border-blue-500 text-right"
          />
          <input
            type="date"
            value={m.due_date || ""}
            onChange={(e) => update(i, "due_date", e.target.value || null)}
            className="text-xs px-2 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-50 focus:outline-none focus:border-blue-500"
          />
          <button
            onClick={() => removeRow(i)}
            className="p-1 text-slate-400 hover:text-red-500 cursor-pointer transition-colors"
          >
            <Trash2 size={13} />
          </button>
        </div>
      ))}
      <div className="flex items-center justify-between pt-1">
        <button
          onClick={addRow}
          className="flex items-center gap-1 text-xs text-blue-500 hover:text-blue-400 cursor-pointer"
        >
          <Plus size={13} />
          加里程碑
        </button>
        <span
          className={`text-xs ${
            totalPct === 100 ? "text-green-500" : totalPct > 100 ? "text-red-500" : "text-amber-500"
          }`}
        >
          合計 {totalPct}%
        </span>
      </div>
    </div>
  );
}

// --- Create Document Modal ---

function CreateDocModal({
  dealId,
  clientId,
  onClose,
  onCreated,
}: {
  dealId: number;
  clientId: number;
  onClose: () => void;
  onCreated: () => void;
}) {
  const [docType, setDocType] = useState<string>("quote");
  const [docNo, setDocNo] = useState("");
  const [amount, setAmount] = useState("");
  const [status, setStatus] = useState("pending");
  const [signDate, setSignDate] = useState("");
  const [notes, setNotes] = useState("");
  const [milestones, setMilestones] = useState<NxMilestone[]>([]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const isSow = docType === "sow";
  const amountNum = parseFloat(amount) || 0;

  const handleSubmit = async () => {
    if (!docType) return;
    setSaving(true);
    setError("");
    try {
      await nxApi.documents.create({
        client_id: clientId,
        doc_type: docType,
        deal_id: dealId,
        doc_no: docNo || null,
        amount: amountNum || null,
        status,
        sign_date: signDate || null,
        notes: notes || null,
        milestone_json: isSow && milestones.length > 0 ? milestones : null,
      });
      onCreated();
    } catch (e) {
      setError(e instanceof Error ? e.message : "儲存失敗");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-xl w-full max-w-lg mx-4 overflow-hidden">
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-200 dark:border-slate-700">
          <h2 className="text-base font-semibold text-slate-900 dark:text-slate-50">新增文件</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 cursor-pointer">
            <X size={18} />
          </button>
        </div>

        <div className="px-5 py-4 space-y-3 overflow-auto max-h-[75vh]">
          {/* Doc type */}
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">文件類型</label>
            <div className="grid grid-cols-5 gap-1.5">
              {DOC_TYPES.map((t) => (
                <button
                  key={t}
                  onClick={() => setDocType(t)}
                  className={`py-1.5 text-xs rounded-lg border font-medium cursor-pointer transition-colors ${
                    docType === t
                      ? "border-blue-500 bg-blue-500/10 text-blue-500"
                      : "border-slate-200 dark:border-slate-700 text-slate-500 hover:border-slate-400"
                  }`}
                >
                  {t.toUpperCase()}
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">文件編號</label>
              <input
                value={docNo}
                onChange={(e) => setDocNo(e.target.value)}
                placeholder="如 Q-2026-001"
                className="w-full text-sm px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-50 focus:outline-none focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">金額</label>
              <input
                type="number"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="0"
                className="w-full text-sm px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-50 focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">狀態</label>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value)}
                className="w-full text-sm px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-50 focus:outline-none focus:border-blue-500"
              >
                {Object.entries(DOC_STATUS_LABELS).map(([v, l]) => (
                  <option key={v} value={v}>
                    {l}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">簽署日期</label>
              <input
                type="date"
                value={signDate}
                onChange={(e) => setSignDate(e.target.value)}
                className="w-full text-sm px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-50 focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">備註</label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={2}
              className="w-full text-sm px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-50 focus:outline-none focus:border-blue-500 resize-none"
            />
          </div>

          {/* SOW milestone editor */}
          {isSow && (
            <div className="border border-slate-200 dark:border-slate-700 rounded-xl p-3 space-y-2">
              <p className="text-xs font-medium text-slate-700 dark:text-slate-300">付款里程碑</p>
              <MilestoneEditor
                milestones={milestones}
                totalAmount={amountNum}
                onChange={setMilestones}
              />
            </div>
          )}

          {error && <p className="text-xs text-red-500">{error}</p>}
        </div>

        <div className="flex justify-end gap-2 px-5 py-4 border-t border-slate-200 dark:border-slate-700">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 cursor-pointer transition-colors"
          >
            取消
          </button>
          <button
            onClick={handleSubmit}
            disabled={saving}
            className="px-4 py-2 text-sm rounded-lg bg-blue-500 text-white font-medium hover:bg-blue-600 cursor-pointer transition-colors disabled:opacity-50"
          >
            {saving ? "儲存中..." : "建立"}
          </button>
        </div>
      </div>
    </div>
  );
}

// --- Milestone Table (read-only) ---

function MilestoneTable({ milestones }: { milestones: NxMilestone[] }) {
  return (
    <div className="mt-2 border border-slate-100 dark:border-slate-800 rounded-lg overflow-hidden">
      <table className="w-full text-xs">
        <thead>
          <tr className="bg-slate-50 dark:bg-slate-800 text-slate-400">
            <th className="text-left px-3 py-1.5 font-medium">里程碑</th>
            <th className="text-right px-3 py-1.5 font-medium">%</th>
            <th className="text-right px-3 py-1.5 font-medium">金額</th>
            <th className="text-right px-3 py-1.5 font-medium">預計日期</th>
          </tr>
        </thead>
        <tbody>
          {milestones.map((m, i) => (
            <tr
              key={i}
              className="border-t border-slate-100 dark:border-slate-800 text-slate-700 dark:text-slate-300"
            >
              <td className="px-3 py-1.5">{m.name || `里程碑 ${i + 1}`}</td>
              <td className="px-3 py-1.5 text-right">{m.pct}%</td>
              <td className="px-3 py-1.5 text-right">
                {m.amount ? m.amount.toLocaleString() : "--"}
              </td>
              <td className="px-3 py-1.5 text-right">{formatDate(m.due_date)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// --- Document Row ---

function DocRow({
  doc,
  onUpdated,
  isClosed,
}: {
  doc: NxDocument;
  onUpdated: () => void;
  isClosed: boolean;
}) {
  const [expanded, setExpanded] = useState(false);
  const [editStatus, setEditStatus] = useState(false);
  const [statusVal, setStatusVal] = useState(doc.status);

  const milestones: NxMilestone[] = (() => {
    if (!doc.milestone_json) return [];
    if (typeof doc.milestone_json === "string") {
      try {
        return JSON.parse(doc.milestone_json) as NxMilestone[];
      } catch {
        return [];
      }
    }
    return doc.milestone_json as NxMilestone[];
  })();

  const hasMilestones = doc.doc_type === "sow" && milestones.length > 0;
  const isExpandable = hasMilestones || doc.notes;

  const saveStatus = async () => {
    try {
      await nxApi.documents.update(doc.id, { status: statusVal });
      setEditStatus(false);
      onUpdated();
    } catch {
      setStatusVal(doc.status);
      setEditStatus(false);
    }
  };

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl overflow-hidden">
      <div className="p-3">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2 min-w-0 flex-1">
            <FileText size={15} className="text-blue-500 flex-shrink-0" />
            <div className="min-w-0">
              <div className="flex items-center gap-1.5 flex-wrap">
                <span className="text-sm font-medium text-slate-900 dark:text-slate-50">
                  {DOC_TYPE_LABELS[doc.doc_type] || doc.doc_type.toUpperCase()}
                </span>
                {doc.doc_no && (
                  <span className="text-xs text-slate-400">#{doc.doc_no}</span>
                )}
                {doc.amount && (
                  <span className="text-xs font-medium text-blue-500">
                    NT${formatAmount(doc.amount)}
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2 mt-0.5">
                {editStatus && !isClosed ? (
                  <div className="flex items-center gap-1">
                    <select
                      value={statusVal}
                      onChange={(e) => setStatusVal(e.target.value)}
                      className="text-xs px-2 py-0.5 rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 focus:outline-none"
                    >
                      {Object.entries(DOC_STATUS_LABELS).map(([v, l]) => (
                        <option key={v} value={v}>
                          {l}
                        </option>
                      ))}
                    </select>
                    <button
                      onClick={saveStatus}
                      className="p-0.5 text-green-500 hover:text-green-400 cursor-pointer"
                    >
                      <Check size={12} />
                    </button>
                    <button
                      onClick={() => {
                        setStatusVal(doc.status);
                        setEditStatus(false);
                      }}
                      className="p-0.5 text-slate-400 hover:text-slate-300 cursor-pointer"
                    >
                      <X size={12} />
                    </button>
                  </div>
                ) : (
                  <button
                    onClick={() => !isClosed && setEditStatus(true)}
                    className={`text-[11px] px-2 py-0.5 rounded-full cursor-pointer transition-colors ${
                      doc.status === "signed"
                        ? "bg-green-500/10 text-green-400"
                        : doc.status === "sent"
                          ? "bg-blue-500/10 text-blue-400"
                          : "bg-slate-100 dark:bg-slate-800 text-slate-500"
                    } ${!isClosed ? "hover:opacity-80" : ""}`}
                  >
                    {DOC_STATUS_LABELS[doc.status] || doc.status}
                  </button>
                )}
                {doc.sign_date && (
                  <span className="text-[11px] text-slate-400">簽署 {doc.sign_date}</span>
                )}
              </div>
            </div>
          </div>
          {isExpandable && (
            <button
              onClick={() => setExpanded(!expanded)}
              className="text-slate-400 hover:text-slate-600 cursor-pointer transition-colors"
            >
              {expanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
            </button>
          )}
        </div>
      </div>

      {expanded && (
        <div className="px-3 pb-3 border-t border-slate-100 dark:border-slate-800 pt-2">
          {doc.notes && (
            <p className="text-xs text-slate-500 mb-2">{doc.notes}</p>
          )}
          {hasMilestones && <MilestoneTable milestones={milestones} />}
        </div>
      )}
    </div>
  );
}

// --- Main export ---

export function DealDocumentsSection({
  dealId,
  clientId,
  isClosed,
}: {
  dealId: number;
  clientId: number;
  isClosed: boolean;
}) {
  const [docs, setDocs] = useState<NxDocument[]>([]);
  const [showCreate, setShowCreate] = useState(false);

  const loadDocs = useCallback(async () => {
    try {
      const data = await nxApi.documents.listByDeal(dealId);
      setDocs(data);
    } catch (err) {
      console.error("Failed to load deal documents:", err);
    }
  }, [dealId]);

  useEffect(() => {
    loadDocs();
  }, [loadDocs]);

  return (
    <>
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <FileText size={16} className="text-indigo-500" />
            <span className="text-sm font-semibold text-slate-900 dark:text-slate-50">
              商務文件
            </span>
            <span className="text-xs text-slate-400">({docs.length})</span>
          </div>
          {!isClosed && (
            <button
              onClick={() => setShowCreate(true)}
              className="flex items-center gap-1 text-xs font-medium px-2.5 py-1 rounded-lg border border-blue-500/30 text-blue-500 hover:bg-blue-500/10 cursor-pointer transition-colors"
            >
              <Plus size={12} />
              新增文件
            </button>
          )}
        </div>

        {docs.length === 0 ? (
          <p className="text-xs text-slate-400 py-2">
            尚無商務文件 {!isClosed && "· 點擊右上角新增報價單 / SOW / PO"}
          </p>
        ) : (
          <div className="space-y-2">
            {docs.map((doc) => (
              <DocRow key={doc.id} doc={doc} onUpdated={loadDocs} isClosed={isClosed} />
            ))}
          </div>
        )}
      </div>

      {showCreate && (
        <CreateDocModal
          dealId={dealId}
          clientId={clientId}
          onClose={() => setShowCreate(false)}
          onCreated={() => {
            setShowCreate(false);
            loadDocs();
          }}
        />
      )}
    </>
  );
}
