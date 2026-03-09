"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  TrendingUp,
  Calendar,
  Plus,
  Zap,
  BookUser,
  Search,
  type LucideIcon,
} from "lucide-react";

interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
}

const NAV_ITEMS: NavItem[] = [
  { label: "控制台", href: "/dashboard", icon: LayoutDashboard },
  { label: "商機 Pipeline", href: "/deals", icon: TrendingUp },
  { label: "行事曆", href: "/calendar", icon: Calendar },
  { label: "新增情報", href: "/capture", icon: Plus },
  { label: "情報 Feed", href: "/intel", icon: Zap },
  { label: "通訊錄", href: "/contacts", icon: BookUser },
  { label: "搜尋", href: "/search", icon: Search },
];

export function DesktopSidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden md:flex w-64 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-700 flex-col">
      <div className="p-4 border-b border-slate-200 dark:border-slate-700">
        <h1 className="text-lg font-bold text-slate-900 dark:text-slate-50 tracking-tight">
          Project Nexus
        </h1>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
          Strategic Console
        </p>
      </div>
      <nav className="flex-1 p-3 space-y-1 overflow-auto">
        {NAV_ITEMS.map((item) => {
          const active = pathname.startsWith(item.href);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors duration-200 cursor-pointer ${
                active
                  ? "bg-blue-500/10 text-blue-500 dark:text-blue-400 font-medium"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800"
              }`}
            >
              <Icon size={20} strokeWidth={1.5} />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
