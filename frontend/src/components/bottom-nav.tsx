"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  TrendingUp,
  Calendar,
  Plus,
  Zap,
  BookUser,
} from "lucide-react";

const NAV_ITEMS = [
  { label: "商機", href: "/deals", icon: TrendingUp },
  { label: "行事曆", href: "/calendar", icon: Calendar },
  { label: "", href: "/capture", icon: Plus, isFab: true },
  { label: "情報", href: "/intel", icon: Zap },
  { label: "通訊錄", href: "/contacts", icon: BookUser },
];

export function BottomNav() {
  const pathname = usePathname();

  return (
    <nav className="fixed bottom-0 inset-x-0 h-16 bg-white/95 dark:bg-slate-900/95 backdrop-blur-sm border-t border-slate-200 dark:border-slate-800 grid grid-cols-5 z-50 md:hidden">
      {NAV_ITEMS.map((item) => {
        const active = pathname.startsWith(item.href);
        const Icon = item.icon;

        if (item.isFab) {
          return (
            <Link
              key={item.href}
              href={item.href}
              className="flex items-center justify-center"
            >
              <div className="w-12 h-12 rounded-full bg-blue-500 flex items-center justify-center shadow-lg shadow-blue-500/25 active:scale-95 transition-transform duration-150 cursor-pointer -mt-4">
                <Icon size={24} className="text-white" strokeWidth={2} />
              </div>
            </Link>
          );
        }

        return (
          <Link
            key={item.href}
            href={item.href}
            className={`flex flex-col items-center justify-center gap-1 cursor-pointer transition-colors duration-200 ${
              active
                ? "text-blue-500 dark:text-blue-400"
                : "text-slate-400 dark:text-slate-500"
            }`}
          >
            <Icon size={20} strokeWidth={1.5} />
            <span className="text-[11px]">{item.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}
