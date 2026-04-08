"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Loader2,
  Briefcase,
  Users,
  Calendar,
  FileText,
  Receipt,
  Building2,
  Check,
  X,
  Plus,
  Trash2,
  ExternalLink,
} from "lucide-react";
import {
  nxApi,
  type NxProject,
  type NxDocument,
  type NxMilestone,
  type NxInvoice,
} from "@/lib/nexus-api";

const STATUS_LABELS: Record<string, string> = {
  planning: "規劃中",
  active: "進行中",
  completed: "已完成",
  paused: "暫停",
};

const INVOICE_STATUS_LABELS: Record<string, string> = {
  draft: "草稿",
  issued: "已開立",
  paid: "已收款",
  cancelled: "已作廢",
};

const INVOICE_STATUS_COLORS: Record<string, string> = {
  draft: "bg-slate-100 text-slate-600 dark:bg-slate-800",
  issued: "bg-blue-500/10 text-blue-500",
  paid: "bg-green-500/10 text-green-500",
  cancelled: "bg-red-500/10 text-red-500",
};

interface ProjectMember {
  id: number;
  user_id: number;
  user_name: string;
  user_email: string;
}

function formatDate(d: string | null | undefined) {
  if (!d) return "—";
  return new Date(d).toLocaleDateString("zh-TW");
}

function formatMoney(amount: number | null | undefined, currency = "TWD") {
  if (amount == null) return "—";
  return `${currency} ${amount.toLocaleString()}`;
}

function parseMilestones(mj: NxMilestone[] | string | null): NxMilestone[] {
  if (!mj) return [];
  if (typeof mj === "string") {
    try {
      return JSON.parse(mj) as NxMilestone[];
    } catch {
      return [];
    }
  }
  return mj;
}

