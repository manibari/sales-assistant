"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  Loader2,
  Target,
  Building2,
  FileText,
  Lightbulb,
  Sparkles,
  Phone,
  Mail,
  Copy,
  Check,
  Calendar,
  ChevronRight,
  Users,
  Briefcase,
  MapPin,
  CheckSquare,
  Square,
  ClipboardList,
  Search,
} from "lucide-react";
import { nxApi } from "@/lib/nexus-api";

type Step = "filter" | "review" | "target" | "summary";

interface IndustryInfo {
  industry: string;
  case_studies: number;
  solutions: number;
}

interface RegionInfo {
  region: string;
  count: number;
}

interface TargetCompany {
  id: number;
  name: string;
  industry: string | null;
  region: string | null;
  status: string;
  deal_count: number;
  contact_count: number;
}

interface BatchCompany {
  id: number;
  name: string;
  industry: string | null;
  region: string | null;
  deal_count: number;
  contacts: { name: string; title: string | null; phone: string | null; email: string | null }[];
}

interface Contact {
  id: number;
  name: string;
  title: string | null;
  phone: string | null;
  email: string | null;
  line_id: string | null;
  role: string | null;
}

export default function OutreachPage() {
  const router = useRouter();
  const [step, setStep] = useState<Step>("filter");
  const [industries, setIndustries] = useState<IndustryInfo[]>([]);
  const [regions, setRegions] = useState<RegionInfo[]>([]);
  const [selectedIndustry, setSelectedIndustry] = useState("");
  const [selectedRegion, setSelectedRegion] = useState("");
  const [caseStudies, setCaseStudies] = useState<Record<string, unknown>[]>([]);
  const [solutions, setSolutions] = useState<Record<string, unknown>[]>([]);
  const [targets, setTargets] = useState<TargetCompany[]>([]);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [batchData, setBatchData] = useState<BatchCompany[]>([]);
  const [visitPlan, setVisitPlan] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [generatingPitch, setGeneratingPitch] = useState<number | null>(null);
  const [pitches, setPitches] = useState<Record<number, string>>({});
  const [copied, setCopied] = useState(false);

  // Load industries + regions on mount
  useEffect(() => {
    setLoading(true);
    Promise.all([
      nxApi.outreach.industries(),
      nxApi.outreach.regions(),
    ])
      .then(([ind, reg]) => {
        setIndustries(ind);
        setRegions(reg);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const canSearch = selectedIndustry || selectedRegion;

  const handleSearch = async () => {
    if (!canSearch) return;
    setLoading(true);
    try {
      const [cs, sol, tgt] = await Promise.all([
        selectedIndustry ? nxApi.outreach.caseStudies(selectedIndustry) : Promise.resolve([]),
        selectedIndustry ? nxApi.outreach.solutions(selectedIndustry) : Promise.resolve([]),
        nxApi.outreach.targets(selectedIndustry || undefined, selectedRegion || undefined),
      ]);
      setCaseStudies(cs);
      setSolutions(sol);
      setTargets(tgt);
      setSelectedIds(new Set());
      setStep("review");
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const toggleSelect = (id: number) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const selectAll = () => {
    if (selectedIds.size === targets.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(targets.map((t) => t.id)));
    }
  };

  const handleViewSummary = async () => {
    if (selectedIds.size === 0) return;
    setLoading(true);
    try {
      const data = await nxApi.outreach.batchSummary(Array.from(selectedIds));
      setBatchData(data);
      setVisitPlan(null);
      setStep("summary");
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateVisitPlan = async () => {
    setGenerating(true);
    setVisitPlan(null);
    try {
      const result = await nxApi.outreach.generateVisitPlan({
        client_ids: Array.from(selectedIds),
        region: selectedRegion || undefined,
        industry: selectedIndustry || undefined,
      });
      setVisitPlan(result.plan);
    } catch (err) {
      console.error(err);
    } finally {
      setGenerating(false);
    }
  };

  const handleGeneratePitch = async (company: BatchCompany) => {
    setGeneratingPitch(company.id);
    try {
      const result = await nxApi.outreach.generatePitch({
        target_company: company.name,
        target_industry: company.industry || selectedIndustry || "",
        include_knowledge: true,
      });
      if (result.pitch) {
        setPitches((prev) => ({ ...prev, [company.id]: result.pitch! }));
      }
    } catch (err) {
      console.error(err);
    } finally {
      setGeneratingPitch(null);
    }
  };

  const handleCopyList = () => {
    const lines = batchData.map((c) => {
      const contactStr = c.contacts
        .map((ct) => `${ct.name}${ct.title ? `(${ct.title})` : ""}${ct.phone ? ` ${ct.phone}` : ""}`)
        .join(", ");
      return `${c.name}｜${c.industry || "-"}｜${c.region || "-"}｜${c.deal_count} 商機｜${contactStr || "無聯絡人"}`;
    });
    navigator.clipboard.writeText(lines.join("\n"));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSchedule = () => {
    const today = new Date().toISOString().slice(0, 10);
    const names = batchData.map((c) => c.name).join("、");
    router.push(
      `/calendar/meeting/new?date=${today}&title=${encodeURIComponent(`出訪：${names.slice(0, 50)}`)}`
    );
  };

  return (
    <div className="flex flex-col h-full">
      <div className="h-14 px-4 flex items-center justify-between border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
        <div className="flex items-center gap-2">
          <Target size={20} className="text-blue-500" />
          <h1 className="text-xl font-bold text-slate-900 dark:text-slate-50">
            陌開工作台
          </h1>
        </div>
        <StepIndicator current={step} />
      </div>

      <div className="flex-1 px-4 py-4 overflow-auto max-w-2xl lg:max-w-4xl mx-auto w-full">
        {loading && (
          <div className="flex items-center justify-center py-12">
            <Loader2 size={20} className="animate-spin text-blue-500" />
          </div>
        )}

        {/* Step 1: Filter — Industry + Region */}
        {!loading && step === "filter" && (
          <div className="space-y-4">
            <p className="text-sm text-slate-500">選擇產業和/或區域，至少選一個</p>

            {/* Industry buttons */}
            <div>
              <h3 className="text-xs font-medium text-slate-500 mb-2 flex items-center gap-1.5">
                <Building2 size={12} />
                產業
              </h3>
              {industries.length === 0 ? (
                <p className="text-xs text-slate-400">尚無案例資料</p>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {industries.map((ind) => (
                    <button
                      key={ind.industry}
                      onClick={() =>
                        setSelectedIndustry((prev) =>
                          prev === ind.industry ? "" : ind.industry
                        )
                      }
                      className={`px-3 py-1.5 text-sm rounded-lg border cursor-pointer transition-colors ${
                        selectedIndustry === ind.industry
                          ? "bg-blue-500 text-white border-blue-500"
                          : "bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:border-blue-400"
                      }`}
                    >
                      {ind.industry}
                      <span className="ml-1 text-[10px] opacity-70">
                        {ind.case_studies}例
                      </span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Region buttons */}
            <div>
              <h3 className="text-xs font-medium text-slate-500 mb-2 flex items-center gap-1.5">
                <MapPin size={12} />
                區域
              </h3>
              {regions.length === 0 ? (
                <p className="text-xs text-slate-400">尚無區域資料（請在客戶資料中設定 region）</p>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {regions.map((r) => (
                    <button
                      key={r.region}
                      onClick={() =>
                        setSelectedRegion((prev) =>
                          prev === r.region ? "" : r.region
                        )
                      }
                      className={`px-3 py-1.5 text-sm rounded-lg border cursor-pointer transition-colors ${
                        selectedRegion === r.region
                          ? "bg-emerald-500 text-white border-emerald-500"
                          : "bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:border-emerald-400"
                      }`}
                    >
                      {r.region}
                      <span className="ml-1 text-[10px] opacity-70">
                        {r.count}家
                      </span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Search button */}
            <button
              onClick={handleSearch}
              disabled={!canSearch}
              className="w-full flex items-center justify-center gap-2 bg-blue-500 hover:bg-blue-600 disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold px-6 py-3 rounded-xl cursor-pointer transition-colors"
            >
              <Search size={18} />
              搜尋目標
            </button>
          </div>
        )}

        {/* Step 2: Review weapons + targets with multi-select */}
        {!loading && step === "review" && (
          <div className="space-y-4">
            <button
              onClick={() => setStep("filter")}
              className="text-xs text-blue-500 cursor-pointer hover:underline"
            >
              ← 返回篩選
            </button>

            <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-50">
              {[selectedIndustry, selectedRegion].filter(Boolean).join(" · ")} — 可用武器
            </h2>

            {/* Case studies */}
            {caseStudies.length > 0 && (
              <div className="space-y-2">
                <h3 className="text-xs font-medium text-slate-500 flex items-center gap-1.5">
                  <FileText size={12} />
                  成功案例
                </h3>
                {caseStudies.map((cs, i) => (
                  <div
                    key={i}
                    className="p-3 bg-green-500/5 border border-green-500/20 rounded-lg"
                  >
                    <p className="text-sm font-medium text-slate-900 dark:text-slate-50">
                      {String(cs.client || "未命名")}
                    </p>
                    <p className="text-xs text-green-600 dark:text-green-400 mt-0.5">
                      {String(cs.outcome || "")}
                    </p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-[10px] text-slate-400">
                        {(cs.solution_type as string[])?.join(", ")}
                      </span>
                      <span className="text-[10px] text-slate-400">
                        · {String(cs.duration || "")}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Solutions */}
            {solutions.length > 0 && (
              <div className="space-y-2">
                <h3 className="text-xs font-medium text-slate-500 flex items-center gap-1.5">
                  <Lightbulb size={12} />
                  適用方案
                </h3>
                {solutions.map((sol, i) => (
                  <div
                    key={i}
                    className="p-3 bg-blue-500/5 border border-blue-500/20 rounded-lg"
                  >
                    <p className="text-sm font-medium text-slate-900 dark:text-slate-50">
                      {String(sol.name || "未命名")}
                    </p>
                    <div className="flex items-center gap-3 mt-1 text-[10px] text-slate-400">
                      <span>預算：{String(sol.typical_budget || "?")}</span>
                      <span>期間：{String(sol.typical_duration || "?")}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Target companies with checkboxes */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-medium text-slate-500 flex items-center gap-1.5">
                  <Target size={12} />
                  目標公司 ({targets.length})
                </h3>
                {targets.length > 0 && (
                  <button
                    onClick={selectAll}
                    className="text-[10px] text-blue-500 cursor-pointer hover:underline"
                  >
                    {selectedIds.size === targets.length ? "取消全選" : "全選"}
                  </button>
                )}
              </div>
              {targets.length === 0 ? (
                <p className="text-xs text-slate-400 py-4 text-center">
                  無符合條件的客戶
                </p>
              ) : (
                targets.map((t) => (
                  <button
                    key={t.id}
                    onClick={() => toggleSelect(t.id)}
                    className={`w-full flex items-center gap-3 p-3 border rounded-lg cursor-pointer transition-colors text-left ${
                      selectedIds.has(t.id)
                        ? "bg-blue-500/5 border-blue-500/40"
                        : "bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-700 hover:border-blue-400"
                    }`}
                  >
                    {selectedIds.has(t.id) ? (
                      <CheckSquare size={16} className="text-blue-500 shrink-0" />
                    ) : (
                      <Square size={16} className="text-slate-300 shrink-0" />
                    )}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-slate-900 dark:text-slate-50">
                        {t.name}
                      </p>
                      <div className="flex items-center gap-2 mt-0.5 flex-wrap">
                        {t.region && (
                          <span className="inline-flex items-center gap-0.5 text-[10px] text-emerald-500">
                            <MapPin size={8} />
                            {t.region}
                          </span>
                        )}
                        {t.deal_count > 0 && (
                          <span className="inline-flex items-center gap-0.5 text-[10px] text-green-500">
                            <Briefcase size={8} />
                            {t.deal_count} 商機
                          </span>
                        )}
                        {t.contact_count > 0 && (
                          <span className="inline-flex items-center gap-0.5 text-[10px] text-slate-400">
                            <Users size={8} />
                            {t.contact_count} 聯絡人
                          </span>
                        )}
                      </div>
                    </div>
                  </button>
                ))
              )}
            </div>

            {/* Bottom bar */}
            {selectedIds.size > 0 && (
              <div className="sticky bottom-0 bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-700 -mx-4 px-4 py-3">
                <button
                  onClick={handleViewSummary}
                  className="w-full flex items-center justify-center gap-2 bg-blue-500 hover:bg-blue-600 text-white font-semibold px-6 py-3 rounded-xl cursor-pointer transition-colors"
                >
                  <ClipboardList size={18} />
                  已選 {selectedIds.size} 家 → 查看出訪總覽
                </button>
              </div>
            )}
          </div>
        )}

        {/* Step 3: Target detail — individual company (kept for single-company pitch) */}
        {!loading && step === "target" && (
          <div className="space-y-4">
            <button
              onClick={() => setStep("review")}
              className="text-xs text-blue-500 cursor-pointer hover:underline"
            >
              ← 返回列表
            </button>
            <p className="text-sm text-slate-400">（個別公司模式已整合到批次總覽中）</p>
          </div>
        )}

        {/* Step 4: Batch Summary */}
        {!loading && step === "summary" && (
          <div className="space-y-4">
            <button
              onClick={() => setStep("review")}
              className="text-xs text-blue-500 cursor-pointer hover:underline"
            >
              ← 返回目標選擇
            </button>

            <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-50">
              出訪總覽（{batchData.length} 家）
            </h2>

            {/* Company cards */}
            {batchData.map((c) => (
              <div
                key={c.id}
                className="p-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl space-y-3"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-lg bg-blue-500/10 flex items-center justify-center">
                      <Building2 size={16} className="text-blue-500" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-slate-900 dark:text-slate-50">
                        {c.name}
                      </p>
                      <div className="flex items-center gap-2 mt-0.5">
                        {c.industry && (
                          <span className="text-[10px] text-slate-400">{c.industry}</span>
                        )}
                        {c.region && (
                          <span className="inline-flex items-center gap-0.5 text-[10px] text-emerald-500">
                            <MapPin size={8} />
                            {c.region}
                          </span>
                        )}
                        <span className="text-[10px] text-slate-400">{c.deal_count} 商機</span>
                      </div>
                    </div>
                  </div>
                  <button
                    onClick={() => handleGeneratePitch(c)}
                    disabled={generatingPitch === c.id}
                    className="text-xs text-blue-500 hover:text-blue-600 cursor-pointer disabled:opacity-50 flex items-center gap-1"
                  >
                    {generatingPitch === c.id ? (
                      <Loader2 size={12} className="animate-spin" />
                    ) : (
                      <Sparkles size={12} />
                    )}
                    生成說帖
                  </button>
                </div>

                {/* Contacts */}
                {c.contacts.length > 0 && (
                  <div className="space-y-1">
                    {c.contacts.map((ct, i) => (
                      <div key={i} className="flex items-center justify-between text-xs">
                        <span className="text-slate-700 dark:text-slate-300">
                          {ct.name}
                          {ct.title && (
                            <span className="text-slate-400 ml-1">({ct.title})</span>
                          )}
                        </span>
                        <div className="flex items-center gap-2">
                          {ct.phone && (
                            <a
                              href={`tel:${ct.phone}`}
                              className="text-green-500 hover:text-green-600 flex items-center gap-0.5"
                            >
                              <Phone size={10} />
                              {ct.phone}
                            </a>
                          )}
                          {ct.email && (
                            <a
                              href={`mailto:${ct.email}`}
                              className="text-blue-500 hover:text-blue-600"
                            >
                              <Mail size={10} />
                            </a>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                {c.contacts.length === 0 && (
                  <p className="text-[10px] text-slate-400">無聯絡人</p>
                )}

                {/* Per-company pitch */}
                {pitches[c.id] && (
                  <div className="p-3 bg-blue-500/5 border border-blue-500/20 rounded-lg">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-[10px] text-blue-500 font-medium flex items-center gap-1">
                        <Sparkles size={10} />
                        說帖
                      </span>
                      <button
                        onClick={() => {
                          navigator.clipboard.writeText(pitches[c.id]);
                          setCopied(true);
                          setTimeout(() => setCopied(false), 2000);
                        }}
                        className="text-[10px] text-slate-400 hover:text-blue-500 cursor-pointer"
                      >
                        複製
                      </button>
                    </div>
                    <p className="text-xs text-slate-700 dark:text-slate-300 whitespace-pre-wrap leading-relaxed">
                      {pitches[c.id]}
                    </p>
                  </div>
                )}
              </div>
            ))}

            {/* Action buttons */}
            <div className="flex gap-2">
              <button
                onClick={handleGenerateVisitPlan}
                disabled={generating}
                className="flex-1 flex items-center justify-center gap-2 bg-blue-500 hover:bg-blue-600 disabled:opacity-50 text-white font-semibold px-4 py-3 rounded-xl cursor-pointer transition-colors"
              >
                {generating ? (
                  <Loader2 size={16} className="animate-spin" />
                ) : (
                  <Sparkles size={16} />
                )}
                {generating ? "生成中..." : "AI 生成出訪計畫"}
              </button>
              <button
                onClick={handleCopyList}
                className="flex items-center justify-center gap-2 px-4 py-3 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 font-medium rounded-xl cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
              >
                {copied ? <Check size={16} /> : <Copy size={16} />}
                {copied ? "已複製" : "複製清單"}
              </button>
            </div>

            {/* Visit plan */}
            {visitPlan && (
              <div className="p-4 bg-white dark:bg-slate-900 border border-blue-500/30 rounded-xl">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-50 flex items-center gap-1.5">
                    <Sparkles size={14} className="text-blue-500" />
                    出訪計畫
                  </h3>
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(visitPlan);
                      setCopied(true);
                      setTimeout(() => setCopied(false), 2000);
                    }}
                    className="flex items-center gap-1 text-xs text-slate-400 hover:text-blue-500 cursor-pointer transition-colors"
                  >
                    {copied ? <Check size={12} /> : <Copy size={12} />}
                    {copied ? "已複製" : "複製"}
                  </button>
                </div>
                <div className="text-sm text-slate-700 dark:text-slate-300 whitespace-pre-wrap leading-relaxed">
                  {visitPlan}
                </div>
              </div>
            )}

            {/* Schedule button */}
            <button
              onClick={handleSchedule}
              className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-green-500 hover:bg-green-600 text-white font-medium rounded-xl cursor-pointer transition-colors"
            >
              <Calendar size={16} />
              排程拜訪
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

function StepIndicator({ current }: { current: Step }) {
  const steps: { key: Step; label: string }[] = [
    { key: "filter", label: "篩選" },
    { key: "review", label: "武器" },
    { key: "target", label: "目標" },
    { key: "summary", label: "總覽" },
  ];
  const currentIdx = steps.findIndex((s) => s.key === current);
  // Map "target" step to "review" visually since target is now merged into review
  const idx = current === "target" ? 1 : currentIdx;

  return (
    <div className="flex items-center gap-1">
      {steps
        .filter((s) => s.key !== "target")
        .map((s, i) => (
          <div key={s.key} className="flex items-center gap-1">
            <span
              className={`text-[10px] px-2 py-0.5 rounded-full ${
                i <=
                (current === "summary"
                  ? 2
                  : current === "review" || current === "target"
                    ? 1
                    : 0)
                  ? "bg-blue-500/10 text-blue-500 font-medium"
                  : "bg-slate-100 dark:bg-slate-800 text-slate-400"
              }`}
            >
              {s.label}
            </span>
            {i < 2 && (
              <ChevronRight size={10} className="text-slate-300" />
            )}
          </div>
        ))}
    </div>
  );
}
