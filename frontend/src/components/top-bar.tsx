"use client";

import { Sun, Moon } from "lucide-react";
import { useTheme } from "./theme-provider";

interface TopBarProps {
  title: string;
  children?: React.ReactNode;
}

export function TopBar({ title, children }: TopBarProps) {
  const { theme, toggle } = useTheme();

  return (
    <header className="h-14 px-4 flex items-center justify-between border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
      <h1 className="text-xl font-bold text-slate-900 dark:text-slate-50 truncate">
        {title}
      </h1>
      <div className="flex items-center gap-2">
        {children}
        <button
          onClick={toggle}
          className="p-2 rounded-lg text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors duration-200 cursor-pointer"
          aria-label="Toggle theme"
        >
          {theme === "dark" ? <Sun size={20} strokeWidth={1.5} /> : <Moon size={20} strokeWidth={1.5} />}
        </button>
      </div>
    </header>
  );
}
