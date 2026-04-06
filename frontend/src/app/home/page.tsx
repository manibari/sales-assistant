"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  TrendingUp,
  Calendar,
  BookUser,
  Zap,
  Brain,
  Landmark,
  Gavel,
  Target,
  FileCheck,
  LayoutDashboard,
  Receipt,
  FileText,
  Users,
  Settings,
  Scale,
  type LucideIcon,
} from "lucide-react";
import { useAuth, type UserRole } from "@/lib/auth-context";

interface Module {
  label: string;
  description: string;
  href: string;
  icon: LucideIcon;
  color: string;
  roles: UserRole[];
  comingSoon?: boolean;
}

interface Section {
  id: string;
  label: string;
  emoji: string;
  modules: Module[];
}

const SECTIONS: Section[] = [
  {
    id: "sales",
    label: "業務與銷售",
    emoji: "📈",
    modules: [
      {
        label: "控制台",
        description: "Pipeline 總覽、行動提醒、今日會議",
        href: "/dashboard",
        icon: LayoutDashboard,
        color: "bg-blue-500",
        roles: ["admin", "sales"],
      },
      {
        label: "商機管理",
        description: "Deal Pipeline、MEDDIC 評估、階段推進",
        href: "/deals",
        icon: TrendingUp,
        color: "bg-indigo-500",
        roles: ["admin", "sales", "finance"],
      },
      {
        label: "行事曆",
        description: "會議管理、行程安排",
        href: "/calendar",
        icon: Calendar,
        color: "bg-violet-500",
        roles: ["admin", "sales"],
      },
      {
        label: "關係網",
        description: "客戶、合作夥伴、聯絡人",
        href: "/contacts",
        icon: BookUser,
        color: "bg-cyan-500",
        roles: ["admin", "sales", "finance"],
      },
      {
        label: "陌開工作台",
        description: "冷開發工作流程",
        href: "/outreach",
        icon: Target,
        color: "bg-pink-500",
        roles: ["admin", "sales"],
      },
    ],
  },
  {
    id: "intel",
    label: "情報與研究",
    emoji: "⚡",
    modules: [
      {
        label: "情報系統",
        description: "情資紀錄、AI 分析、知識庫",
        href: "/intel",
        icon: Zap,
        color: "bg-amber-500",
        roles: ["admin", "sales"],
      },
      {
        label: "知識庫",
        description: "文件解析、知識檢索",
        href: "/knowledge",
        icon: Brain,
        color: "bg-emerald-500",
        roles: ["admin", "sales"],
      },
      {
        label: "補助案",
        description: "政府補助追蹤、截止日管理",
        href: "/subsidies",
        icon: Landmark,
        color: "bg-teal-500",
        roles: ["admin", "sales"],
      },
      {
        label: "政府標案",
        description: "標案搜尋、投標追蹤",
        href: "/tenders",
        icon: Gavel,
        color: "bg-orange-500",
        roles: ["admin", "sales"],
      },
    ],
  },
  {
    id: "legal",
    label: "法務與行政",
    emoji: "⚖️",
    modules: [
      {
        label: "文件追蹤",
        description: "NDA、MOU、合約文件管理",
        href: "/documents",
        icon: FileCheck,
        color: "bg-slate-500",
        roles: ["admin", "sales", "finance"],
      },
      {
        label: "報價單",
        description: "建立與管理報價文件",
        href: "/quotes",
        icon: Receipt,
        color: "bg-lime-600",
        roles: ["admin", "sales"],
        comingSoon: true,
      },
      {
        label: "合約管理",
        description: "合約建立、簽署追蹤",
        href: "/contracts",
        icon: Scale,
        color: "bg-rose-500",
        roles: ["admin", "finance"],
        comingSoon: true,
      },
    ],
  },
  {
    id: "finance",
    label: "財務管理",
    emoji: "💰",
    modules: [
      {
        label: "發票管理",
        description: "開立發票、付款追蹤",
        href: "/invoices",
        icon: Receipt,
        color: "bg-red-500",
        roles: ["admin", "finance"],
        comingSoon: true,
      },
      {
        label: "帳款管理",
        description: "應收帳款、請款追蹤",
        href: "/billing",
        icon: FileText,
        color: "bg-orange-600",
        roles: ["admin", "finance"],
        comingSoon: true,
      },
    ],
  },
  {
    id: "system",
    label: "系統管理",
    emoji: "⚙️",
    modules: [
      {
        label: "使用者管理",
        description: "新增帳號、設定角色權限",
        href: "/admin/users",
        icon: Users,
        color: "bg-slate-700",
        roles: ["admin"],
      },
      {
        label: "系統設定",
        description: "整合設定、AI 引擎、通知",
        href: "/settings",
        icon: Settings,
        color: "bg-slate-600",
        roles: ["admin"],
      },
    ],
  },
];

function ModuleCard({ mod }: { mod: Module }) {
  const Icon = mod.icon;
  const card = (
    <div
      className={`relative bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-2xl p-5 flex flex-col gap-3 shadow-sm transition-all duration-200 min-h-[120px] ${
        mod.comingSoon
          ? "opacity-60 cursor-default"
          : "hover:shadow-md hover:-translate-y-0.5 cursor-pointer"
      }`}
    >
      <div className={`w-10 h-10 rounded-xl ${mod.color} flex items-center justify-center`}>
        <Icon size={20} className="text-white" strokeWidth={1.5} />
      </div>
      <div>
        <p className="text-sm font-semibold text-slate-900 dark:text-slate-50">
          {mod.label}
        </p>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5 leading-relaxed">
          {mod.description}
        </p>
      </div>
      {mod.comingSoon && (
        <span className="absolute top-3 right-3 text-[10px] font-medium bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 px-2 py-0.5 rounded-full">
          即將開放
        </span>
      )}
    </div>
  );

  if (mod.comingSoon) {
    return <div>{card}</div>;
  }
  return <Link href={mod.href}>{card}</Link>;
}

export default function HomePage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.push("/login");
    }
  }, [user, loading, router]);

  if (loading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const roleLabel: Record<string, string> = {
    admin: "系統管理員",
    sales: "業務",
    finance: "財務",
  };

  const visibleSections = SECTIONS
    .map((section) => ({
      ...section,
      modules: section.modules.filter((m) => m.roles.includes(user.role as UserRole)),
    }))
    .filter((section) => section.modules.length > 0);

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 p-6 md:p-10">
      <div className="max-w-5xl mx-auto space-y-10">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-50">
            歡迎回來，{user.name}
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            {roleLabel[user.role] ?? user.role} · Project Nexus
          </p>
        </div>

        {visibleSections.map((section) => (
          <div key={section.id}>
            <div className="flex items-center gap-2 mb-4">
              <span className="text-lg" aria-hidden="true">{section.emoji}</span>
              <h2 className="text-sm font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                {section.label}
              </h2>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
              {section.modules.map((mod) => (
                <ModuleCard key={mod.href} mod={mod} />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
