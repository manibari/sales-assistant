"use client";

import { useState, useEffect } from "react";
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
  Briefcase,
  ChevronDown,
  ChevronRight,
  Home,
  Users,
  LogOut,
  PanelLeftClose,
  PanelLeftOpen,
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
        roles: ["admin", "manager"],
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
        roles: ["admin", "manager"],
      },
      { label: "關係網", href: "/contacts", icon: BookUser },
      {
        label: "陌開工作台",
        href: "/outreach",
        icon: Target,
        roles: ["admin", "manager"],
      },
    ],
  },
  // 情報與研究 — admin/sales only
  {
    title: "情報與研究",
    collapsible: true,
    roles: ["admin", "manager"],
    items: [
      { label: "新增情報", href: "/capture", icon: Plus },
      { label: "情報紀錄", href: "/intel", icon: Zap },
      { label: "知識庫", href: "/knowledge", icon: Brain },
      { label: "補助案", href: "/subsidies", icon: Landmark },
      { label: "政府標案", href: "/tenders", icon: Gavel },
    ],
  },
  // 交付與專案 — admin/sales/finance（成案後的執行階段）
  {
    title: "交付與專案",
    collapsible: true,
    roles: ["admin", "manager", "user"],
    items: [
      { label: "專案管理", href: "/projects", icon: Briefcase },
    ],
  },
  // 法務與行政 — admin/sales/finance
  {
    title: "法務與行政",
    collapsible: true,
    roles: ["admin", "manager", "user"],
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

const SIDEBAR_STORAGE_KEY = "nexus_sidebar_collapsed";

export function DesktopSidebar() {
  const pathname = usePathname();
  const [sectionCollapsed, setSectionCollapsed] = useState<Record<string, boolean>>({});
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const { user, logout } = useAuth();
  const role = (user?.role ?? "manager") as UserRole;

  // Restore sidebar collapsed state from localStorage
  useEffect(() => {
    const stored = localStorage.getItem(SIDEBAR_STORAGE_KEY);
    if (stored === "true") setSidebarCollapsed(true);
  }, []);

  const toggleSidebar = () => {
    setSidebarCollapsed((prev) => {
      const next = !prev;
      localStorage.setItem(SIDEBAR_STORAGE_KEY, String(next));
      return next;
    });
  };

  const toggleSection = (key: string) => {
    setSectionCollapsed((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const isActiveInSection = (items: NavItem[]) =>
    items.some((item) => pathname === item.href || (item.href !== "/home" && pathname.startsWith(item.href)));

  return (
    <aside
      className={`hidden md:flex flex-col bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-700 transition-all duration-200 ${
        sidebarCollapsed ? "w-[60px]" : "w-64"
      }`}
    >
      {/* Header */}
      <div className={`border-b border-slate-200 dark:border-slate-700 flex items-center ${sidebarCollapsed ? "p-3 justify-center" : "p-4 justify-between"}`}>
        {!sidebarCollapsed && (
          <div className="overflow-hidden">
            <h1 className="text-lg font-bold text-slate-900 dark:text-slate-50 tracking-tight truncate">
              Project Nexus
            </h1>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Strategic Console
            </p>
          </div>
        )}
        <button
          onClick={toggleSidebar}
          aria-label={sidebarCollapsed ? "展開側邊欄" : "收起側邊欄"}
          title={sidebarCollapsed ? "展開側邊欄" : "收起側邊欄"}
          className="p-1.5 rounded-lg text-slate-400 dark:text-slate-500 hover:text-slate-600 dark:hover:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer shrink-0"
        >
          {sidebarCollapsed ? (
            <PanelLeftOpen size={18} strokeWidth={1.5} />
          ) : (
            <PanelLeftClose size={18} strokeWidth={1.5} />
          )}
        </button>
      </div>

      {/* Nav */}
      <nav className="flex-1 p-2 overflow-auto overflow-x-hidden">
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
          const isSectionCollapsed = section.collapsible && sectionCollapsed[key] && !sectionActive;

          return (
            <div key={key} className={si > 0 ? "mt-2" : ""}>
              {/* Section title — hidden when sidebar is collapsed */}
              {section.title && !sidebarCollapsed && (
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
                      {isSectionCollapsed ? (
                        <ChevronRight size={14} />
                      ) : (
                        <ChevronDown size={14} />
                      )}
                    </span>
                  )}
                  <span>{section.title}</span>
                </button>
              )}

              {/* Items */}
              {(!isSectionCollapsed || sidebarCollapsed) && (
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
                        title={sidebarCollapsed ? item.label : undefined}
                        className={`flex items-center rounded-lg text-sm transition-colors duration-200 cursor-pointer ${
                          sidebarCollapsed
                            ? "justify-center p-2.5"
                            : "gap-3 px-3 py-2"
                        } ${
                          active
                            ? "bg-blue-500/10 text-blue-500 dark:text-blue-400 font-medium"
                            : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800"
                        }`}
                      >
                        <Icon size={18} strokeWidth={1.5} />
                        {!sidebarCollapsed && item.label}
                      </Link>
                    );
                  })}
                </div>
              )}

              {/* Divider between sections in collapsed mode */}
              {sidebarCollapsed && si < NAV_SECTIONS.length - 1 && (
                <div className="my-1 border-b border-slate-100 dark:border-slate-800" />
              )}
            </div>
          );
        })}
      </nav>

      {/* User footer */}
      {user && (
        <div className={`border-t border-slate-200 dark:border-slate-700 flex items-center ${sidebarCollapsed ? "p-2 justify-center" : "p-3 justify-between"}`}>
          {!sidebarCollapsed && (
            <div className="overflow-hidden">
              <p className="text-xs text-slate-500 dark:text-slate-400 truncate">
                {user.name}
              </p>
              <p className="text-[11px] text-slate-400 dark:text-slate-600 capitalize">
                {user.role === "admin" ? "管理員" : user.role === "manager" ? "管理者" : "使用者"}
              </p>
            </div>
          )}
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
