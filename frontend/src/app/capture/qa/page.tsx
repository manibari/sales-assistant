"use client";

import { useState, useEffect, useCallback, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { TopBar } from "@/components/top-bar";
import { Check, ChevronRight, Loader2 } from "lucide-react";
import { nxApi, type NxIntel } from "@/lib/nexus-api";

// --- Q&A Flow Definition ---

interface QaQuestion {
  id: string;
  question: string;
  options: { label: string; value: string }[];
  multiSelect?: boolean;
  skipLabel?: string;
  tbdQuestion?: string; // TBD text if skipped
}

const ROLE_QUESTION: QaQuestion = {
  id: "role",
  question: "他是什麼角色？",
  options: [
    { label: "客戶", value: "client" },
    { label: "夥伴", value: "partner" },
    { label: "SI", value: "si" },
    { label: "其他", value: "other" },
  ],
  skipLabel: "稍後再說",
  tbdQuestion: "確認角色",
};

const CLIENT_QUESTIONS: QaQuestion[] = [
  {
    id: "industry",
    question: "什麼產業？",
    options: [
      { label: "食品業", value: "food" },
      { label: "石化業", value: "petrochemical" },
      { label: "半導體", value: "semiconductor" },
      { label: "製造業", value: "manufacturing" },
      { label: "其他", value: "other" },
    ],
    skipLabel: "稍後再問",
    tbdQuestion: "確認產業別",
  },
  {
    id: "pain_points",
    question: "已知痛點？",
    multiSelect: true,
    options: [
      { label: "產線自動化", value: "automation" },
      { label: "品質檢測 (AOI)", value: "aoi" },
      { label: "能源管理", value: "energy" },
      { label: "安全監控", value: "safety" },
      { label: "ERP/系統整合", value: "erp" },
      { label: "IoT 資料收集", value: "iot" },
    ],
    skipLabel: "稍後再問",
    tbdQuestion: "確認客戶痛點",
  },
  {
    id: "nda_status",
    question: "NDA 狀態？",
    options: [
      { label: "尚未開始", value: "pending" },
      { label: "進行中", value: "in_progress" },
      { label: "已簽署", value: "signed" },
      { label: "不需要", value: "not_required" },
    ],
  },
  {
    id: "mou_status",
    question: "MOU 狀態？",
    options: [
      { label: "尚未開始", value: "pending" },
      { label: "進行中", value: "in_progress" },
      { label: "已簽署", value: "signed" },
      { label: "不需要", value: "not_required" },
    ],
  },
  {
    id: "budget",
    question: "預估預算範圍？",
    options: [
      { label: "< 100K", value: "<100K" },
      { label: "100K - 500K", value: "100-500K" },
      { label: "500K - 1M", value: "500K-1M" },
      { label: "1M+", value: "1M+" },
      { label: "未知", value: "unknown" },
    ],
  },
];

const PARTNER_QUESTIONS: QaQuestion[] = [
  {
    id: "capabilities",
    question: "能力標籤？",
    multiSelect: true,
    options: [
      { label: "IoT", value: "iot" },
      { label: "影像辨識", value: "vision" },
      { label: "ERP", value: "erp" },
      { label: "自動控制", value: "auto_ctrl" },
      { label: "資安", value: "security" },
      { label: "ML/AI", value: "ml_ai" },
    ],
    skipLabel: "稍後再問",
    tbdQuestion: "確認夥伴能力",
  },
  {
    id: "industry_exp",
    question: "產業經驗？",
    multiSelect: true,
    options: [
      { label: "食品業", value: "food" },
      { label: "石化業", value: "petrochemical" },
      { label: "半導體", value: "semiconductor" },
      { label: "製造業", value: "manufacturing" },
    ],
    skipLabel: "稍後再問",
    tbdQuestion: "確認產業經驗",
  },
  {
    id: "team_size",
    question: "團隊規模？",
    options: [
      { label: "1-10 人", value: "1-10" },
      { label: "10-50 人", value: "10-50" },
      { label: "50-200 人", value: "50-200" },
      { label: "200+ 人", value: "200+" },
    ],
  },
];

// --- Component ---

function QaFlow() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const intelId = Number(searchParams.get("id"));

  const [intel, setIntel] = useState<NxIntel | null>(null);
  const [questions, setQuestions] = useState<QaQuestion[]>([ROLE_QUESTION]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string | string[]>>({});
  const [selected, setSelected] = useState<string[]>([]);
  const [done, setDone] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (intelId) {
      nxApi.intel.get(intelId).then(setIntel).catch(console.error);
    }
  }, [intelId]);

  const currentQ = questions[currentIndex];
  const totalSteps = questions.length;
  const progress = ((currentIndex + 1) / totalSteps) * 100;

  const handleSelect = (value: string) => {
    if (currentQ?.multiSelect) {
      setSelected((prev) =>
        prev.includes(value) ? prev.filter((v) => v !== value) : [...prev, value]
      );
    } else {
      // Single select — advance immediately
      processAnswer(value);
    }
  };

  const processAnswer = useCallback(
    (answer: string | string[]) => {
      if (!currentQ) return;
      const newAnswers = { ...answers, [currentQ.id]: answer };
      setAnswers(newAnswers);

      // If role question, determine branch
      if (currentQ.id === "role") {
        const role = typeof answer === "string" ? answer : answer[0];
        if (role === "client") {
          setQuestions([ROLE_QUESTION, ...CLIENT_QUESTIONS]);
        } else if (role === "partner") {
          setQuestions([ROLE_QUESTION, ...PARTNER_QUESTIONS]);
        } else {
          // SI / other — done after role
          finishFlow(newAnswers);
          return;
        }
      }

      // Move to next question or finish
      if (currentIndex < questions.length - 1) {
        setCurrentIndex(currentIndex + 1);
        setSelected([]);
      } else {
        finishFlow(newAnswers);
      }
    },
    [currentQ, answers, currentIndex, questions.length]
  );

  const handleMultiConfirm = () => {
    if (selected.length > 0) {
      processAnswer(selected);
    }
  };

  const handleSkip = async () => {
    if (!currentQ) return;
    // Create TBD for skipped question
    if (currentQ.tbdQuestion && intelId) {
      try {
        await nxApi.tbd.create({
          question: currentQ.tbdQuestion,
          linked_type: "contact",
          linked_id: intelId,
          source: "skip",
        });
      } catch (err) {
        console.error("Failed to create TBD:", err);
      }
    }

    // Same branching logic for role skip
    if (currentQ.id === "role") {
      finishFlow(answers);
      return;
    }

    if (currentIndex < questions.length - 1) {
      setCurrentIndex(currentIndex + 1);
      setSelected([]);
    } else {
      finishFlow(answers);
    }
  };

  const finishFlow = async (finalAnswers: Record<string, string | string[]>) => {
    setSaving(true);
    try {
      // Confirm intel with parsed answers
      await nxApi.intel.confirm(intelId, JSON.stringify(finalAnswers));

      // Create client/partner if role was answered
      const role = finalAnswers.role;
      if (role === "client" && intel) {
        const client = await nxApi.clients.create({
          name: `Intel #${intelId}`,
          industry: finalAnswers.industry as string,
          budget_range: finalAnswers.budget as string,
        });

        // Update NDA/MOU if answered
        // (simplified — in full version would update document records)
        console.log("Client created:", client.id);
      } else if (role === "partner" && intel) {
        const partner = await nxApi.partners.create({
          name: `Intel #${intelId}`,
          team_size: finalAnswers.team_size as string,
        });
        console.log("Partner created:", partner.id);
      }

      setDone(true);
    } catch (err) {
      console.error("Failed to finish flow:", err);
    } finally {
      setSaving(false);
    }
  };

  // --- Render ---

  if (!intelId) {
    return (
      <div className="flex flex-col h-full">
        <TopBar title="Q&A" />
        <div className="flex-1 flex items-center justify-center text-slate-500">
          Missing intel ID
        </div>
      </div>
    );
  }

  if (done) {
    return (
      <div className="flex flex-col h-full">
        <TopBar title="完成" />
        <div className="flex-1 flex flex-col items-center justify-center gap-6 px-4">
          <div className="w-16 h-16 rounded-full bg-green-500/10 flex items-center justify-center">
            <Check size={32} className="text-green-500" />
          </div>
          <div className="text-center">
            <h2 className="text-xl font-bold text-slate-900 dark:text-slate-50">
              情報已確認
            </h2>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-2">
              資料已儲存，可在情報 Feed 中查看
            </p>
          </div>
          <div className="flex gap-3 w-full max-w-xs">
            <button
              onClick={() => router.push("/capture")}
              className="flex-1 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-700 font-medium px-6 py-3 rounded-lg min-h-[44px] cursor-pointer transition-colors duration-200"
            >
              再加一筆
            </button>
            <button
              onClick={() => router.push("/intel")}
              className="flex-1 bg-blue-500 hover:bg-blue-600 text-white font-semibold px-6 py-3 rounded-lg min-h-[44px] active:scale-[0.98] transition-all duration-200 cursor-pointer"
            >
              查看情報
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <TopBar title="情報問答" />

      <div className="flex-1 px-4 py-6 flex flex-col max-w-2xl mx-auto w-full">
        {/* Progress bar */}
        <div className="mb-6">
          <div className="flex justify-between text-[11px] text-slate-400 dark:text-slate-500 mb-2">
            <span>
              問題 {currentIndex + 1} / {totalSteps}
            </span>
            <span>{Math.round(progress)}%</span>
          </div>
          <div className="h-1 bg-slate-200 dark:bg-slate-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-500 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Raw input preview */}
        {intel && currentIndex === 0 && (
          <div className="mb-6 p-4 bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl">
            <p className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-2">
              原始輸入
            </p>
            <p className="text-sm text-slate-700 dark:text-slate-300 line-clamp-3">
              {intel.raw_input}
            </p>
          </div>
        )}

        {/* Question */}
        {currentQ && (
          <div className="flex-1 flex flex-col">
            <h2 className="text-xl md:text-2xl font-bold text-slate-900 dark:text-slate-50 mb-6">
              {currentQ.question}
            </h2>

            {/* Options grid */}
            <div className="grid grid-cols-2 gap-2">
              {currentQ.options.map((opt) => {
                const isSelected = currentQ.multiSelect
                  ? selected.includes(opt.value)
                  : answers[currentQ.id] === opt.value;

                return (
                  <button
                    key={opt.value}
                    onClick={() => handleSelect(opt.value)}
                    className={`min-h-[44px] px-4 py-3 text-sm font-medium rounded-lg border transition-colors duration-200 cursor-pointer ${
                      isSelected
                        ? "border-blue-500 bg-blue-500/10 text-blue-500 dark:text-blue-400"
                        : "bg-slate-100 dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-50 hover:border-blue-500 hover:bg-slate-200 dark:hover:bg-slate-700"
                    }`}
                  >
                    {currentQ.multiSelect && isSelected && (
                      <Check size={14} className="inline mr-1.5 -mt-0.5" />
                    )}
                    {opt.label}
                  </button>
                );
              })}
            </div>

            {/* Multi-select confirm button */}
            {currentQ.multiSelect && selected.length > 0 && (
              <button
                onClick={handleMultiConfirm}
                className="mt-4 w-full bg-blue-500 hover:bg-blue-600 text-white font-semibold px-6 py-3 rounded-lg min-h-[44px] active:scale-[0.98] transition-all duration-200 cursor-pointer"
              >
                確認 ({selected.length})
              </button>
            )}
          </div>
        )}

        {/* Skip button */}
        {currentQ?.skipLabel && (
          <div className="mt-4 flex justify-end">
            <button
              onClick={handleSkip}
              className="text-slate-400 dark:text-slate-500 hover:text-slate-600 dark:hover:text-slate-300 text-sm py-2 flex items-center gap-1 cursor-pointer transition-colors duration-200"
            >
              {currentQ.skipLabel}
              <ChevronRight size={16} strokeWidth={1.5} />
            </button>
          </div>
        )}

        {/* Saving overlay */}
        {saving && (
          <div className="fixed inset-0 bg-slate-950/50 flex items-center justify-center z-50">
            <div className="bg-white dark:bg-slate-900 rounded-xl p-6 flex flex-col items-center gap-3">
              <Loader2 size={24} className="animate-spin text-blue-500" />
              <span className="text-sm text-slate-500">儲存中...</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function QaPage() {
  return (
    <Suspense
      fallback={
        <div className="flex items-center justify-center h-full">
          <Loader2 size={24} className="animate-spin text-blue-500" />
        </div>
      }
    >
      <QaFlow />
    </Suspense>
  );
}