export default function ProjectDetailPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = Number(params.id);

  const [project, setProject] = useState<NxProject | null>(null);
  const [members, setMembers] = useState<ProjectMember[]>([]);
  const [sows, setSows] = useState<NxDocument[]>([]);
  const [invoices, setInvoices] = useState<NxInvoice[]>([]);
  const [allUsers, setAllUsers] = useState<{ id: number; name: string }[]>([]);
  const [loading, setLoading] = useState(true);

  // Edit states
  const [editingPm, setEditingPm] = useState(false);
  const [editingCsm, setEditingCsm] = useState(false);
  const [editingStatus, setEditingStatus] = useState(false);
  const [pmValue, setPmValue] = useState<number | null>(null);
  const [csmValue, setCsmValue] = useState<number | null>(null);
  const [statusValue, setStatusValue] = useState("");
  const [showAddMember, setShowAddMember] = useState(false);
  const [memberToAdd, setMemberToAdd] = useState<number | null>(null);
  const [invoiceModal, setInvoiceModal] = useState<{
    sow: NxDocument;
    milestone: NxMilestone;
    index: number;
  } | null>(null);

  const loadAll = useCallback(async () => {
    try {
      const proj = await nxApi.projects.get(projectId);
      setProject(proj);

      const [mems, invs, users] = await Promise.all([
        nxApi.projects.listMembers(projectId),
        nxApi.invoices.list({ project_id: projectId }),
        nxApi.deals.listUsers(),
      ]);
      setMembers(mems);
      setInvoices(invs);
      setAllUsers(users);

      // Load SOWs for this project's deal
      if (proj.deal_id) {
        const docs = await nxApi.documents.listByDeal(proj.deal_id);
        setSows(docs.filter((d) => d.doc_type === "sow"));
      }
    } catch (err) {
      console.error("Failed to load project:", err);
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    loadAll();
  }, [loadAll]);

  const updatePm = async () => {
    await nxApi.projects.update(projectId, { pm_id: pmValue } as Partial<NxProject>);
    setEditingPm(false);
    loadAll();
  };

  const updateCsm = async () => {
    await nxApi.projects.update(projectId, { csm_id: csmValue } as Partial<NxProject>);
    setEditingCsm(false);
    loadAll();
  };

  const updateStatus = async () => {
    await nxApi.projects.update(projectId, { status: statusValue } as Partial<NxProject>);
    setEditingStatus(false);
    loadAll();
  };

  const addMember = async () => {
    if (!memberToAdd) return;
    await nxApi.projects.addMember(projectId, memberToAdd);
    setMemberToAdd(null);
    setShowAddMember(false);
    loadAll();
  };

  const removeMember = async (userId: number) => {
    if (!confirm("確定移除此成員？")) return;
    await nxApi.projects.removeMember(projectId, userId);
    loadAll();
  };

  // For each milestone, find the invoice (if any) by sow_doc_id + milestone_index
  const findInvoiceForMilestone = (sowId: number, idx: number): NxInvoice | undefined =>
    invoices.find((i) => i.sow_doc_id === sowId && i.milestone_index === idx);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 size={24} className="animate-spin text-blue-500" />
      </div>
    );
  }

  if (!project) {
    return (
      <div className="flex items-center justify-center h-full text-slate-400">
        找不到此專案
      </div>
    );
  }

  const memberUserIds = new Set(members.map((m) => m.user_id));
  const availableForMember = allUsers.filter((u) => !memberUserIds.has(u.id));

  return (
    <div className="flex flex-col h-full">
      <div className="h-14 px-4 flex items-center gap-3 border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
        <button
          onClick={() => router.push("/projects")}
          className="p-1.5 text-slate-400 hover:text-slate-600 cursor-pointer transition-colors"
        >
          <ArrowLeft size={20} />
        </button>
        <Briefcase size={18} className="text-indigo-500" />
        <h1 className="text-lg font-bold text-slate-900 dark:text-slate-50 truncate flex-1">
          {project.name}
        </h1>
      </div>

      <div className="flex-1 px-4 py-4 overflow-auto max-w-2xl lg:max-w-4xl mx-auto w-full space-y-3">
        {/* Header card */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4">
          <div className="flex items-start justify-between gap-3">
            <div className="flex-1 min-w-0">
              {project.client_name && (
                <p className="text-sm text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
                  <Building2 size={13} />
                  {project.client_name}
                </p>
              )}
              {project.deal_name && project.deal_id && (
                <Link
                  href={`/deals/${project.deal_id}`}
                  className="text-xs text-blue-500 hover:underline mt-1 inline-flex items-center gap-1"
                >
                  ← 商機：{project.deal_name}
                </Link>
              )}
            </div>
            <div>
              {editingStatus ? (
                <div className="flex items-center gap-1">
                  <select
                    value={statusValue}
                    onChange={(e) => setStatusValue(e.target.value)}
                    className="text-xs px-2 py-1 rounded border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 focus:outline-none"
                  >
                    {Object.entries(STATUS_LABELS).map(([v, l]) => (
                      <option key={v} value={v}>
                        {l}
                      </option>
                    ))}
                  </select>
                  <button onClick={updateStatus} className="p-0.5 text-blue-500 cursor-pointer">
                    <Check size={14} />
                  </button>
                  <button
                    onClick={() => setEditingStatus(false)}
                    className="p-0.5 text-slate-400 cursor-pointer"
                  >
                    <X size={14} />
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => {
                    setStatusValue(project.status);
                    setEditingStatus(true);
                  }}
                  className="text-xs px-2.5 py-1 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 cursor-pointer hover:bg-slate-200 transition-colors"
                >
                  {STATUS_LABELS[project.status] || project.status}
                </button>
              )}
            </div>
          </div>

          {/* PM / CSM / dates */}
          <div className="mt-3 grid grid-cols-2 gap-3 text-xs">
            <div>
              <span className="text-slate-400">PM</span>
              <div className="mt-0.5">
                {editingPm ? (
                  <div className="flex items-center gap-1">
                    <select
                      value={pmValue ?? ""}
                      onChange={(e) =>
                        setPmValue(e.target.value ? Number(e.target.value) : null)
                      }
                      className="text-xs px-2 py-0.5 rounded border border-blue-500 bg-white dark:bg-slate-800 focus:outline-none"
                    >
                      <option value="">未指定</option>
                      {allUsers.map((u) => (
                        <option key={u.id} value={u.id}>
                          {u.name}
                        </option>
                      ))}
                    </select>
                    <button onClick={updatePm} className="text-blue-500 cursor-pointer">
                      <Check size={12} />
                    </button>
                    <button
                      onClick={() => setEditingPm(false)}
                      className="text-slate-400 cursor-pointer"
                    >
                      <X size={12} />
                    </button>
                  </div>
                ) : (
                  <span
                    onClick={() => {
                      setPmValue(project.pm_id ?? null);
                      setEditingPm(true);
                    }}
                    className="text-slate-700 dark:text-slate-300 cursor-pointer hover:text-blue-500"
                  >
                    {project.pm_name || "未指定"}
                  </span>
                )}
              </div>
            </div>
            <div>
              <span className="text-slate-400">CSM</span>
              <div className="mt-0.5">
                {editingCsm ? (
                  <div className="flex items-center gap-1">
                    <select
                      value={csmValue ?? ""}
                      onChange={(e) =>
                        setCsmValue(e.target.value ? Number(e.target.value) : null)
                      }
                      className="text-xs px-2 py-0.5 rounded border border-blue-500 bg-white dark:bg-slate-800 focus:outline-none"
                    >
                      <option value="">未指定</option>
                      {allUsers.map((u) => (
                        <option key={u.id} value={u.id}>
                          {u.name}
                        </option>
                      ))}
                    </select>
                    <button onClick={updateCsm} className="text-blue-500 cursor-pointer">
                      <Check size={12} />
                    </button>
                    <button
                      onClick={() => setEditingCsm(false)}
                      className="text-slate-400 cursor-pointer"
                    >
                      <X size={12} />
                    </button>
                  </div>
                ) : (
                  <span
                    onClick={() => {
                      setCsmValue(project.csm_id ?? null);
                      setEditingCsm(true);
                    }}
                    className="text-slate-700 dark:text-slate-300 cursor-pointer hover:text-blue-500"
                  >
                    {project.csm_name || "未指定"}
                  </span>
                )}
              </div>
            </div>
            <div>
              <span className="text-slate-400">起始</span>
              <div className="text-slate-700 dark:text-slate-300 mt-0.5">
                {formatDate(project.start_date)}
              </div>
            </div>
            <div>
              <span className="text-slate-400">結束</span>
              <div className="text-slate-700 dark:text-slate-300 mt-0.5">
                {formatDate(project.end_date)}
              </div>
            </div>
          </div>
        </div>

        {/* Members */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Users size={16} className="text-slate-500" />
              <span className="text-sm font-semibold text-slate-900 dark:text-slate-50">
                專案成員
              </span>
              <span className="text-xs text-slate-400">({members.length})</span>
            </div>
            <button
              onClick={() => setShowAddMember(!showAddMember)}
              className="text-xs text-blue-500 hover:text-blue-400 cursor-pointer"
            >
              {showAddMember ? "取消" : "+ 加入"}
            </button>
          </div>

          {showAddMember && (
            <div className="mb-2 flex items-center gap-2">
              <select
                value={memberToAdd ?? ""}
                onChange={(e) =>
                  setMemberToAdd(e.target.value ? Number(e.target.value) : null)
                }
                className="flex-1 text-xs px-2 py-1.5 rounded border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 focus:outline-none"
              >
                <option value="">選擇成員...</option>
                {availableForMember.map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.name}
                  </option>
                ))}
              </select>
              <button
                onClick={addMember}
                disabled={!memberToAdd}
                className="text-xs px-3 py-1.5 bg-blue-500 text-white rounded font-medium cursor-pointer disabled:opacity-50"
              >
                新增
              </button>
            </div>
          )}

          {members.length === 0 ? (
            <p className="text-xs text-slate-400 py-1">尚無成員</p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {members.map((m) => (
                <span
                  key={m.id}
                  className="inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300"
                >
                  {m.user_name}
                  <button
                    onClick={() => removeMember(m.user_id)}
                    className="text-slate-400 hover:text-red-500 cursor-pointer"
                  >
                    <X size={11} />
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>

        {/* SOW + Milestones */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-3">
            <FileText size={16} className="text-blue-500" />
            <span className="text-sm font-semibold text-slate-900 dark:text-slate-50">
              SOW 與付款里程碑
            </span>
            <span className="text-xs text-slate-400">({sows.length})</span>
          </div>

          {sows.length === 0 ? (
            <p className="text-xs text-slate-400">
              尚無 SOW · 請到{" "}
              {project.deal_id && (
                <Link
                  href={`/deals/${project.deal_id}`}
                  className="text-blue-500 hover:underline"
                >
                  商機詳頁
                </Link>
              )}{" "}
              建立
            </p>
          ) : (
            <div className="space-y-3">
              {sows.map((sow) => {
                const milestones = parseMilestones(sow.milestone_json);
                return (
                  <div
                    key={sow.id}
                    className="border border-slate-100 dark:border-slate-800 rounded-lg overflow-hidden"
                  >
                    <div className="px-3 py-2 bg-slate-50 dark:bg-slate-800 flex items-center justify-between">
                      <div className="text-xs">
                        <span className="font-medium text-slate-700 dark:text-slate-300">
                          {sow.doc_no || `SOW #${sow.id}`}
                        </span>
                        <span className="text-slate-400 ml-2">
                          {formatMoney(sow.amount, sow.currency)}
                        </span>
                      </div>
                    </div>
                    {milestones.length === 0 ? (
                      <p className="text-xs text-slate-400 px-3 py-2">無里程碑</p>
                    ) : (
                      <table className="w-full text-xs">
                        <thead>
                          <tr className="text-slate-400 border-b border-slate-100 dark:border-slate-800">
                            <th className="text-left px-3 py-1.5 font-medium">里程碑</th>
                            <th className="text-right px-3 py-1.5 font-medium">金額</th>
                            <th className="text-right px-3 py-1.5 font-medium">日期</th>
                            <th className="text-right px-3 py-1.5 font-medium">狀態</th>
                          </tr>
                        </thead>
                        <tbody>
                          {milestones.map((m, idx) => {
                            const inv = findInvoiceForMilestone(sow.id, idx);
                            return (
                              <tr
                                key={idx}
                                className="border-b border-slate-100 dark:border-slate-800 last:border-0"
                              >
                                <td className="px-3 py-2 text-slate-700 dark:text-slate-300">
                                  {m.name || `里程碑 ${idx + 1}`}
                                  <span className="text-slate-400 ml-1">({m.pct}%)</span>
                                </td>
                                <td className="px-3 py-2 text-right text-slate-700 dark:text-slate-300">
                                  {m.amount ? m.amount.toLocaleString() : "—"}
                                </td>
                                <td className="px-3 py-2 text-right text-slate-400">
                                  {formatDate(m.due_date)}
                                </td>
                                <td className="px-3 py-2 text-right">
                                  {inv ? (
                                    <span
                                      className={`inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full font-medium ${INVOICE_STATUS_COLORS[inv.status] || INVOICE_STATUS_COLORS.draft}`}
                                    >
                                      {INVOICE_STATUS_LABELS[inv.status] || inv.status} ·{" "}
                                      {inv.invoice_no}
                                    </span>
                                  ) : (
                                    <button
                                      onClick={() =>
                                        setInvoiceModal({ sow, milestone: m, index: idx })
                                      }
                                      className="text-[10px] px-2 py-0.5 rounded-full border border-blue-500/30 text-blue-500 hover:bg-blue-500/10 cursor-pointer transition-colors"
                                    >
                                      + 開票
                                    </button>
                                  )}
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Invoices */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <Receipt size={16} className="text-green-500" />
            <span className="text-sm font-semibold text-slate-900 dark:text-slate-50">
              發票
            </span>
            <span className="text-xs text-slate-400">({invoices.length})</span>
          </div>

          {invoices.length === 0 ? (
            <p className="text-xs text-slate-400">尚無發票</p>
          ) : (
            <div className="space-y-1">
              {invoices.map((inv) => (
                <div
                  key={inv.id}
                  className="flex items-center justify-between text-xs py-1.5 border-b border-slate-100 dark:border-slate-800 last:border-0"
                >
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-slate-700 dark:text-slate-300">
                      {inv.invoice_no}
                    </span>
                    <span
                      className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${INVOICE_STATUS_COLORS[inv.status] || INVOICE_STATUS_COLORS.draft}`}
                    >
                      {INVOICE_STATUS_LABELS[inv.status] || inv.status}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 text-slate-400">
                    <span>{formatDate(inv.issue_date)}</span>
                    <span className="text-slate-700 dark:text-slate-300 font-medium">
                      {formatMoney(inv.amount, inv.currency)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {invoiceModal && project && (
        <CreateInvoiceModal
          dealId={project.deal_id!}
          clientId={project.client_id!}
          projectId={projectId}
          sow={invoiceModal.sow}
          milestone={invoiceModal.milestone}
          milestoneIndex={invoiceModal.index}
          onClose={() => setInvoiceModal(null)}
          onCreated={() => {
            setInvoiceModal(null);
            loadAll();
          }}
        />
      )}
    </div>
  );
}

// --- Invoice Create Modal ---

function CreateInvoiceModal({
  dealId,
  clientId,
  projectId,
  sow,
  milestone,
  milestoneIndex,
  onClose,
  onCreated,
}: {
  dealId: number;
  clientId: number;
  projectId: number;
  sow: NxDocument;
  milestone: NxMilestone;
  milestoneIndex: number;
  onClose: () => void;
  onCreated: () => void;
}) {
  const today = new Date().toISOString().slice(0, 10);
  const [invoiceNo, setInvoiceNo] = useState(
    `INV-${new Date().getFullYear()}${String(new Date().getMonth() + 1).padStart(2, "0")}-${milestoneIndex + 1}`
  );
  const [amount, setAmount] = useState(String(milestone.amount || 0));
  const [issueDate, setIssueDate] = useState(today);
  const [dueDate, setDueDate] = useState("");
  const [notes, setNotes] = useState(`${sow.doc_no || `SOW#${sow.id}`} - ${milestone.name || `里程碑 ${milestoneIndex + 1}`}`);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async () => {
    setSaving(true);
    setError("");
    try {
      await nxApi.invoices.create({
        deal_id: dealId,
        client_id: clientId,
        project_id: projectId,
        sow_doc_id: sow.id,
        milestone_index: milestoneIndex,
        invoice_no: invoiceNo,
        amount: parseFloat(amount) || 0,
        currency: sow.currency || "TWD",
        issue_date: issueDate || null,
        due_date: dueDate || null,
        notes: notes || null,
      });
      onCreated();
    } catch (e) {
      setError(e instanceof Error ? e.message : "建立失敗");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-xl w-full max-w-md mx-4 overflow-hidden">
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-200 dark:border-slate-700">
          <h2 className="text-base font-semibold text-slate-900 dark:text-slate-50">
            開立發票
          </h2>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 cursor-pointer"
          >
            <X size={18} />
          </button>
        </div>

        <div className="px-5 py-4 space-y-3">
          <div className="text-xs text-slate-500 bg-slate-50 dark:bg-slate-800 rounded-lg p-2">
            {sow.doc_no || `SOW #${sow.id}`} · {milestone.name || `里程碑 ${milestoneIndex + 1}`}
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">發票號碼 *</label>
            <input
              value={invoiceNo}
              onChange={(e) => setInvoiceNo(e.target.value)}
              className="w-full text-sm px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 focus:outline-none focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">金額 *</label>
            <input
              type="number"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              className="w-full text-sm px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 focus:outline-none focus:border-blue-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">開立日期</label>
              <input
                type="date"
                value={issueDate}
                onChange={(e) => setIssueDate(e.target.value)}
                className="w-full text-sm px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 focus:outline-none focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">到期日</label>
              <input
                type="date"
                value={dueDate}
                onChange={(e) => setDueDate(e.target.value)}
                className="w-full text-sm px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">備註</label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={2}
              className="w-full text-sm px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 resize-none focus:outline-none focus:border-blue-500"
            />
          </div>

          {error && <p className="text-xs text-red-500">{error}</p>}
        </div>

        <div className="flex justify-end gap-2 px-5 py-4 border-t border-slate-200 dark:border-slate-700">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 text-slate-600 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800"
          >
            取消
          </button>
          <button
            onClick={handleSubmit}
            disabled={saving || !invoiceNo || !amount}
            className="px-4 py-2 text-sm rounded-lg bg-blue-500 text-white font-medium cursor-pointer hover:bg-blue-600 disabled:opacity-50"
          >
            {saving ? "儲存中..." : "建立發票"}
          </button>
        </div>
      </div>
    </div>
  );
}
