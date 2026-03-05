"use client";

import { useEffect, useState } from "react";
import { api, GraphData } from "@/lib/api";

export default function NetworkPage() {
  const [graph, setGraph] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.network
      .graph()
      .then(setGraph)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-gray-500">Loading graph data...</p>;
  if (error) return <p className="text-red-400">Error: {error}</p>;
  if (!graph) return null;

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">關係網絡</h2>
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-gray-900 rounded-lg border border-gray-800 p-4">
          <p className="text-3xl font-bold">{graph.nodes.length}</p>
          <p className="text-sm text-gray-500">節點</p>
        </div>
        <div className="bg-gray-900 rounded-lg border border-gray-800 p-4">
          <p className="text-3xl font-bold">{graph.edges.length}</p>
          <p className="text-sm text-gray-500">連結</p>
        </div>
      </div>

      <div className="bg-gray-900 rounded-lg border border-gray-800 p-6 min-h-[400px] flex items-center justify-center">
        <p className="text-gray-500">
          D3.js / react-force-graph 互動式網絡圖將在 S34 實作
        </p>
      </div>

      <div className="mt-6 grid grid-cols-2 gap-4">
        <div>
          <h3 className="text-sm font-semibold text-gray-400 mb-2">
            節點統計
          </h3>
          <NodeStats nodes={graph.nodes} />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-gray-400 mb-2">
            連結統計
          </h3>
          <EdgeStats edges={graph.edges} />
        </div>
      </div>
    </div>
  );
}

function NodeStats({ nodes }: { nodes: GraphData["nodes"] }) {
  const counts = nodes.reduce(
    (acc, n) => {
      acc[n.type] = (acc[n.type] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );
  const labels: Record<string, string> = {
    person: "人物",
    org: "組織",
    project: "案件",
    intel: "情報",
  };
  return (
    <ul className="space-y-1 text-sm">
      {Object.entries(counts).map(([type, count]) => (
        <li key={type} className="flex justify-between text-gray-400">
          <span>{labels[type] ?? type}</span>
          <span className="font-mono">{count}</span>
        </li>
      ))}
    </ul>
  );
}

function EdgeStats({ edges }: { edges: GraphData["edges"] }) {
  const counts = edges.reduce(
    (acc, e) => {
      acc[e.type] = (acc[e.type] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );
  return (
    <ul className="space-y-1 text-sm">
      {Object.entries(counts).map(([type, count]) => (
        <li key={type} className="flex justify-between text-gray-400">
          <span>{type}</span>
          <span className="font-mono">{count}</span>
        </li>
      ))}
    </ul>
  );
}
