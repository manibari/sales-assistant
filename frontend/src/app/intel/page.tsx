"use client";

import { useState, useEffect } from "react";
import { TopBar } from "@/components/top-bar";
import { nxApi, type NxIntel } from "@/lib/nexus-api";
import { FileText, Camera, Mic } from "lucide-react";

const INPUT_ICONS: Record<string, typeof FileText> = {
  text: FileText,
  photo: Camera,
  voice: Mic,
};

export default function IntelPage() {
  const [intels, setIntels] = useState<NxIntel[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    nxApi.intel
      .list()
      .then(setIntels)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="flex flex-col h-full">
      <TopBar title="情報 Feed" />
      <div className="flex-1 px-4 py-4 overflow-auto">
        {loading ? (
          <div className="flex items-center justify-center py-20 text-slate-400">
            載入中...
          </div>
        ) : intels.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-slate-400 dark:text-slate-500">
            <p className="text-sm">尚無情報</p>
            <p className="text-xs mt-1">點擊 ＋ 新增第一筆情報</p>
          </div>
        ) : (
          <div className="space-y-3 max-w-2xl lg:max-w-4xl mx-auto">
            {intels.map((intel) => {
              const Icon = INPUT_ICONS[intel.input_type] || FileText;
              const isConfirmed = intel.status === "confirmed";
              return (
                <div
                  key={intel.id}
                  className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4 transition-colors duration-200 cursor-pointer hover:border-slate-300 dark:hover:border-slate-600"
                >
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 rounded-lg bg-cyan-500/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                      <Icon size={16} className="text-cyan-500" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-slate-900 dark:text-slate-50 line-clamp-2">
                        {intel.raw_input}
                      </p>
                      <div className="flex items-center gap-2 mt-2">
                        <span
                          className={`text-[11px] px-2 py-0.5 rounded-full font-medium ${
                            isConfirmed
                              ? "bg-green-500/10 text-green-400"
                              : "bg-amber-500/10 text-amber-400"
                          }`}
                        >
                          {isConfirmed ? "已確認" : "草稿"}
                        </span>
                        <span className="text-[11px] text-slate-400 dark:text-slate-500">
                          {new Date(intel.created_at).toLocaleDateString("zh-TW")}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
