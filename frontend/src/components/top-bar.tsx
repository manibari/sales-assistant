"use client";

import { Sun, Moon, LogOut, Home } from "lucide-react";
import Link from "next/link";
import { useTheme } from "./theme-provider";
import { useAuth } from "@/lib/auth-context";

interface TopBarProps {
  title: string;
  children?: React.ReactNode;
}

export function TopBar({ title, children }: TopBarProps) {
  const { theme, toggle } = useTheme();
  const { user, logout } = useAuth();

  return (
    <header className="h-14 px-4 flex items-center justify-between border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shrink-0">
      <h1 className="text-xl font-bold text-slate-900 dark:text-slate-50 truncate">
        {title}
      </h1>
      <div className="flex items-center gap-1">
        {children}
        <Link
          href="/home"
          className="p-2 rounded-lg text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors duration-200"
          aria-label="主畫面"
        >
          <Home size={18} strokeWidth={1.5} />
        </Link>
        <button
          onClick={toggle}
          className="p-2 rounded-lg text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors duration-200 cursor-pointer"
          aria-label="Toggle theme"
        >
          {theme === "dark" ? <Sun size={18} strokeWidth={1.5} /> : <Moon size={18} strokeWidth={1.5} />}
        </button>
        {user && (
          <div className="flex items-center gap-2 ml-1 pl-2 border-l border-slate-200 dark:border-slate-700">
            <span className="text-xs text-slate-500 dark:text-slate-400 hidden sm:block">
              {user.name}
            </span>
            <button
              onClick={logout}
              className="p-2 rounded-lg text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors duration-200 cursor-pointer"
              aria-label="登出"
              title="登出"
            >
              <LogOut size={18} strokeWidth={1.5} />
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
