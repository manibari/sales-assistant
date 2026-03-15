"use client";

import { useState, useEffect } from "react";
import {
  ChevronDown,
  ChevronRight,
  RefreshCw,
  Loader2,
  Tag,
} from "lucide-react";
import { nxApi, type NxKnowledge } from "@/lib/nexus-api";

export function KnowledgePanel({
  fileId,
  parseStatus,
  onReparsed,
}: {
  fileId: number;
  parseStatus: string;
  onReparsed?: () => void;
}) {
  const [chunks, setChunks] = useState<NxKnowledge[]>([]);
  const [loading, setLoading] = useState(false);
  const [reparsing, setReparsing] = useState(false);
  const [expandedChunk, setExpandedChunk] = useState<number | null>(null);

  useEffect(() => {
    if (parseStatus === "done" || parseStatus === "partial") {
      setLoading(true);
      nxApi.files
        .knowledge(fileId)
        .then(setChunks)
        .catch(console.error)
        .finally(() => setLoading(false));
    }
  }, [fileId, parseStatus]);

  const handleReparse = async () => {
    setReparsing(true);
    try {
      await nxApi.files.reparse(fileId);
      onReparsed?.();
    } catch (err) {
      console.error("Reparse failed:", err);
    } finally {
      setReparsing(false);
    }
  };

  if (loading) {
    return (
      <div className="px-4 py-3 flex items-center gap-2 text-xs text-slate-400">
        <Loader2 size={12} className="animate-spin" />
        載入知識段落...
      </div>
    );
  }

  return (
    <div className="border-t border-slate-200 dark:border-slate-700">
      {/* Reparse button for failed/partial */}
      {(parseStatus === "failed" || parseStatus === "partial") && (
        <div className="px-4 py-2 flex items-center gap-2">
          <button
            onClick={handleReparse}
            disabled={reparsing}
            className="flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg border border-blue-500/30 text-blue-500 hover:bg-blue-500/10 cursor-pointer transition-colors disabled:opacity-50"
          >
            {reparsing ? (
              <Loader2 size={12} className="animate-spin" />
            ) : (
              <RefreshCw size={12} />
            )}
            重新解析
          </button>
          {parseStatus === "failed" && (
            <span className="text-[11px] text-red-400">解析失敗</span>
          )}
          {parseStatus === "partial" && (
            <span className="text-[11px] text-amber-500">部分摘要缺失</span>
          )}
        </div>
      )}

      {chunks.length === 0 && parseStatus === "done" && (
        <div className="px-4 py-3 text-xs text-slate-400">無知識段落</div>
      )}

      {chunks.length > 0 && (
        <div className="divide-y divide-slate-100 dark:divide-slate-800">
          {chunks.map((chunk) => (
            <div key={chunk.id} className="px-4 py-2">
              <button
                onClick={() =>
                  setExpandedChunk(
                    expandedChunk === chunk.id ? null : chunk.id
                  )
                }
                className="w-full flex items-start gap-2 text-left cursor-pointer"
              >
                <span className="mt-0.5 flex-shrink-0 text-slate-400">
                  {expandedChunk === chunk.id ? (
                    <ChevronDown size={12} />
                  ) : (
                    <ChevronRight size={12} />
                  )}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="text-xs text-slate-700 dark:text-slate-300 line-clamp-2">
                    {chunk.summary || chunk.content.slice(0, 120) + "..."}
                  </p>
                  {chunk.tags && chunk.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-1">
                      {chunk.tags.map((tag, i) => (
                        <span
                          key={i}
                          className="inline-flex items-center gap-0.5 text-[10px] px-1.5 py-0.5 rounded-full bg-blue-500/10 text-blue-500"
                        >
                          <Tag size={8} />
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                {chunk.metadata && (
                  <span className="text-[10px] text-slate-400 flex-shrink-0">
                    {chunk.metadata.page_number
                      ? `p.${chunk.metadata.page_number}`
                      : chunk.metadata.slide_number
                        ? `#${chunk.metadata.slide_number}`
                        : ""}
                  </span>
                )}
              </button>
              {expandedChunk === chunk.id && (
                <div className="mt-2 ml-5 p-3 bg-slate-50 dark:bg-slate-800 rounded-lg text-xs text-slate-600 dark:text-slate-400 whitespace-pre-wrap max-h-60 overflow-auto">
                  {chunk.content}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
