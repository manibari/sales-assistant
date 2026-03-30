export const STAGE_ORDER = ["L0", "L1", "L2", "L3", "L4", "L5", "L6", "L7"];

export const STAGE_LABELS: Record<string, string> = {
  L0: "L0 客戶開發",
  L1: "L1 等待追蹤",
  L2: "L2 提案",
  L3: "L3 確認意願",
  L4: "L4 執行 POC",
  L5: "L5 完成 POC",
  L6: "L6 議價",
  L7: "L7 簽約",
  LOST: "遺失",
  HOLD: "擱置",
};

export const STAGE_INDEX: Record<string, number> = {
  L0: 0, L1: 1, L2: 2, L3: 3, L4: 4, L5: 5, L6: 6, L7: 7, LOST: 8, HOLD: 9,
};

export const STAGE_BAR_COLORS: Record<string, string> = {
  L0: "bg-slate-400",
  L1: "bg-blue-400",
  L2: "bg-cyan-400",
  L3: "bg-indigo-400",
  L4: "bg-amber-400",
  L5: "bg-orange-400",
  L6: "bg-yellow-400",
  L7: "bg-green-500",
  LOST: "bg-red-500",
  HOLD: "bg-gray-400",
};

export const MEDDIC_LABELS: Record<string, string> = {
  metrics: "Metrics (量化指標)",
  economic_buyer: "Economic Buyer (經濟決策者)",
  decision_criteria: "Decision Criteria (決策標準)",
  decision_process: "Decision Process (決策流程)",
  identify_pain: "Identify Pain (痛點辨識)",
  champion: "Champion (內部擁護者)",
};

export const CLOSE_REASONS = [
  { label: "預算不足", value: "budget" },
  { label: "時程不合", value: "timing" },
  { label: "選擇競品", value: "competitor" },
  { label: "需求消失", value: "no_need" },
  { label: "其他", value: "other" },
];
