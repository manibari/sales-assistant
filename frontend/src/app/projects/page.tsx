"use client";

import { useEffect, useState } from "react";
import { api, Project } from "@/lib/api";

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.projects
      .list()
      .then(setProjects)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-gray-500">Loading...</p>;
  if (error) return <p className="text-red-400">Error: {error}</p>;

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">案件列表</h2>
      <div className="bg-gray-900 rounded-lg border border-gray-800 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-800 text-gray-400">
              <th className="text-left p-3">#</th>
              <th className="text-left p-3">案件名稱</th>
              <th className="text-left p-3">階段</th>
              <th className="text-left p-3">業務</th>
              <th className="text-left p-3">Presale</th>
            </tr>
          </thead>
          <tbody>
            {projects.map((p) => (
              <tr
                key={p.project_id}
                className="border-b border-gray-800/50 hover:bg-gray-800/30 transition-colors"
              >
                <td className="p-3 font-mono text-xs text-gray-500">
                  {p.project_id}
                </td>
                <td className="p-3">{p.project_name}</td>
                <td className="p-3">
                  <StatusBadge code={p.status_code} />
                </td>
                <td className="p-3 text-gray-400">{p.sales_owner ?? "—"}</td>
                <td className="p-3 text-gray-400">{p.presale_owner ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-gray-600 mt-2">{projects.length} projects</p>
    </div>
  );
}

function StatusBadge({ code }: { code: string }) {
  const colors: Record<string, string> = {
    L0: "bg-gray-700",
    L1: "bg-blue-900 text-blue-300",
    L2: "bg-indigo-900 text-indigo-300",
    L3: "bg-violet-900 text-violet-300",
    L4: "bg-purple-900 text-purple-300",
    L5: "bg-fuchsia-900 text-fuchsia-300",
    L6: "bg-pink-900 text-pink-300",
    L7: "bg-green-900 text-green-300",
    P0: "bg-teal-900 text-teal-300",
    P1: "bg-cyan-900 text-cyan-300",
    P2: "bg-emerald-900 text-emerald-300",
    LOST: "bg-red-900 text-red-300",
    HOLD: "bg-yellow-900 text-yellow-300",
  };
  return (
    <span
      className={`px-2 py-0.5 rounded text-xs font-mono ${colors[code] ?? "bg-gray-700"}`}
    >
      {code}
    </span>
  );
}
