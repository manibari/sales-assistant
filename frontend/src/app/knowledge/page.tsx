"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Loader2,
  Search,
  Brain,
  FileText,
  Tag,
  ChevronRight,
  ChevronDown,
  Building2,
  Filter,
} from "lucide-react";
import {
  nxApi,
  type NxKnowledge,
  type NxClient,
} from "@/lib/nexus-api";

export default function KnowledgePage() {
  const [chunks, setChunks] = useState<NxKnowledge[]>([]);
  const [clients, setClients] = useState<NxClient[]>([]);
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [query, setQuery] = useState("");
  const [clientFilter, setClientFilter] = useState<number | undefined>();
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [totalCount, setTotalCount] = useState(0);

  // Load clients for filter dropdown
  useEffect(() => {
    nxApi.clients.list("active").then(setClients).catch(console.error);
  }, []);

  // Initial load: all knowledge
  const loadAll = useCallback(async () => {
    setLoading(true);
    try {
      // Use search with empty-ish query to get all, or by-client
      if (clientFilter) {
        const data = await nxApi.knowledge.byClient(clientFilter);
        setChunks(data);
        setTotalCount(data.length);
      } else {
        const data = await nxApi.knowledge.all(200);
        setChunks(data);
        setTotalCount(data.length);
      }
    } catch {
      setChunks([]);
      setTotalCount(0);
    } finally {
      setLoading(false);
    }
  }, [clientFilter]);

  useEffect(() => {
    loadAll();
  }, [loadAll]);

  const handleSearch = async () => {
    const q = query.trim();
    if (q.length < 2) {
      loadAll();
      return;
    }
    setSearching(true);
    try {
      const results = await nxApi.knowledge.search(q, clientFilter);
      setChunks(results);
      setTotalCount(results.length);
    } catch {
      setChunks([]);
    } finally {
      setSearching(false);
    }
  };

  // Group by file
  const grouped = chunks.reduce<
    Record<string, { fileName: string; fileId: number; chunks: NxKnowledge[] }>
  >((acc, chunk) => {
    const key = String(chunk.file_id);
    if (!acc[key]) {
      acc[key] = {
        fileName: chunk.file_name || `File #${chunk.file_id}`,
        fileId: chunk.file_id,
        chunks: [],
      };
    }
    acc[key].chunks.push(chunk);
    return acc;
  }, {});

  // Collect all unique tags
  const allTags = Array.from(
    new Set(chunks.flatMap((c) => c.tags || []))
  ).slice(0, 20);

  return (
    <div className="flex flex-col h-full">
      <div className="h-14 px-4 flex items-center justify-between border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
        <div className="flex items-center gap-2">
          <Brain size={20} className="text-blue-500" />
          <h1 className="text-xl font-bold text-slate-900 dark:text-slate-50">
            知識庫
          </h1>
        </div>
        <span className="text-xs text-slate-400">
          {totalCount} 段知識
        </span>
      </div>

      <div className="flex-1 px-4 py-4 overflow-auto max-w-2xl lg:max-w-4xl mx-auto w-full space-y-4">
        {/* Search + Filter */}
        <div className="flex gap-2">
          <div className="flex-1 relative">
            <Search
              size={14}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
            />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              placeholder="搜尋所有知識..."
              className="w-full pl-8 pr-3 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-50 focus:outline-none focus:border-blue-500"
            />
          </div>
          <button
            onClick={handleSearch}
            disabled={searching}
            className="flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-lg bg-blue-500 text-white hover:bg-blue-600 cursor-pointer transition-colors disabled:opacity-50"
          >
            {searching ? (
              <Loader2 size={14} className="animate-spin" />
            ) : (
              <Search size={14} />
            )}
            搜尋
          </button>
        </div>

        {/* Client filter */}
        <div className="flex items-center gap-2">
          <Filter size={14} className="text-slate-400" />
          <select
            value={clientFilter ?? ""}
            onChange={(e) =>
              setClientFilter(e.target.value ? Number(e.target.value) : undefined)
            }
            className="text-xs bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg px-3 py-1.5 text-slate-700 dark:text-slate-300 focus:outline-none focus:border-blue-500"
          >
            <option value="">所有公司</option>
            {clients.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
          {allTags.length > 0 && (
            <div className="flex flex-wrap gap-1 ml-2">
              {allTags.slice(0, 8).map((tag) => (
                <button
                  key={tag}
                  onClick={() => {
                    setQuery(tag);
                    setTimeout(handleSearch, 0);
                  }}
                  className="inline-flex items-center gap-0.5 text-[10px] px-1.5 py-0.5 rounded-full bg-blue-500/10 text-blue-500 cursor-pointer hover:bg-blue-500/20 transition-colors"
                >
                  <Tag size={8} />
                  {tag}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Content */}
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 size={20} className="animate-spin text-blue-500" />
          </div>
        ) : Object.keys(grouped).length === 0 ? (
          <div className="text-center py-12 text-slate-400 text-sm">
            {query ? "找不到相關知識" : "尚無知識段落，請上傳 PDF / PPTX / DOCX 文件"}
          </div>
        ) : (
          <div className="space-y-3">
            {Object.values(grouped).map((group) => (
              <FileGroup
                key={group.fileId}
                fileName={group.fileName}
                chunks={group.chunks}
                expandedId={expandedId}
                onToggleExpand={(id) =>
                  setExpandedId(expandedId === id ? null : id)
                }
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function FileGroup({
  fileName,
  chunks,
  expandedId,
  onToggleExpand,
}: {
  fileName: string;
  chunks: NxKnowledge[];
  expandedId: number | null;
  onToggleExpand: (id: number) => void;
}) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl overflow-hidden">
      {/* File header */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="w-full px-4 py-3 flex items-center justify-between gap-2 text-left cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
      >
        <div className="flex items-center gap-2 min-w-0">
          <FileText size={14} className="text-blue-500 flex-shrink-0" />
          <span className="text-sm font-medium text-slate-900 dark:text-slate-50 truncate">
            {fileName}
          </span>
          <span className="text-[10px] text-slate-400 flex-shrink-0">
            {chunks.length} 段
          </span>
        </div>
        {collapsed ? (
          <ChevronRight size={14} className="text-slate-400" />
        ) : (
          <ChevronDown size={14} className="text-slate-400" />
        )}
      </button>

      {/* Chunks */}
      {!collapsed && (
        <div className="border-t border-slate-100 dark:border-slate-800 divide-y divide-slate-100 dark:divide-slate-800">
          {chunks.map((chunk) => (
            <div key={chunk.id} className="px-4 py-2">
              <button
                onClick={() => onToggleExpand(chunk.id)}
                className="w-full flex items-start gap-2 text-left cursor-pointer"
              >
                <span className="mt-0.5 flex-shrink-0 text-slate-400">
                  {expandedId === chunk.id ? (
                    <ChevronDown size={12} />
                  ) : (
                    <ChevronRight size={12} />
                  )}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="text-xs text-slate-700 dark:text-slate-300 line-clamp-2">
                    {chunk.summary || chunk.content.slice(0, 150)}
                  </p>
                  {chunk.tags && chunk.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-1">
                      {chunk.tags.map((tag, i) => (
                        <span
                          key={i}
                          className="text-[10px] px-1.5 py-0.5 rounded-full bg-blue-500/10 text-blue-500"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                {chunk.metadata && (
                  <span className="text-[10px] text-slate-400 flex-shrink-0">
                    {(chunk.metadata as Record<string, unknown>).page_number
                      ? `p.${(chunk.metadata as Record<string, unknown>).page_number}`
                      : (chunk.metadata as Record<string, unknown>).slide_number
                        ? `#${(chunk.metadata as Record<string, unknown>).slide_number}`
                        : ""}
                  </span>
                )}
              </button>
              {expandedId === chunk.id && (
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
