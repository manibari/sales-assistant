"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { TopBar } from "@/components/top-bar";
import { Camera, Type, ArrowRight, Loader2 } from "lucide-react";
import { nxApi } from "@/lib/nexus-api";

export default function CapturePage() {
  const router = useRouter();
  const [inputText, setInputText] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!inputText.trim()) return;
    setLoading(true);
    try {
      const intel = await nxApi.intel.create({
        raw_input: inputText.trim(),
        input_type: "text",
      });
      // Navigate to Q&A flow with intel ID
      router.push(`/capture/qa?id=${intel.id}`);
    } catch (err) {
      console.error("Failed to create intel:", err);
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <TopBar title="新增情報" />
      <div className="flex-1 px-4 py-6 flex flex-col gap-6 max-w-2xl mx-auto w-full">
        {/* Input method tabs */}
        <div className="flex gap-2">
          <button className="flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-400 dark:text-slate-500 cursor-not-allowed min-h-[44px]">
            <Camera size={20} strokeWidth={1.5} />
            <span className="text-sm font-medium">拍照</span>
          </button>
          <button className="flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg bg-blue-500/10 border border-blue-500 text-blue-500 dark:text-blue-400 min-h-[44px] cursor-pointer">
            <Type size={20} strokeWidth={1.5} />
            <span className="text-sm font-medium">文字輸入</span>
          </button>
        </div>

        {/* Text input area */}
        <div className="flex-1 flex flex-col gap-3">
          <label className="text-xs font-medium text-slate-500 dark:text-slate-400">
            會議記錄 / 名片資訊 / 任何情報
          </label>
          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="貼上會議記錄、語音轉文字、名片資訊...&#10;&#10;例如：「今天去 A 食品拜訪陳副廠長，他提到今年重點是產線自動化，預算約 300K，希望先做 AOI。NDA 已簽。」"
            className="flex-1 min-h-[200px] w-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-4 py-3 text-base text-slate-900 dark:text-slate-50 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none transition-colors duration-200 resize-none"
          />
          <p className="text-[11px] text-slate-400 dark:text-slate-500">
            AI 會自動解析人物、組織、痛點、時程等資訊
          </p>
        </div>

        {/* Submit button */}
        <button
          onClick={handleSubmit}
          disabled={!inputText.trim() || loading}
          className="w-full flex items-center justify-center gap-2 bg-blue-500 hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold px-6 py-3 rounded-lg min-h-[44px] active:scale-[0.98] transition-all duration-200 cursor-pointer"
        >
          {loading ? (
            <Loader2 size={20} className="animate-spin" />
          ) : (
            <>
              <span>送出情報</span>
              <ArrowRight size={20} strokeWidth={1.5} />
            </>
          )}
        </button>
      </div>
    </div>
  );
}
