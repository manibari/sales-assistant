"use client";

import { HardDrive } from "lucide-react";

export function SettingsTabGDrive() {
  return (
    <div className="space-y-6">
      <div className="border border-slate-200 dark:border-slate-700 rounded-xl p-5 opacity-60">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 bg-yellow-500/10 rounded-lg flex items-center justify-center">
            <HardDrive size={20} className="text-yellow-500" />
          </div>
          <div>
            <h3 className="font-medium text-slate-900 dark:text-slate-100">Google Drive</h3>
            <p className="text-xs text-slate-500">文件同步與協作</p>
          </div>
        </div>
        <div className="bg-slate-50 dark:bg-slate-800 rounded-lg px-4 py-8 text-center">
          <p className="text-sm text-slate-500 dark:text-slate-400">
            即將推出
          </p>
          <p className="text-xs text-slate-400 mt-1">
            Google Drive 整合正在規劃中，敬請期待。
          </p>
        </div>
      </div>
    </div>
  );
}
