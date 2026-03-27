// 經濟部行業標準分類（第11次修訂）
export const INDUSTRIES = [
  // C 製造業
  { label: "C08 食品製造業", value: "C08 食品製造業" },
  { label: "C11 紡織業", value: "C11 紡織業" },
  { label: "C15 紙漿紙製品製造業", value: "C15 紙漿紙製品製造業" },
  { label: "C16 印刷及資料儲存媒體複製業", value: "C16 印刷及資料儲存媒體複製業" },
  { label: "C17 石油及煤製品製造業", value: "C17 石油及煤製品製造業" },
  { label: "C18 化學材料製造業", value: "C18 化學材料製造業" },
  { label: "C21 橡膠製品製造業", value: "C21 橡膠製品製造業" },
  { label: "C22 塑膠製品製造業", value: "C22 塑膠製品製造業" },
  { label: "C23 非金屬礦物製品製造業", value: "C23 非金屬礦物製品製造業" },
  { label: "C24 基本金屬製造業", value: "C24 基本金屬製造業" },
  { label: "C24 藥品製造業", value: "C24 藥品製造業" },
  { label: "C25 金屬製品製造業", value: "C25 金屬製品製造業" },
  { label: "C26 電子零組件製造業", value: "C26 電子零組件製造業" },
  { label: "C27 電腦電子光學製品製造業", value: "C27 電腦電子光學製品製造業" },
  { label: "C28 電力設備製造業", value: "C28 電力設備製造業" },
  { label: "C29 機械設備製造業", value: "C29 機械設備製造業" },
  { label: "C30 汽車及零件製造業", value: "C30 汽車及零件製造業" },
  { label: "C31 其他運輸工具製造業", value: "C31 其他運輸工具製造業" },
  // D-E 公用事業
  { label: "D01 電力供應業", value: "D01 電力供應業" },
  { label: "E38 廢棄物處理業", value: "E38 廢棄物處理業" },
  // F 營建
  { label: "F41 建築工程業", value: "F41 建築工程業" },
  // H 運輸
  { label: "H49 陸上運輸業", value: "H49 陸上運輸業" },
  { label: "H51 航空運輸業", value: "H51 航空運輸業" },
  // J 資通訊
  { label: "J61 電信業", value: "J61 電信業" },
  { label: "J62 電腦程式設計及資訊服務業", value: "J62 電腦程式設計及資訊服務業" },
  // K 金融
  { label: "K64 金融服務業", value: "K64 金融服務業" },
  // L 不動產
  { label: "L68 不動產業", value: "L68 不動產業" },
  // M 專業服務
  { label: "M72 研究發展服務業", value: "M72 研究發展服務業" },
  // O 公共行政
  { label: "O84 公共行政", value: "O84 公共行政" },
  // P 教育
  { label: "P85 教育業", value: "P85 教育業" },
];

// Short display label: strip the code prefix for UI
export function industryLabel(value: string | null): string {
  if (!value) return "—";
  // Handle legacy values
  const legacy: Record<string, string> = {
    food: "食品製造業", petrochemical: "化學材料製造業", semiconductor: "電子零組件製造業",
    manufacturing: "製造業", tech: "電腦電子光學", finance: "金融服務業",
    healthcare: "醫療", transportation: "運輸業", other: "其他",
  };
  if (legacy[value]) return legacy[value];
  // Strip "CXX " prefix for display
  return value.replace(/^[A-Z]\d+\s/, "");
}

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
