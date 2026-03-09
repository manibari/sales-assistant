"use client";

import { TopBar } from "@/components/top-bar";
import { Calendar as CalendarIcon } from "lucide-react";

export default function CalendarPage() {
  return (
    <div className="flex flex-col h-full">
      <TopBar title="行事曆" />
      <div className="flex-1 flex flex-col items-center justify-center px-4 text-slate-400 dark:text-slate-500">
        <CalendarIcon size={48} strokeWidth={1} className="mb-4 opacity-50" />
        <p className="text-sm">行事曆功能開發中</p>
        <p className="text-xs mt-1">S37 Sprint</p>
      </div>
    </div>
  );
}
