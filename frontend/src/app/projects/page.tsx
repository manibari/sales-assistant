"use client";

import { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import { TopBar } from "@/components/top-bar";
import {
  Briefcase,
  Loader2,
  Search,
  Users,
  Calendar,
  ChevronRight,
  Building2,
} from "lucide-react";
import { nxApi, type NxProject } from "@/lib/nexus-api";

const STATUS_LABELS: Record<string, string> = {
  planning: "規劃中",
  active: "進行中",
  completed: "已完成",
  paused: "暫停",
};

const STATUS_COLORS: Record<string, string> = {
  planning: "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400",
  active: "bg-green-500/10 text-green-600 dark:text-green-400",
  completed: "bg-blue-500/10 text-blue-600 dark:text-blue-400",
  paused: "bg-amber-500/10 text-amber-600 dark:text-amber-400",
};

const STATUS_FILTERS = ["all", "active", "planning", "completed", "paused"];

function formatDate(d: string | null) {
  if (!d) return "—";
  return new Date(d).toLocaleDateString("zh-TW");
}

export default function ProjectsPage() {
  const [projects, setProjects] = useState<NxProject[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  useEffect(() => {
    nxApi.projects
      .list()
      .then(setProjects)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(() => {
    return projects.filter((p) => {
      if (statusFilter !== "all" && p.status !== statusFilter) return false;
      if (search.trim()) {
        const q = search.toLowerCase();
        if (
          !p.name.toLowerCase().includes(q) &&
          !(p.client_name || "").toLowerCase().includes(q) &&
          !(p.deal_name || "").toLowerCase().includes(q)
        )
          return false;
      }
      return true;
    });
  }, [projects, search, statusFilter]);

  const counts = useMemo(() => {
    const c: Record<string, number> = { all: projects.length };
    for (const p of projects) c[p.status] = (c[p.status] || 0) + 1;
    return c;
  }, [projects]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 size={24} className="animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <TopBar title="專案管理" />

      <div className="flex-1 px-4 py-4 overflow-auto max-w-2xl lg:max-w-4xl mx-auto w-full space-y-4">
        {/* Status filters */}
        <div className="flex gap-2 flex-wrap">
          {STATUS_FILTERS.map((s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`text-xs px-3 py-1.5 rounded-full font-medium border cursor-pointer transition-colors ${
                statusFilter === s
                  ? "border-blue-500 bg-blue-500/10 text-blue-500"
                  : "border-slate-200 dark:border-slate-700 text-slate-500 hover:border-slate-400"
              }`}
            >
              {s === "all" ? "全部" : STATUS_LABELS[s]}{" "}
              <span className="text-slate-400">({counts[s] || 0})</span>
            </button>
          ))}
        </div>

        {/* Search */}
        <div className="relative">
          <Search
            size={16}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
          />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="搜尋專案名稱、客戶、商機..."
            className="w-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl pl-10 pr-4 py-2.5 text-sm text-slate-900 dark:text-slate-50 placeholder:text-slate-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none"
          />
        </div>

        {/* List */}
        {filtered.length === 0 ? (
          <div className="text-center py-12 text-slate-400 text-sm">
            {search || statusFilter !== "all"
              ? "沒有符合條件的專案"
              : "尚無專案 · 從成交的商機詳頁建立"}
          </div>
        ) : (
          <div className="space-y-2">
            {filtered.map((p) => (
              <ProjectRow key={p.id} project={p} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function ProjectRow({ project }: { project: NxProject }) {
  return (
    <Link
      href={`/projects/${project.id}`}
      className="block bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-4 hover:border-blue-500/50 transition-colors"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-2 min-w-0 flex-1">
          <Briefcase size={16} className="text-indigo-500 mt-0.5 flex-shrink-0" />
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2 flex-wrap">
              <p className="text-sm font-semibold text-slate-900 dark:text-slate-50 truncate">
                {project.name}
              </p>
              <span
                className={`text-[11px] px-2 py-0.5 rounded-full font-medium ${
                  STATUS_COLORS[project.status] || STATUS_COLORS.planning
                }`}
              >
                {STATUS_LABELS[project.status] || project.status}
              </span>
            </div>
            <div className="flex items-center gap-3 mt-1.5 text-xs text-slate-500 flex-wrap">
              {project.client_name && (
                <span className="flex items-center gap-1">
                  <Building2 size={11} />
                  {project.client_name}
                </span>
              )}
              {project.pm_name && (
                <span className="flex items-center gap-1">
                  <Users size={11} />
                  PM：{project.pm_name}
                </span>
              )}
              {project.csm_name && (
                <span className="flex items-center gap-1 text-slate-400">
                  CSM：{project.csm_name}
                </span>
              )}
              {(project.start_date || project.end_date) && (
                <span className="flex items-center gap-1 text-slate-400">
                  <Calendar size={11} />
                  {formatDate(project.start_date)} → {formatDate(project.end_date)}
                </span>
              )}
            </div>
          </div>
        </div>
        <ChevronRight size={16} className="text-slate-300 flex-shrink-0 mt-1" />
      </div>
    </Link>
  );
}
