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
} from "lucide-react";
import { nxApi } from "@/lib/nexus-api";

type Step = "industry" | "review" | "target" | "pitch";

interface IndustryInfo {
  industry: string;
  case_studies: number;
  solutions: number;
}

interface TargetCompany {
  id: number;
  name: string;
  industry: string | null;
  status: string;
  deal_count: number;
  contact_count: number;
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
  const [step, setStep] = useState<Step>("industry");
  const [industries, setIndustries] = useState<IndustryInfo[]>([]);
  const [selectedIndustry, setSelectedIndustry] = useState("");
  const [caseStudies, setCaseStudies] = useState<Record<string, unknown>[]>([]);
  const [solutions, setSolutions] = useState<Record<string, unknown>[]>([]);
  const [targets, setTargets] = useState<TargetCompany[]>([]);
  const [selectedTarget, setSelectedTarget] = useState<TargetCompany | null>(null);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [pitch, setPitch] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [copied, setCopied] = useState(false);

  // Load industries on mount
  useEffect(() => {
    setLoading(true);
    nxApi.outreach
      .industries()
      .then(setIndustries)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const handleSelectIndustry = async (industry: string) => {
    setSelectedIndustry(industry);
    setLoading(true);
    try {
      const [cs, sol, tgt] = await Promise.all([
        nxApi.outreach.caseStudies(industry),
        nxApi.outreach.solutions(industry),
        nxApi.outreach.targets(industry),
      ]);
      setCaseStudies(cs);
      setSolutions(sol);
      setTargets(tgt);
      setStep("review");
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectTarget = async (target: TargetCompany) => {
    setSelectedTarget(target);
    setStep("target");
    try {
      const ct = await nxApi.outreach.contacts(target.id);
      setContacts(ct);
    } catch {
      setContacts([]);
    }
  };

  const handleGeneratePitch = async () => {
    if (!selectedTarget) return;
    setGenerating(true);
    setPitch(null);
    try {
      const result = await nxApi.outreach.generatePitch({
        target_company: selectedTarget.name,
        target_industry: selectedIndustry,
        include_knowledge: true,
      });
      setPitch(result.pitch);
      setStep("pitch");
    } catch (err) {
      console.error(err);
    } finally {
      setGenerating(false);
    }
  };

  const handleCopy = () => {
    if (pitch) {
      navigator.clipboard.writeText(pitch);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleSchedule = () => {
    if (!selectedTarget) return;
    const today = new Date().toISOString().slice(0, 10);
    router.push(
      `/calendar/meeting/new?date=${today}&title=${encodeURIComponent(`陌開：${selectedTarget.name}`)}`
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

        {/* Step 1: Select Industry */}
        {!loading && step === "industry" && (
          <div className="space-y-3">
            <p className="text-sm text-slate-500">選擇目標產業，系統會配對案例和方案</p>
            {industries.length === 0 ? (
              <div className="text-center py-12 text-slate-400 text-sm">
                尚無案例資料，請先在 materials/case-studies/ 新增案例
              </div>
            ) : (
              <div className="grid gap-2">
                {industries.map((ind) => (
                  <button
                    key={ind.industry}
                    onClick={() => handleSelectIndustry(ind.industry)}
                    className="flex items-center justify-between p-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl hover:border-blue-500 cursor-pointer transition-colors text-left"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center">
                        <Building2 size={18} className="text-blue-500" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-slate-900 dark:text-slate-50">
                          {ind.industry}
                        </p>
                        <p className="text-[11px] text-slate-400">
                          {ind.case_studies} 案例 · {ind.solutions} 方案
                        </p>
                      </div>
                    </div>
                    <ChevronRight size={16} className="text-slate-400" />
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Step 2: Review case studies + solutions */}
        {!loading && step === "review" && (
          <div className="space-y-4">
            <button
              onClick={() => setStep("industry")}
              className="text-xs text-blue-500 cursor-pointer hover:underline"
            >
              ← 返回選產業
            </button>

            <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-50">
              {selectedIndustry} — 可用武器
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

            {/* Target companies */}
            <div className="space-y-2">
              <h3 className="text-xs font-medium text-slate-500 flex items-center gap-1.5">
                <Target size={12} />
                目標公司 ({targets.length})
              </h3>
              {targets.length === 0 ? (
                <p className="text-xs text-slate-400 py-4 text-center">
                  尚無 {selectedIndustry} 的客戶資料
                </p>
              ) : (
                targets.map((t) => (
                  <button
                    key={t.id}
                    onClick={() => handleSelectTarget(t)}
                    className="w-full flex items-center justify-between p-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg hover:border-blue-500 cursor-pointer transition-colors text-left"
                  >
                    <div className="flex items-center gap-2">
                      <Building2 size={14} className="text-slate-400" />
                      <div>
                        <p className="text-sm text-slate-900 dark:text-slate-50">
                          {t.name}
                        </p>
                        <div className="flex items-center gap-2 mt-0.5">
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
                    </div>
                    <ChevronRight size={14} className="text-slate-400" />
                  </button>
                ))
              )}
            </div>
          </div>
        )}

        {/* Step 3: Target detail + contacts */}
        {!loading && step === "target" && selectedTarget && (
          <div className="space-y-4">
            <button
              onClick={() => setStep("review")}
              className="text-xs text-blue-500 cursor-pointer hover:underline"
            >
              ← 返回列表
            </button>

            <div className="p-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center">
                  <Building2 size={18} className="text-blue-500" />
                </div>
                <div>
                  <p className="text-base font-medium text-slate-900 dark:text-slate-50">
                    {selectedTarget.name}
                  </p>
                  <p className="text-xs text-slate-400">
                    {selectedTarget.industry || selectedIndustry}
                  </p>
                </div>
              </div>
            </div>

            {/* Contacts */}
            {contacts.length > 0 && (
              <div className="space-y-2">
                <h3 className="text-xs font-medium text-slate-500">聯絡人</h3>
                {contacts.map((c) => (
                  <div
                    key={c.id}
                    className="p-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-slate-900 dark:text-slate-50">
                          {c.name}
                        </p>
                        {c.title && (
                          <p className="text-[11px] text-slate-400">{c.title}</p>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        {c.phone && (
                          <a
                            href={`tel:${c.phone}`}
                            className="p-1.5 rounded-lg bg-green-500/10 text-green-500 hover:bg-green-500/20 transition-colors"
                          >
                            <Phone size={14} />
                          </a>
                        )}
                        {c.email && (
                          <a
                            href={`mailto:${c.email}`}
                            className="p-1.5 rounded-lg bg-blue-500/10 text-blue-500 hover:bg-blue-500/20 transition-colors"
                          >
                            <Mail size={14} />
                          </a>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {contacts.length === 0 && (
              <p className="text-xs text-slate-400 text-center py-4">
                尚無聯絡人資料
              </p>
            )}

            {/* Generate pitch button */}
            <button
              onClick={handleGeneratePitch}
              disabled={generating}
              className="w-full flex items-center justify-center gap-2 bg-blue-500 hover:bg-blue-600 disabled:opacity-50 text-white font-semibold px-6 py-3 rounded-xl cursor-pointer transition-colors"
            >
              {generating ? (
                <Loader2 size={18} className="animate-spin" />
              ) : (
                <Sparkles size={18} />
              )}
              {generating ? "生成說帖中..." : "AI 生成說帖"}
            </button>
          </div>
        )}

        {/* Step 4: Pitch result */}
        {!loading && step === "pitch" && pitch && (
          <div className="space-y-4">
            <button
              onClick={() => setStep("target")}
              className="text-xs text-blue-500 cursor-pointer hover:underline"
            >
              ← 返回
            </button>

            <div className="p-4 bg-white dark:bg-slate-900 border border-blue-500/30 rounded-xl">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-50 flex items-center gap-1.5">
                  <Sparkles size={14} className="text-blue-500" />
                  說帖 — {selectedTarget?.name}
                </h3>
                <button
                  onClick={handleCopy}
                  className="flex items-center gap-1 text-xs text-slate-400 hover:text-blue-500 cursor-pointer transition-colors"
                >
                  {copied ? <Check size={12} /> : <Copy size={12} />}
                  {copied ? "已複製" : "複製"}
                </button>
              </div>
              <div className="text-sm text-slate-700 dark:text-slate-300 whitespace-pre-wrap leading-relaxed">
                {pitch}
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-2">
              <button
                onClick={handleSchedule}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-green-500 hover:bg-green-600 text-white font-medium rounded-xl cursor-pointer transition-colors"
              >
                <Calendar size={16} />
                排程拜訪
              </button>
              <button
                onClick={handleGeneratePitch}
                disabled={generating}
                className="flex items-center justify-center gap-2 px-4 py-3 border border-blue-500/30 text-blue-500 font-medium rounded-xl cursor-pointer hover:bg-blue-500/10 transition-colors disabled:opacity-50"
              >
                {generating ? (
                  <Loader2 size={16} className="animate-spin" />
                ) : (
                  <Sparkles size={16} />
                )}
                重新生成
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function StepIndicator({ current }: { current: Step }) {
  const steps: { key: Step; label: string }[] = [
    { key: "industry", label: "產業" },
    { key: "review", label: "武器" },
    { key: "target", label: "目標" },
    { key: "pitch", label: "說帖" },
  ];
  const idx = steps.findIndex((s) => s.key === current);

  return (
    <div className="flex items-center gap-1">
      {steps.map((s, i) => (
        <div key={s.key} className="flex items-center gap-1">
          <span
            className={`text-[10px] px-2 py-0.5 rounded-full ${
              i <= idx
                ? "bg-blue-500/10 text-blue-500 font-medium"
                : "bg-slate-100 dark:bg-slate-800 text-slate-400"
            }`}
          >
            {s.label}
          </span>
          {i < steps.length - 1 && (
            <ChevronRight size={10} className="text-slate-300" />
          )}
        </div>
      ))}
    </div>
  );
}
