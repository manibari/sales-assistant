"use client";

import { useEffect, useState } from "react";
import { api, Client } from "@/lib/api";

export default function ClientsPage() {
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.crm
      .list()
      .then(setClients)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-gray-500">Loading...</p>;
  if (error) return <p className="text-red-400">Error: {error}</p>;

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">客戶列表</h2>
      <div className="bg-gray-900 rounded-lg border border-gray-800 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-800 text-gray-400">
              <th className="text-left p-3">ID</th>
              <th className="text-left p-3">公司名稱</th>
              <th className="text-left p-3">產業</th>
              <th className="text-right p-3">健康分數</th>
            </tr>
          </thead>
          <tbody>
            {clients.map((c) => (
              <tr
                key={c.client_id}
                className="border-b border-gray-800/50 hover:bg-gray-800/30 transition-colors"
              >
                <td className="p-3 font-mono text-xs text-gray-500">
                  {c.client_id}
                </td>
                <td className="p-3">{c.company_name}</td>
                <td className="p-3 text-gray-400">{c.industry ?? "—"}</td>
                <td className="p-3 text-right">
                  <HealthBadge score={c.client_health_score} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-gray-600 mt-2">{clients.length} clients</p>
    </div>
  );
}

function HealthBadge({ score }: { score: number | null }) {
  if (score === null) return <span className="text-gray-600">—</span>;
  const color =
    score >= 70 ? "text-green-400" : score >= 40 ? "text-yellow-400" : "text-red-400";
  return <span className={`font-mono ${color}`}>{score}</span>;
}
