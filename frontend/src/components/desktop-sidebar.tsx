"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  TrendingUp,
  Calendar,
  Plus,
  Zap,
  BookUser,
  FileCheck,
  Search,
  Landmark,
  Brain,
  Target,
  Settings,
  Gavel,
  ChevronDown,
  ChevronRight,
  Home,
  Users,
  LogOut,
  type LucideIcon,
} from "lucide-react";
import { useAuth, type UserRole } from "@/lib/auth-context";

interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
  roles?: UserRole[]; // if set, overrides section-level roles for this item
}

interface NavSection {
  title?: string;
  collapsible?: boolean;
  roles?: UserRole[]; // if set, entire section hidden for roles not listed
  items: NavItem[];
}

const NAV_SECTIONS: NavSection[] = [
  // Top — always visible, items filtered individually
  {
    items: [
      { label: "主畫面", href: "/home", icon: Home },
      {
        label: "控制台",
        href: "/dashboard",
        icon: LayoutDashboard,
        roles: ["admin", "sales"],
      },
    ],
  },
  // 業務與銷售 — finance sees 商機+關係網 only
  {
    title: "業務與銷售",
    collapsible: true,
    items: [
      { label: "商機 Pipeline", href: "/deals", icon: TrendingUp },
      {
        label: "行事曆",
        href: "/calendar",
        icon: Calendar,
        roles: ["admin", "sales"],
      },
      { label: "關係網", href: "/contacts", icon: BookUser },
      {
        label: "陌開工作台",
        href: "/outreach",
        icon: Target,
        roles: ["admin", "sales"],
      },
    ],
  },
  // 情報與研究 — admin/sales only
  {
    title: "情報與研究",
    collapsible: true,
    roles: ["admin", "sales"],
    items: [
      { label: "新增情報", href: "/capture", icon: Plus },
      { label: "情報紀錄", href: "/intel", icon: Zap },
      { label: "知識庫", href: "/knowledge", icon: Brain },
      { label: "補助案", href: "/subsidies", icon: Landmark },
      { label: "政府標案", href: "/tenders", icon: Gavel },
    ],
  },
  // 法務與行政 — admin/sales/finance
  {
    title: "法務與行政",
    collapsible: true,
    roles: ["admin", "sales", "finance"],
    items: [
      { label: "文件追蹤", href: "/documents", icon: FileCheck },
    ],
  },
  // 系統管理 — admin only
  {
    title: "系統管理",
    collapsible: true,
    roles: ["admin"],
    items: [
      { label: "使用者管理", href: "/admin/users", icon: Users },
      { label: "搜尋", href: "/search", icon: Search },
      { label: "設定", href: "/settings", icon: Settings },
    ],
  },
];

export function DesktopSidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState<Record<string, boolean>>({});
  const { user, logout } = useAuth();
  const role = (user?.role ?? "sales") as UserRole;

  const toggleSection = (key: string) => {
    setCollapsed((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const isActiveInSection = (items: NavItem[]) =>
    items.some((item) => pathname === item.href || (item.href !== "/home" && pathname.startsWith(item.href)));

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

      <nav className="flex-1 p-3 overflow-auto">
        {NAV_SECTIONS.map((section, si) => {
          // Section-level role check
          if (section.roles && !section.roles.includes(role)) return null;

          // Item-level role filter
          const visibleItems = section.items.filter(
            (item) => !item.roles || item.roles.includes(role)
          );
          if (visibleItems.length === 0) return null;

          const key = section.title ? `${section.title}-${si}` : `section-${si}`;
          const sectionActive = isActiveInSection(visibleItems);
          const isCollapsed = section.collapsible && collapsed[key] && !sectionActive;

          return (
            <div key={key} className={si > 0 ? "mt-3" : ""}>
              {section.title && (
                <button
                  onClick={() => section.collapsible && toggleSection(key)}
                  className={`flex items-center gap-1 w-full px-3 mb-1 py-1 rounded-md text-xs font-medium transition-colors ${
                    section.collapsible
                      ? "cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800/50"
                      : ""
                  } ${
                    sectionActive
                      ? "text-slate-900 dark:text-slate-100"
                      : "text-slate-400 dark:text-slate-500"
                  }`}
                >
                  {section.collapsible && (
                    <span className="text-slate-300 dark:text-slate-600">
                      {isCollapsed ? (
                        <ChevronRight size={14} />
                      ) : (
                        <ChevronDown size={14} />
                      )}
                    </span>
                  )}
                  <span>{section.title}</span>
                </button>
              )}
              {!isCollapsed && (
                <div className="space-y-0.5">
                  {visibleItems.map((item) => {
                    const active =
                      pathname === item.href ||
                      (item.href !== "/home" && pathname.startsWith(item.href));
                    const Icon = item.icon;
                    return (
                      <Link
                        key={item.href}
                        href={item.href}
                        className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors duration-200 cursor-pointer ${
                          active
                            ? "bg-blue-500/10 text-blue-500 dark:text-blue-400 font-medium"
                            : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800"
                        }`}
                      >
                        <Icon size={18} strokeWidth={1.5} />
                        {item.label}
                      </Link>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </nav>

      {user && (
        <div className="p-3 border-t border-slate-200 dark:border-slate-700 flex items-center justify-between">
          <div>
            <p className="text-xs text-slate-500 dark:text-slate-400 truncate">
              {user.name}
            </p>
            <p className="text-[11px] text-slate-400 dark:text-slate-600 capitalize">
              {user.role === "admin" ? "管理員" : user.role === "sales" ? "業務" : "財務"}
            </p>
          </div>
          <button
            onClick={logout}
            aria-label="登出"
            title="登出"
            className="p-1.5 rounded-lg text-slate-400 dark:text-slate-600 hover:text-slate-600 dark:hover:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
          >
            <LogOut size={15} strokeWidth={1.5} />
          </button>
        </div>
      )}
    </aside>
  );
}
