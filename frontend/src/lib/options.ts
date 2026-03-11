export const INDUSTRIES = [
  { label: "食品業", value: "food" },
  { label: "石化業", value: "petrochemical" },
  { label: "半導體", value: "semiconductor" },
  { label: "製造業", value: "manufacturing" },
  { label: "科技", value: "tech" },
  { label: "金融", value: "finance" },
  { label: "醫療", value: "healthcare" },
  { label: "系統整合", value: "system_integration" },
  { label: "交通運輸", value: "transportation" },
  { label: "其他", value: "other" },
];

export const BUDGET_PRESETS = [
  { label: "< 10 萬", amount: 100000 },
  { label: "10-50 萬", amount: 300000 },
  { label: "50-100 萬", amount: 750000 },
  { label: "100-500 萬", amount: 3000000 },
  { label: "500 萬+", amount: 5000000 },
];

export function formatBudget(amount: number | null | undefined): string {
  if (!amount) return "—";
  const wan = amount / 10000;
  if (wan >= 10000) return `${(wan / 10000).toFixed(1)} 億`;
  if (wan >= 1) return `${wan.toFixed(0)} 萬`;
  return `${amount.toLocaleString()} 元`;
}
