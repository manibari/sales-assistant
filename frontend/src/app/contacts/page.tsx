"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { TopBar } from "@/components/top-bar";
import { nxApi, type NxClient, type NxPartner } from "@/lib/nexus-api";
import { formatBudget, industryLabel } from "@/lib/options";
import { Building2, Handshake, Plus, Trash2, Merge, CheckSquare, Pin, PinOff, BarChart3 } from "lucide-react";
import { ClientHeatmap } from "@/components/client-heatmap";
import { CreateClientModal } from "@/components/create-client-modal";
import { CreatePartnerModal } from "@/components/create-partner-modal";

const TRUST_LABELS: Record<string, string> = {
  unverified: "未驗證",
  testing: "驗證中",
  verified: "已驗證",
  core_team: "核心班底",
  si_backed: "SI 擔保",
  demoted: "不推薦",
};

const TRUST_COLORS: Record<string, string> = {
  unverified: "bg-amber-500/10 text-amber-400",
  testing: "bg-blue-500/10 text-blue-400",
  verified: "bg-green-500/10 text-green-400",
  core_team: "bg-green-500/10 text-green-400",
  si_backed: "bg-violet-500/10 text-violet-400",
  demoted: "bg-red-500/10 text-red-400",
};


export default function ContactsPage() {
  const [tab, setTab] = useState<"clients" | "partners" | "analysis">("clients");
  const [clients, setClients] = useState<NxClient[]>([]);
  const [partners, setPartners] = useState<NxPartner[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectMode, setSelectMode] = useState(false);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [merging, setMerging] = useState(false);
  const [showMergeConfirm, setShowMergeConfirm] = useState(false);

  const toggleSelect = (id: number) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const exitSelectMode = () => {
    setSelectMode(false);
    setSelected(new Set());
    setShowMergeConfirm(false);
  };

  const handleMerge = async () => {
    if (selected.size < 2) return;
    setMerging(true);
    try {
      const ids = Array.from(selected);
      const targetId = ids[0]; // first selected = target
      const sourceIds = ids.slice(1);
      await nxApi.clients.merge(targetId, sourceIds);
      exitSelectMode();
      loadData();
    } catch (err) {
      console.error("Merge failed:", err);
    } finally {
      setMerging(false);
    }
  };

  const handleBulkDelete = async () => {
    setMerging(true);
    const errors: string[] = [];
    try {
      for (const id of selected) {
        try {
          await nxApi.clients.delete(id);
        } catch (err) {
          const msg = err instanceof Error ? err.message : String(err);
          errors.push(msg);
        }
      }
      if (errors.length) {
        alert(`部分客戶無法刪除：\n${errors.join("\n")}`);
      }
      exitSelectMode();
      loadData();
    } catch (err) {
      console.error("Delete failed:", err);
    } finally {
      setMerging(false);
    }
  };

  const handleBulkDeletePartners = async () => {
    setMerging(true);
    const errors: string[] = [];
    try {
      for (const id of selected) {
        try {
          await nxApi.partners.delete(id);
        } catch (err) {
          const msg = err instanceof Error ? err.message : String(err);
          errors.push(msg);
        }
      }
      if (errors.length) {
        alert(`部分夥伴無法刪除：\n${errors.join("\n")}`);
      }
      exitSelectMode();
      loadData();
    } catch (err) {
      console.error("Delete partners failed:", err);
    } finally {
      setMerging(false);
    }
  };

  const handleTogglePin = async (id: number, type: "client" | "partner") => {
    try {
      if (type === "client") {
        const updated = await nxApi.clients.togglePin(id);
        setClients((prev) => prev.map((c) => (c.id === id ? { ...c, ...updated } : c)));
      } else {
        const updated = await nxApi.partners.togglePin(id);
        setPartners((prev) => prev.map((p) => (p.id === id ? { ...p, ...updated } : p)));
      }
    } catch (err) {
      console.error("Pin toggle failed:", err);
    }
  };

  const loadData = () => {
    setLoading(true);
    if (tab === "clients" || tab === "analysis") {
      nxApi.clients.list().then(setClients).catch(console.error).finally(() => setLoading(false));
    } else {
      nxApi.partners.list().then(setPartners).catch(console.error).finally(() => setLoading(false));
    }
  };

  useEffect(() => {
    loadData();
  }, [tab]);

  return (
    <div className="flex flex-col h-full">
      <TopBar title="關係網">
        <button
          onClick={() => selectMode ? exitSelectMode() : setSelectMode(true)}
          className={`p-2 rounded-lg cursor-pointer transition-colors ${
            selectMode
              ? "text-blue-500 bg-blue-500/10"
              : "text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
          }`}
          title={selectMode ? "取消選取" : "選取模式"}
        >
          <CheckSquare size={20} />
        </button>
        <button
          onClick={() => setShowCreateModal(true)}
          className="p-2 rounded-lg text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer transition-colors"
          title={tab === "clients" ? "新增客戶" : "新增夥伴"}
        >
          <Plus size={20} />
        </button>
      </TopBar>

      {/* Sub-tabs */}
      <div className="px-4 pt-3 flex gap-2 border-b border-slate-200 dark:border-slate-800">
        <button
          onClick={() => { exitSelectMode(); setTab("clients"); }}
          className={`flex items-center gap-1.5 px-3 py-2 text-sm font-medium border-b-2 transition-colors cursor-pointer ${
            tab === "clients"
              ? "border-blue-500 text-blue-500"
              : "border-transparent text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
          }`}
        >
          <Building2 size={16} strokeWidth={1.5} />
          客戶
        </button>
        <button
          onClick={() => { exitSelectMode(); setTab("partners"); }}
          className={`flex items-center gap-1.5 px-3 py-2 text-sm font-medium border-b-2 transition-colors cursor-pointer ${
            tab === "partners"
              ? "border-blue-500 text-blue-500"
              : "border-transparent text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
          }`}
        >
          <Handshake size={16} strokeWidth={1.5} />
          夥伴
        </button>
        <button
          onClick={() => { exitSelectMode(); setTab("analysis"); }}
          className={`flex items-center gap-1.5 px-3 py-2 text-sm font-medium border-b-2 transition-colors cursor-pointer ${
            tab === "analysis"
              ? "border-blue-500 text-blue-500"
              : "border-transparent text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
          }`}
        >
          <BarChart3 size={16} strokeWidth={1.5} />
          分析
        </button>
      </div>

      <div className="flex-1 px-4 py-4 overflow-auto">
        {loading ? (
          <div className="flex items-center justify-center py-20 text-slate-400">載入中...</div>
        ) : tab === "analysis" ? (
          clients.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 text-slate-400 dark:text-slate-500">
              <p className="text-sm">尚無客戶資料</p>
            </div>
          ) : (
            <div className="max-w-2xl lg:max-w-5xl mx-auto">
              <ClientHeatmap clients={clients} />
            </div>
          )
        ) : tab === "clients" ? (
          clients.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 text-slate-400 dark:text-slate-500">
              <p className="text-sm">尚無客戶</p>
            </div>
          ) : (
            <div className="space-y-3 max-w-2xl lg:max-w-4xl mx-auto">
              {/* Action toolbar when items selected */}
              {selectMode && selected.size > 0 && (
                <div className="sticky top-0 z-10 flex items-center gap-3 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-3">
                  <span className="text-sm text-slate-600 dark:text-slate-300 font-medium">
                    已選 {selected.size} 筆
                  </span>
                  <div className="flex-1" />
                  {selected.size >= 2 && (
                    <button
                      onClick={() => setShowMergeConfirm(true)}
                      disabled={merging}
                      className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-blue-500 text-white rounded-lg cursor-pointer hover:bg-blue-600 disabled:opacity-50 transition-colors"
                    >
                      <Merge size={14} />
                      整併
                    </button>
                  )}
                  <button
                    onClick={handleBulkDelete}
                    disabled={merging}
                    className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-red-500/10 text-red-400 rounded-lg cursor-pointer hover:bg-red-500/20 disabled:opacity-50 transition-colors"
                  >
                    <Trash2 size={14} />
                    刪除
                  </button>
                </div>
              )}

              {/* Merge confirmation */}
              {showMergeConfirm && (
                <div className="bg-blue-500/5 border border-blue-500/20 rounded-xl p-4 space-y-3">
                  <p className="text-sm text-slate-700 dark:text-slate-300">
                    將以下客戶整併為一筆（第一個為主體，其餘合併進去）：
                  </p>
                  <div className="space-y-1">
                    {Array.from(selected).map((id, idx) => {
                      const c = clients.find((cl) => cl.id === id);
                      return (
                        <div key={id} className="flex items-center gap-2 text-sm">
                          {idx === 0 ? (
                            <span className="text-[11px] px-2 py-0.5 rounded-full bg-blue-500 text-white font-medium">主體</span>
                          ) : (
                            <span className="text-[11px] px-2 py-0.5 rounded-full bg-slate-200 dark:bg-slate-700 text-slate-500">合併</span>
                          )}
                          <span className="text-slate-900 dark:text-slate-100">{c?.name || `#${id}`}</span>
                        </div>
                      );
                    })}
                  </div>
                  <div className="flex gap-2 justify-end">
                    <button
                      onClick={() => setShowMergeConfirm(false)}
                      className="px-3 py-1.5 text-xs bg-slate-200 dark:bg-slate-700 rounded-lg cursor-pointer"
                    >
                      取消
                    </button>
                    <button
                      onClick={handleMerge}
                      disabled={merging}
                      className="px-3 py-1.5 text-xs bg-blue-500 text-white rounded-lg cursor-pointer disabled:opacity-50 font-medium"
                    >
                      {merging ? "整併中..." : "確認整併"}
                    </button>
                  </div>
                </div>
              )}

              {(() => {
                const domesticClients = clients.filter((c) => c.market !== "overseas");
                const overseasClients = clients.filter((c) => c.market === "overseas");
                const renderCard = (c: NxClient) => {
                  const isSelected = selected.has(c.id);
                  const CardWrapper = selectMode ? "div" : Link;
                  const cardProps = selectMode
                    ? { onClick: () => toggleSelect(c.id) }
                    : { href: `/contacts/clients/${c.id}` };
                  return (
                    <CardWrapper
                      key={c.id}
                      {...(cardProps as any)}
                      className={`block bg-white dark:bg-slate-900 border rounded-xl p-4 cursor-pointer transition-colors duration-200 group ${
                        isSelected
                          ? "border-blue-500 bg-blue-500/5"
                          : "border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600"
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        {selectMode && (
                          <div className={`w-5 h-5 rounded border-2 flex items-center justify-center flex-shrink-0 transition-colors ${
                            isSelected ? "bg-blue-500 border-blue-500" : "border-slate-300 dark:border-slate-600"
                          }`}>
                            {isSelected && <span className="text-white text-xs font-bold">✓</span>}
                          </div>
                        )}
                        <div className="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center flex-shrink-0">
                          <Building2 size={20} className="text-blue-500" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-1.5">
                            <h3 className="text-base font-semibold text-slate-900 dark:text-slate-50 truncate">
                              {c.name}
                            </h3>
                            {c.pinned && <Pin size={12} className="text-amber-500 flex-shrink-0" />}
                          </div>
                          <div className="flex items-center gap-1.5 mt-0.5 flex-wrap">
                            {c.industry && (
                              <span className="text-[11px] px-1.5 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 font-medium">
                                {industryLabel(c.industry)}
                              </span>
                            )}
                            {(c.deal_count ?? 0) > 0 && (
                              <span className="text-[11px] px-1.5 py-0.5 rounded-full bg-blue-500/10 text-blue-500 font-medium">
                                {c.deal_count} 商機
                              </span>
                            )}
                            {(c.partner_count ?? 0) > 0 && (
                              <span className="text-[11px] px-1.5 py-0.5 rounded-full bg-green-500/10 text-green-600 dark:text-green-400 font-medium">
                                {c.partner_count} 夥伴
                              </span>
                            )}
                            {c.deal_budget_total != null && c.deal_budget_total > 0 && (
                              <span className="text-[11px] text-slate-400">
                                {formatBudget(c.deal_budget_total)}
                              </span>
                            )}
                          </div>
                          {c.tags && c.tags.length > 0 && (
                            <div className="flex items-center gap-1 mt-1 flex-wrap">
                              {c.tags.slice(0, 3).map((tag) => (
                                <span key={tag.id} className="text-[10px] px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400">
                                  {tag.name}
                                </span>
                              ))}
                              {c.tags.length > 3 && (
                                <span className="text-[10px] text-slate-400">+{c.tags.length - 3}</span>
                              )}
                            </div>
                          )}
                        </div>
                        {!selectMode && (
                          <button
                            onClick={(e) => { e.preventDefault(); e.stopPropagation(); handleTogglePin(c.id, "client"); }}
                            className={`p-1.5 rounded-lg transition-colors cursor-pointer flex-shrink-0 ${
                              c.pinned
                                ? "text-amber-500 hover:bg-amber-500/10"
                                : "text-slate-300 dark:text-slate-600 hover:text-amber-500 opacity-0 group-hover:opacity-100"
                            }`}
                            title={c.pinned ? "取消釘選" : "釘選"}
                          >
                            {c.pinned ? <PinOff size={16} /> : <Pin size={16} />}
                          </button>
                        )}
                      </div>
                    </CardWrapper>
                  );
                };
                return (
                  <>
                    {domesticClients.length > 0 && (
                      <>
                        <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider px-1">
                          國內 ({domesticClients.length})
                        </p>
                        {domesticClients.map(renderCard)}
                      </>
                    )}
                    {overseasClients.length > 0 && (
                      <>
                        <p className="text-xs font-semibold text-amber-500 uppercase tracking-wider px-1 mt-2">
                          海外 ({overseasClients.length})
                        </p>
                        {overseasClients.map(renderCard)}
                      </>
                    )}
                  </>
                );
              })()}
            </div>
          )
        ) : partners.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-slate-400 dark:text-slate-500">
            <p className="text-sm">尚無夥伴</p>
          </div>
        ) : (
          <div className="space-y-3 max-w-2xl lg:max-w-4xl mx-auto">
            {/* Action toolbar when partners selected */}
            {selectMode && selected.size > 0 && (
              <div className="sticky top-0 z-10 flex items-center gap-3 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-3">
                <span className="text-sm text-slate-600 dark:text-slate-300 font-medium">
                  已選 {selected.size} 筆
                </span>
                <div className="flex-1" />
                <button
                  onClick={handleBulkDeletePartners}
                  disabled={merging}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-red-500/10 text-red-400 rounded-lg cursor-pointer hover:bg-red-500/20 disabled:opacity-50 transition-colors"
                >
                  <Trash2 size={14} />
                  刪除
                </button>
              </div>
            )}

            {partners.map((p) => {
              const isSelected = selected.has(p.id);
              const CardWrapper = selectMode ? "div" : Link;
              const cardProps = selectMode
                ? { onClick: () => toggleSelect(p.id) }
                : { href: `/contacts/partners/${p.id}` };
              return (
                <CardWrapper
                  key={p.id}
                  {...(cardProps as any)}
                  className={`block bg-white dark:bg-slate-900 border rounded-xl p-4 cursor-pointer transition-colors duration-200 group ${
                    isSelected
                      ? "border-blue-500 bg-blue-500/5"
                      : "border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    {selectMode && (
                      <div className={`w-5 h-5 rounded border-2 flex items-center justify-center flex-shrink-0 ${
                        isSelected ? "bg-blue-500 border-blue-500" : "border-slate-300 dark:border-slate-600"
                      }`}>
                        {isSelected && <span className="text-white text-xs font-bold">✓</span>}
                      </div>
                    )}
                    <div className="w-10 h-10 rounded-lg bg-green-500/10 flex items-center justify-center flex-shrink-0">
                      <Handshake size={20} className="text-green-500" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1.5">
                        <h3 className="text-base font-semibold text-slate-900 dark:text-slate-50 truncate">
                          {p.name}
                        </h3>
                        {p.pinned && <Pin size={12} className="text-amber-500 flex-shrink-0" />}
                      </div>
                      <div className="flex items-center gap-1.5 mt-1 flex-wrap">
                        <span
                          className={`text-[11px] px-2 py-0.5 rounded-full font-medium ${
                            TRUST_COLORS[p.trust_level] || "bg-slate-700 text-slate-400"
                          }`}
                        >
                          {TRUST_LABELS[p.trust_level] || p.trust_level}
                        </span>
                        {p.team_size && (
                          <span className="text-[11px] text-slate-400">{p.team_size} 人</span>
                        )}
                        {(p.deal_count ?? 0) > 0 && (
                          <span className="text-[11px] px-1.5 py-0.5 rounded-full bg-green-500/10 text-green-500 font-medium">
                            {p.deal_count} 商機
                          </span>
                        )}
                        {p.tags && p.tags.slice(0, 2).map((tag) => (
                          <span key={tag.id} className="text-[10px] px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400">
                            {tag.name}
                          </span>
                        ))}
                      </div>
                    </div>
                    {!selectMode && (
                      <button
                        onClick={(e) => { e.preventDefault(); e.stopPropagation(); handleTogglePin(p.id, "partner"); }}
                        className={`p-1.5 rounded-lg transition-colors cursor-pointer flex-shrink-0 ${
                          p.pinned
                            ? "text-amber-500 hover:bg-amber-500/10"
                            : "text-slate-300 dark:text-slate-600 hover:text-amber-500 opacity-0 group-hover:opacity-100"
                        }`}
                        title={p.pinned ? "取消釘選" : "釘選"}
                      >
                        {p.pinned ? <PinOff size={16} /> : <Pin size={16} />}
                      </button>
                    )}
                  </div>
                </CardWrapper>
              );
            })}
          </div>
        )}
      </div>

      {/* Create modal */}
      {showCreateModal && (
        tab === "clients" ? (
          <CreateClientModal
            onClose={() => setShowCreateModal(false)}
            onCreated={() => {
              setShowCreateModal(false);
              loadData();
            }}
          />
        ) : (
          <CreatePartnerModal
            onClose={() => setShowCreateModal(false)}
            onCreated={() => {
              setShowCreateModal(false);
              loadData();
            }}
          />
        )
      )}
    </div>
  );
}

