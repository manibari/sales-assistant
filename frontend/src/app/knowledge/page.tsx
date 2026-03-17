"use client";

import { useState, useEffect, useCallback } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  Loader2,
  Search,
  Brain,
  FileText,
  Tag,
  ArrowLeft,
  Plus,
  Pencil,
  Trash2,
  RefreshCw,
  Inbox,
  BookOpen,
  Archive,
  ArrowUpRight,
  ChevronRight,
  ChevronDown,
  X,
  FilePlus2,
  FolderOpen,
  CheckCircle2,
  Clock,
} from "lucide-react";
import {
  nxApi,
  type NxMemory,
  type NxMemoryCategory,
  type NxMemoryTemplate,
} from "@/lib/nexus-api";

type Tab = "inbox" | "library";
type ViewMode = "list" | "read" | "edit";

const TYPE_LABELS: Record<string, string> = {
  "client-profile": "客戶",
  "deal-overview": "案件",
  intel: "情報",
  meeting: "會議",
  "file-summary": "文件",
  "domain-insight": "領域知識",
  "deal-note": "案件知識",
  manual: "手動",
};

const STATUS_CONFIG: Record<string, { label: string; color: string }> = {
  inbox: { label: "收件匣", color: "bg-orange-500/10 text-orange-600" },
  draft: { label: "草稿", color: "bg-yellow-500/10 text-yellow-600" },
  published: { label: "已發布", color: "bg-green-500/10 text-green-600" },
  archived: { label: "已封存", color: "bg-slate-500/10 text-slate-500" },
};

export default function KnowledgePage() {
  const [tab, setTab] = useState<Tab>("inbox");
  const [memories, setMemories] = useState<NxMemory[]>([]);
  const [categories, setCategories] = useState<NxMemoryCategory[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [query, setQuery] = useState("");
  const [searching, setSearching] = useState(false);
  // Library filters
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [categoryFilter, setCategoryFilter] = useState<string>("");
  const [zoneFilter, setZoneFilter] = useState<string>("");
  // View
  const [viewMode, setViewMode] = useState<ViewMode>("list");
  const [selectedMemory, setSelectedMemory] = useState<NxMemory | null>(null);
  const [editBody, setEditBody] = useState("");
  // Modals
  const [showPromote, setShowPromote] = useState(false);
  const [promoteSource, setPromoteSource] = useState<NxMemory | null>(null);
  const [showTemplate, setShowTemplate] = useState(false);
  const [showCreate, setShowCreate] = useState(false);

  // Inbox count
  const [inboxCount, setInboxCount] = useState(0);

  const loadInboxCount = useCallback(async () => {
    try {
      const data = await nxApi.memory.list({ status: "inbox" });
      setInboxCount(data.length);
    } catch {
      /* ignore */
    }
  }, []);

  const loadCategories = useCallback(async () => {
    try {
      const cats = await nxApi.memory.categories();
      setCategories(cats);
    } catch {
      /* ignore */
    }
  }, []);

  const loadAll = useCallback(async () => {
    setLoading(true);
    try {
      if (tab === "inbox") {
        const data = await nxApi.memory.list({ status: "inbox" });
        setMemories(data);
        setInboxCount(data.length);
      } else {
        const params: Record<string, string> = {};
        if (statusFilter) params.status = statusFilter;
        else {
          // Library shows draft + published by default (not inbox, not archived)
          // We filter client-side since API only supports single status
        }
        if (categoryFilter) params.category = categoryFilter;
        if (zoneFilter) params.zone = zoneFilter;
        const data = await nxApi.memory.list(params);
        // Filter to only draft/published unless explicit filter
        if (!statusFilter) {
          setMemories(data.filter((m) => m.status === "draft" || m.status === "published"));
        } else {
          setMemories(data);
        }
      }
    } catch {
      setMemories([]);
    } finally {
      setLoading(false);
    }
  }, [tab, statusFilter, categoryFilter, zoneFilter]);

  useEffect(() => {
    loadAll();
    loadCategories();
  }, [loadAll, loadCategories]);

  useEffect(() => {
    if (tab === "library") loadInboxCount();
  }, [tab, loadInboxCount]);

  const handleSearch = async () => {
    const q = query.trim();
    if (q.length < 2) {
      loadAll();
      return;
    }
    setSearching(true);
    try {
      const results = await nxApi.memory.search(q);
      if (tab === "inbox") {
        setMemories(results.filter((m) => m.status === "inbox" || !m.status));
      } else {
        setMemories(results.filter((m) => m.status === "draft" || m.status === "published"));
      }
    } catch {
      setMemories([]);
    } finally {
      setSearching(false);
    }
  };

  const handleSync = async () => {
    setSyncing(true);
    try {
      await nxApi.memory.syncAll();
      await loadAll();
    } finally {
      setSyncing(false);
    }
  };

  const openMemory = async (path: string) => {
    try {
      const mem = await nxApi.memory.get(path);
      setSelectedMemory(mem);
      setEditBody(mem._body || "");
      setViewMode("read");
    } catch {
      console.error("Failed to load memory");
    }
  };

  const handleDelete = async (path: string) => {
    if (!confirm("確定刪除？")) return;
    try {
      await nxApi.memory.delete(path);
      setViewMode("list");
      setSelectedMemory(null);
      loadAll();
    } catch {
      console.error("Failed to delete");
    }
  };

  const handleArchive = async (path: string) => {
    try {
      await nxApi.memory.updateStatus(path, "archived");
      loadAll();
    } catch {
      console.error("Failed to archive");
    }
  };

  const handleStatusChange = async (path: string, status: string) => {
    try {
      await nxApi.memory.updateStatus(path, status);
      if (selectedMemory?.path === path) {
        setSelectedMemory({ ...selectedMemory, status });
      }
      loadAll();
    } catch {
      console.error("Failed to update status");
    }
  };

  const handleSaveEdit = async () => {
    if (!selectedMemory) return;
    try {
      const updated = await nxApi.memory.update(selectedMemory.path, {
        body: editBody,
      });
      setSelectedMemory({ ...selectedMemory, _body: editBody, ...updated });
      setViewMode("read");
      loadAll();
    } catch {
      console.error("Failed to save");
    }
  };

  const openPromoteModal = (mem: NxMemory) => {
    setPromoteSource(mem);
    setShowPromote(true);
  };

  // Read / Edit view
  if (viewMode === "read" && selectedMemory) {
    return (
      <div className="flex flex-col h-full">
        <div className="h-14 px-4 flex items-center justify-between border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
          <button
            onClick={() => {
              setViewMode("list");
              setSelectedMemory(null);
            }}
            className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-900 dark:hover:text-slate-200 cursor-pointer transition-colors"
          >
            <ArrowLeft size={16} />
            返回
          </button>
          <div className="flex items-center gap-2">
            {selectedMemory.status === "draft" && (
              <button
                onClick={() => handleStatusChange(selectedMemory.path, "published")}
                className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium rounded-lg bg-green-500/10 text-green-600 hover:bg-green-500/20 cursor-pointer transition-colors"
              >
                <CheckCircle2 size={12} />
                發布
              </button>
            )}
            {selectedMemory.status === "published" && (
              <button
                onClick={() => handleStatusChange(selectedMemory.path, "draft")}
                className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium rounded-lg bg-yellow-500/10 text-yellow-600 hover:bg-yellow-500/20 cursor-pointer transition-colors"
              >
                <Clock size={12} />
                退回草稿
              </button>
            )}
            <button
              onClick={() => setViewMode("edit")}
              className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 cursor-pointer transition-colors"
            >
              <Pencil size={12} />
              編輯
            </button>
            <button
              onClick={() => handleDelete(selectedMemory.path)}
              className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium rounded-lg bg-red-500/10 text-red-500 hover:bg-red-500/20 cursor-pointer transition-colors"
            >
              <Trash2 size={12} />
              刪除
            </button>
          </div>
        </div>
        <div className="flex-1 px-4 py-4 overflow-auto max-w-3xl mx-auto w-full">
          {/* Metadata badges */}
          <div className="mb-4 flex flex-wrap gap-2 items-center">
            <TypeBadge type={selectedMemory.type} />
            {selectedMemory.status && <StatusBadge status={selectedMemory.status} />}
            {selectedMemory.category && (
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-600 font-medium">
                {selectedMemory.category}
              </span>
            )}
            {selectedMemory.client && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600">
                {selectedMemory.client}
              </span>
            )}
            {selectedMemory.source === "auto" && (
              <span className="text-[10px] text-slate-400">
                auto from {selectedMemory.source_type} #{selectedMemory.source_id}
              </span>
            )}
            {selectedMemory.source === "promoted" && selectedMemory.promoted_from && (
              <span className="text-[10px] text-slate-400">
                promoted from {selectedMemory.promoted_from}
              </span>
            )}
          </div>
          {selectedMemory.tags && selectedMemory.tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mb-3">
              {selectedMemory.tags.map((tag) => (
                <span key={tag} className="text-[10px] px-1.5 py-0.5 rounded-full bg-blue-500/10 text-blue-500">
                  {tag}
                </span>
              ))}
            </div>
          )}
          <div className="text-xs text-slate-400 mb-4">
            建立: {selectedMemory.created} | 更新: {selectedMemory.updated}
          </div>
          {/* Related items */}
          {selectedMemory.related && selectedMemory.related.length > 0 && (
            <div className="mb-4 p-3 rounded-lg bg-slate-50 dark:bg-slate-800/50">
              <div className="text-xs font-medium text-slate-500 mb-1">相關知識</div>
              {selectedMemory.related.map((r) => (
                <button key={r} onClick={() => openMemory(r)} className="block text-xs text-blue-500 hover:underline cursor-pointer">
                  {r}
                </button>
              ))}
            </div>
          )}
          {/* Markdown body */}
          <article className="prose prose-sm dark:prose-invert max-w-none">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {selectedMemory._body || ""}
            </ReactMarkdown>
          </article>
        </div>
      </div>
    );
  }

  // Edit view
  if (viewMode === "edit" && selectedMemory) {
    return (
      <div className="flex flex-col h-full">
        <div className="h-14 px-4 flex items-center justify-between border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
          <button
            onClick={() => setViewMode("read")}
            className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-900 dark:hover:text-slate-200 cursor-pointer transition-colors"
          >
            <ArrowLeft size={16} />
            取消
          </button>
          <button
            onClick={handleSaveEdit}
            className="px-4 py-1.5 text-xs font-medium rounded-lg bg-blue-500 text-white hover:bg-blue-600 cursor-pointer transition-colors"
          >
            儲存
          </button>
        </div>
        <div className="flex-1 p-4 overflow-auto">
          <textarea
            value={editBody}
            onChange={(e) => setEditBody(e.target.value)}
            className="w-full h-full min-h-[60vh] p-4 text-sm font-mono rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-50 focus:outline-none focus:border-blue-500 resize-none"
          />
        </div>
      </div>
    );
  }

  // List view (default)
  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="h-14 px-4 flex items-center justify-between border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
        <div className="flex items-center gap-2">
          <Brain size={20} className="text-blue-500" />
          <h1 className="text-xl font-bold text-slate-900 dark:text-slate-50">
            知識管理
          </h1>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleSync}
            disabled={syncing}
            className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 cursor-pointer transition-colors disabled:opacity-50"
          >
            <RefreshCw size={12} className={syncing ? "animate-spin" : ""} />
            同步
          </button>
          {tab === "library" && (
            <>
              <button
                onClick={() => setShowTemplate(true)}
                className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 cursor-pointer transition-colors"
              >
                <FilePlus2 size={12} />
                從模板建立
              </button>
              <button
                onClick={() => setShowCreate(true)}
                className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium rounded-lg bg-blue-500 text-white hover:bg-blue-600 cursor-pointer transition-colors"
              >
                <Plus size={12} />
                新增
              </button>
            </>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="px-4 pt-3 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800">
        <div className="flex gap-1">
          <button
            onClick={() => setTab("inbox")}
            className={`flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-t-lg border-b-2 transition-colors cursor-pointer ${
              tab === "inbox"
                ? "border-blue-500 text-blue-600 bg-blue-50 dark:bg-blue-500/10"
                : "border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"
            }`}
          >
            <Inbox size={14} />
            收件匣
            {inboxCount > 0 && (
              <span className="ml-1 px-1.5 py-0.5 text-[10px] font-bold rounded-full bg-orange-500 text-white">
                {inboxCount}
              </span>
            )}
          </button>
          <button
            onClick={() => setTab("library")}
            className={`flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-t-lg border-b-2 transition-colors cursor-pointer ${
              tab === "library"
                ? "border-blue-500 text-blue-600 bg-blue-50 dark:bg-blue-500/10"
                : "border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"
            }`}
          >
            <BookOpen size={14} />
            知識庫
          </button>
        </div>
      </div>

      <div className="flex-1 px-4 py-4 overflow-auto max-w-3xl mx-auto w-full space-y-4">
        {/* Search */}
        <div className="flex gap-2">
          <div className="flex-1 relative">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              placeholder={tab === "inbox" ? "搜尋素材..." : "搜尋知識..."}
              className="w-full pl-8 pr-3 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-50 focus:outline-none focus:border-blue-500"
            />
          </div>
          <button
            onClick={handleSearch}
            disabled={searching}
            className="flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-lg bg-blue-500 text-white hover:bg-blue-600 cursor-pointer transition-colors disabled:opacity-50"
          >
            {searching ? <Loader2 size={14} className="animate-spin" /> : <Search size={14} />}
            搜尋
          </button>
        </div>

        {/* Library filters */}
        {tab === "library" && (
          <div className="flex items-center gap-2 flex-wrap">
            <select
              value={zoneFilter}
              onChange={(e) => setZoneFilter(e.target.value)}
              className="text-xs bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg px-3 py-1.5 text-slate-700 dark:text-slate-300 focus:outline-none focus:border-blue-500"
            >
              <option value="">所有範圍</option>
              <option value="domain">領域知識</option>
              <option value="deals">案件知識</option>
            </select>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="text-xs bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg px-3 py-1.5 text-slate-700 dark:text-slate-300 focus:outline-none focus:border-blue-500"
            >
              <option value="">草稿 + 已發布</option>
              <option value="draft">草稿</option>
              <option value="published">已發布</option>
              <option value="archived">已封存</option>
            </select>
            {categories.length > 0 && (
              <select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                className="text-xs bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg px-3 py-1.5 text-slate-700 dark:text-slate-300 focus:outline-none focus:border-blue-500"
              >
                <option value="">所有分類</option>
                {categories.map((c) => (
                  <option key={c.name} value={c.name}>
                    {c.name} ({c.count})
                  </option>
                ))}
              </select>
            )}
          </div>
        )}

        {/* Content */}
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 size={20} className="animate-spin text-blue-500" />
          </div>
        ) : memories.length === 0 ? (
          <div className="text-center py-12 text-slate-400 text-sm">
            {tab === "inbox"
              ? "收件匣是空的。點擊「同步」從資料庫匯入素材。"
              : "知識庫是空的。從收件匣提煉素材，或直接新增。"}
          </div>
        ) : tab === "inbox" ? (
          <InboxList
            memories={memories}
            onOpen={openMemory}
            onPromote={openPromoteModal}
            onArchive={handleArchive}
            onDelete={handleDelete}
          />
        ) : (
          <LibraryList memories={memories} onOpen={openMemory} />
        )}
      </div>

      {/* Promote Modal */}
      {showPromote && promoteSource && (
        <PromoteModal
          source={promoteSource}
          categories={categories}
          onClose={() => {
            setShowPromote(false);
            setPromoteSource(null);
          }}
          onPromoted={() => {
            setShowPromote(false);
            setPromoteSource(null);
            loadAll();
            loadCategories();
          }}
        />
      )}

      {/* Template Picker */}
      {showTemplate && (
        <TemplatePicker
          categories={categories}
          onClose={() => setShowTemplate(false)}
          onCreated={() => {
            setShowTemplate(false);
            loadAll();
            loadCategories();
          }}
        />
      )}

      {/* Create Modal */}
      {showCreate && (
        <CreateModal
          categories={categories}
          onClose={() => setShowCreate(false)}
          onCreated={() => {
            setShowCreate(false);
            loadAll();
            loadCategories();
          }}
        />
      )}
    </div>
  );
}

// --- Inbox list ---
function InboxList({
  memories,
  onOpen,
  onPromote,
  onArchive,
  onDelete,
}: {
  memories: NxMemory[];
  onOpen: (path: string) => void;
  onPromote: (mem: NxMemory) => void;
  onArchive: (path: string) => void;
  onDelete: (path: string) => void;
}) {
  return (
    <div className="space-y-2">
      {memories.map((mem) => (
        <div
          key={mem.path}
          className="px-4 py-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl hover:border-blue-300 dark:hover:border-blue-700 transition-colors"
        >
          <div className="flex items-center justify-between gap-2">
            <button
              onClick={() => onOpen(mem.path)}
              className="flex items-center gap-2 min-w-0 flex-1 text-left cursor-pointer"
            >
              <FileText size={14} className="text-orange-500 flex-shrink-0" />
              <span className="text-sm font-medium text-slate-900 dark:text-slate-50 truncate">
                {mem.title}
              </span>
            </button>
            <div className="flex items-center gap-1.5 flex-shrink-0">
              <button
                onClick={() => onPromote(mem)}
                className="flex items-center gap-1 px-2.5 py-1 text-[10px] font-medium rounded-lg bg-blue-500 text-white hover:bg-blue-600 cursor-pointer transition-colors"
              >
                <ArrowUpRight size={10} />
                加入知識庫
              </button>
              <button
                onClick={() => onArchive(mem.path)}
                className="p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 cursor-pointer transition-colors"
                title="封存"
              >
                <Archive size={12} />
              </button>
              <button
                onClick={() => onDelete(mem.path)}
                className="p-1.5 text-slate-400 hover:text-red-500 cursor-pointer transition-colors"
                title="刪除"
              >
                <Trash2 size={12} />
              </button>
            </div>
          </div>
          <div className="flex items-center gap-2 mt-1.5 ml-6">
            <TypeBadge type={mem.type} />
            {mem.client && (
              <span className="text-[10px] text-emerald-600">{mem.client}</span>
            )}
            <span className="text-[10px] text-slate-400 ml-auto">{mem.updated}</span>
          </div>
          {mem.tags && mem.tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-1.5 ml-6">
              {mem.tags.slice(0, 5).map((tag) => (
                <span key={tag} className="text-[10px] px-1.5 py-0.5 rounded-full bg-blue-500/10 text-blue-500">
                  <Tag size={8} className="inline mr-0.5" />
                  {tag}
                </span>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

// --- Library list ---
function LibraryList({
  memories,
  onOpen,
}: {
  memories: NxMemory[];
  onOpen: (path: string) => void;
}) {
  // Group by category
  const grouped = memories.reduce<Record<string, NxMemory[]>>((acc, mem) => {
    const cat = mem.category || "未分類";
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(mem);
    return acc;
  }, {});

  return (
    <div className="space-y-6">
      {Object.entries(grouped).map(([cat, mems]) => (
        <CategoryGroup key={cat} category={cat} memories={mems} onOpen={onOpen} />
      ))}
    </div>
  );
}

function CategoryGroup({
  category,
  memories,
  onOpen,
}: {
  category: string;
  memories: NxMemory[];
  onOpen: (path: string) => void;
}) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div>
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="flex items-center gap-2 mb-2 cursor-pointer hover:opacity-80 transition-opacity"
      >
        {collapsed ? (
          <ChevronRight size={14} className="text-slate-400" />
        ) : (
          <ChevronDown size={14} className="text-slate-400" />
        )}
        <FolderOpen size={14} className="text-indigo-500" />
        <span className="text-xs font-medium text-slate-600 dark:text-slate-400">
          {category}
        </span>
        <span className="text-[10px] text-slate-400">{memories.length}</span>
      </button>
      {!collapsed && (
        <div className="space-y-1.5">
          {memories.map((mem) => (
            <button
              key={mem.path}
              onClick={() => onOpen(mem.path)}
              className="w-full text-left px-4 py-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl hover:border-blue-300 dark:hover:border-blue-700 cursor-pointer transition-colors"
            >
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2 min-w-0">
                  <FileText size={14} className="text-blue-500 flex-shrink-0" />
                  <span className="text-sm font-medium text-slate-900 dark:text-slate-50 truncate">
                    {mem.title}
                  </span>
                </div>
                <div className="flex items-center gap-1.5 flex-shrink-0">
                  <TypeBadge type={mem.type} />
                  {mem.status && <StatusBadge status={mem.status} />}
                </div>
              </div>
              <div className="flex items-center gap-2 mt-1.5 ml-6">
                {mem.client && (
                  <span className="text-[10px] text-emerald-600">{mem.client}</span>
                )}
                <span className="text-[10px] text-slate-400 ml-auto">{mem.updated}</span>
              </div>
              {mem.tags && mem.tags.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-1.5 ml-6">
                  {mem.tags.slice(0, 5).map((tag) => (
                    <span key={tag} className="text-[10px] px-1.5 py-0.5 rounded-full bg-blue-500/10 text-blue-500">
                      <Tag size={8} className="inline mr-0.5" />
                      {tag}
                    </span>
                  ))}
                </div>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

// --- Badges ---
function TypeBadge({ type }: { type: string }) {
  const label = TYPE_LABELS[type] || type;
  return (
    <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-purple-500/10 text-purple-500 font-medium">
      {label}
    </span>
  );
}

function StatusBadge({ status }: { status: string }) {
  const cfg = STATUS_CONFIG[status] || { label: status, color: "bg-slate-500/10 text-slate-500" };
  return (
    <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium ${cfg.color}`}>
      {cfg.label}
    </span>
  );
}

// --- Promote Modal ---
function PromoteModal({
  source,
  categories,
  onClose,
  onPromoted,
}: {
  source: NxMemory;
  categories: NxMemoryCategory[];
  onClose: () => void;
  onPromoted: () => void;
}) {
  const [targetZone, setTargetZone] = useState<"domain" | "deals">("domain");
  const [category, setCategory] = useState("");
  const [newCategory, setNewCategory] = useState("");
  const [title, setTitle] = useState(source.title);
  const [body, setBody] = useState(source._body || "");
  const [tags, setTags] = useState(source.tags?.join(", ") || "");
  const [saving, setSaving] = useState(false);
  const [loadingBody, setLoadingBody] = useState(!source._body);

  // Load body if not present
  useEffect(() => {
    if (!source._body) {
      nxApi.memory.get(source.path).then((full) => {
        setBody(full._body || "");
        setLoadingBody(false);
      }).catch(() => setLoadingBody(false));
    }
  }, [source]);

  const finalCategory = newCategory.trim() || category;

  const handlePromote = async () => {
    if (!title.trim() || !finalCategory) return;
    setSaving(true);
    try {
      await nxApi.memory.promote({
        source_path: source.path,
        target_zone: targetZone,
        category: finalCategory,
        new_title: title.trim(),
        new_body: body,
        tags: tags
          .split(",")
          .map((t) => t.trim())
          .filter(Boolean),
      });
      onPromoted();
    } catch (e) {
      console.error("Promote failed", e);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-xl w-full max-w-4xl mx-4 max-h-[85vh] flex flex-col">
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-200 dark:border-slate-700">
          <h2 className="text-lg font-bold text-slate-900 dark:text-slate-50">
            加入知識庫
          </h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 cursor-pointer">
            <X size={18} />
          </button>
        </div>

        <div className="flex-1 flex overflow-hidden">
          {/* Left: source preview */}
          <div className="w-1/2 border-r border-slate-200 dark:border-slate-700 p-4 overflow-auto">
            <div className="text-xs font-medium text-slate-500 mb-2">原始素材</div>
            <div className="text-sm font-medium text-slate-900 dark:text-slate-50 mb-2">
              {source.title}
            </div>
            <div className="flex flex-wrap gap-1 mb-3">
              <TypeBadge type={source.type} />
              {source.client && (
                <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600">
                  {source.client}
                </span>
              )}
            </div>
            {loadingBody ? (
              <Loader2 size={16} className="animate-spin text-blue-500" />
            ) : (
              <article className="prose prose-xs dark:prose-invert max-w-none text-xs">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{body}</ReactMarkdown>
              </article>
            )}
          </div>

          {/* Right: promote form */}
          <div className="w-1/2 p-4 overflow-auto space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">
                目標
              </label>
              <div className="flex gap-2">
                <button
                  onClick={() => setTargetZone("domain")}
                  className={`flex-1 py-2 text-sm font-medium rounded-lg border cursor-pointer transition-colors ${
                    targetZone === "domain"
                      ? "border-blue-500 bg-blue-50 dark:bg-blue-500/10 text-blue-600"
                      : "border-slate-200 dark:border-slate-700 text-slate-500"
                  }`}
                >
                  領域知識
                </button>
                <button
                  onClick={() => setTargetZone("deals")}
                  className={`flex-1 py-2 text-sm font-medium rounded-lg border cursor-pointer transition-colors ${
                    targetZone === "deals"
                      ? "border-blue-500 bg-blue-50 dark:bg-blue-500/10 text-blue-600"
                      : "border-slate-200 dark:border-slate-700 text-slate-500"
                  }`}
                >
                  案件知識
                </button>
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">
                分類
              </label>
              {categories.length > 0 && (
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full px-3 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-50 focus:outline-none focus:border-blue-500 mb-2"
                >
                  <option value="">選擇現有分類...</option>
                  {categories.map((c) => (
                    <option key={c.name} value={c.name}>
                      {c.name} ({c.count})
                    </option>
                  ))}
                </select>
              )}
              <input
                value={newCategory}
                onChange={(e) => setNewCategory(e.target.value)}
                placeholder="或輸入新分類..."
                className="w-full px-3 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-50 focus:outline-none focus:border-blue-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">
                標題
              </label>
              <input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full px-3 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-50 focus:outline-none focus:border-blue-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">
                內容（可編輯）
              </label>
              <textarea
                value={body}
                onChange={(e) => setBody(e.target.value)}
                rows={10}
                className="w-full px-3 py-2 text-sm font-mono rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-50 focus:outline-none focus:border-blue-500 resize-none"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">
                標籤（逗號分隔）
              </label>
              <input
                value={tags}
                onChange={(e) => setTags(e.target.value)}
                className="w-full px-3 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-50 focus:outline-none focus:border-blue-500"
                placeholder="AI, 食品製造, ..."
              />
            </div>
          </div>
        </div>

        <div className="flex justify-end gap-2 px-5 py-4 border-t border-slate-200 dark:border-slate-700">
          <button onClick={onClose} className="px-4 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 cursor-pointer transition-colors">
            取消
          </button>
          <button
            onClick={handlePromote}
            disabled={!title.trim() || !finalCategory || saving}
            className="px-4 py-2 text-sm font-medium rounded-lg bg-blue-500 text-white hover:bg-blue-600 cursor-pointer transition-colors disabled:opacity-50"
          >
            {saving ? <Loader2 size={14} className="animate-spin" /> : "提煉為知識"}
          </button>
        </div>
      </div>
    </div>
  );
}

// --- Template Picker Modal ---
function TemplatePicker({
  categories,
  onClose,
  onCreated,
}: {
  categories: NxMemoryCategory[];
  onClose: () => void;
  onCreated: () => void;
}) {
  const [templates, setTemplates] = useState<NxMemoryTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTemplate, setSelectedTemplate] = useState("");
  const [targetZone, setTargetZone] = useState<"domain" | "deals">("domain");
  const [category, setCategory] = useState("");
  const [newCategory, setNewCategory] = useState("");
  const [title, setTitle] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    nxApi.memory
      .templates()
      .then((t) => {
        setTemplates(t);
        if (t.length > 0) setSelectedTemplate(t[0].name);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const finalCategory = newCategory.trim() || category;

  const handleCreate = async () => {
    if (!selectedTemplate || !title.trim() || !finalCategory) return;
    setSaving(true);
    try {
      await nxApi.memory.fromTemplate({
        template_name: selectedTemplate,
        target_zone: targetZone,
        category: finalCategory,
        title: title.trim(),
      });
      onCreated();
    } catch (e) {
      console.error("From template failed", e);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-xl w-full max-w-lg mx-4 max-h-[80vh] overflow-auto">
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-200 dark:border-slate-700">
          <h2 className="text-lg font-bold text-slate-900 dark:text-slate-50">從模板建立</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 cursor-pointer">
            <X size={18} />
          </button>
        </div>
        <div className="p-5 space-y-4">
          {loading ? (
            <div className="flex justify-center py-4">
              <Loader2 size={20} className="animate-spin text-blue-500" />
            </div>
          ) : (
            <>
              <div>
                <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">模板</label>
                <div className="space-y-2">
                  {templates.map((t) => (
                    <button
                      key={t.name}
                      onClick={() => setSelectedTemplate(t.name)}
                      className={`w-full text-left px-3 py-2.5 rounded-lg border cursor-pointer transition-colors ${
                        selectedTemplate === t.name
                          ? "border-blue-500 bg-blue-50 dark:bg-blue-500/10"
                          : "border-slate-200 dark:border-slate-700 hover:border-slate-300"
                      }`}
                    >
                      <div className="text-sm font-medium text-slate-900 dark:text-slate-50">{t.title}</div>
                      <div className="text-xs text-slate-500 mt-0.5">{t.description}</div>
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">目標</label>
                <div className="flex gap-2">
                  <button
                    onClick={() => setTargetZone("domain")}
                    className={`flex-1 py-2 text-sm font-medium rounded-lg border cursor-pointer transition-colors ${
                      targetZone === "domain"
                        ? "border-blue-500 bg-blue-50 dark:bg-blue-500/10 text-blue-600"
                        : "border-slate-200 dark:border-slate-700 text-slate-500"
                    }`}
                  >
                    領域知識
                  </button>
                  <button
                    onClick={() => setTargetZone("deals")}
                    className={`flex-1 py-2 text-sm font-medium rounded-lg border cursor-pointer transition-colors ${
                      targetZone === "deals"
                        ? "border-blue-500 bg-blue-50 dark:bg-blue-500/10 text-blue-600"
                        : "border-slate-200 dark:border-slate-700 text-slate-500"
                    }`}
                  >
                    案件知識
                  </button>
                </div>
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">分類</label>
                {categories.length > 0 && (
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    className="w-full px-3 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-50 focus:outline-none focus:border-blue-500 mb-2"
                  >
                    <option value="">選擇現有分類...</option>
                    {categories.map((c) => (
                      <option key={c.name} value={c.name}>{c.name} ({c.count})</option>
                    ))}
                  </select>
                )}
                <input
                  value={newCategory}
                  onChange={(e) => setNewCategory(e.target.value)}
                  placeholder="或輸入新分類..."
                  className="w-full px-3 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-50 focus:outline-none focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">標題 *</label>
                <input
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full px-3 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-50 focus:outline-none focus:border-blue-500"
                  placeholder="知識標題"
                />
              </div>
            </>
          )}
        </div>
        <div className="flex justify-end gap-2 px-5 py-4 border-t border-slate-200 dark:border-slate-700">
          <button onClick={onClose} className="px-4 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 cursor-pointer transition-colors">
            取消
          </button>
          <button
            onClick={handleCreate}
            disabled={!selectedTemplate || !title.trim() || !finalCategory || saving}
            className="px-4 py-2 text-sm font-medium rounded-lg bg-blue-500 text-white hover:bg-blue-600 cursor-pointer transition-colors disabled:opacity-50"
          >
            {saving ? <Loader2 size={14} className="animate-spin" /> : "建立"}
          </button>
        </div>
      </div>
    </div>
  );
}

// --- Create Modal (direct) ---
function CreateModal({
  categories,
  onClose,
  onCreated,
}: {
  categories: NxMemoryCategory[];
  onClose: () => void;
  onCreated: () => void;
}) {
  const [targetZone, setTargetZone] = useState<"domain" | "deals">("domain");
  const [category, setCategory] = useState("");
  const [newCategory, setNewCategory] = useState("");
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [tags, setTags] = useState("");
  const [saving, setSaving] = useState(false);

  const finalCategory = newCategory.trim() || category;

  const handleCreate = async () => {
    if (!title.trim() || !finalCategory) return;
    setSaving(true);
    try {
      const catSlug = finalCategory.replace(/[\s/\\:*?"<>|]+/g, "-").replace(/^-+|-+$/g, "");
      const folder = targetZone === "domain" ? `domain/${catSlug}` : `deals/${catSlug}`;
      await nxApi.memory.create({
        title: title.trim(),
        type: targetZone === "domain" ? "domain-insight" : "deal-note",
        scope: targetZone === "domain" ? "long-term" : "short-term",
        tags: tags.split(",").map((t) => t.trim()).filter(Boolean),
        body,
        folder,
      });
      onCreated();
    } catch (e) {
      console.error("Create failed", e);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-xl w-full max-w-lg mx-4 max-h-[80vh] overflow-auto">
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-200 dark:border-slate-700">
          <h2 className="text-lg font-bold text-slate-900 dark:text-slate-50">新增知識</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 cursor-pointer">
            <X size={18} />
          </button>
        </div>
        <div className="p-5 space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">目標</label>
            <div className="flex gap-2">
              <button
                onClick={() => setTargetZone("domain")}
                className={`flex-1 py-2 text-sm font-medium rounded-lg border cursor-pointer transition-colors ${
                  targetZone === "domain"
                    ? "border-blue-500 bg-blue-50 dark:bg-blue-500/10 text-blue-600"
                    : "border-slate-200 dark:border-slate-700 text-slate-500"
                }`}
              >
                領域知識
              </button>
              <button
                onClick={() => setTargetZone("deals")}
                className={`flex-1 py-2 text-sm font-medium rounded-lg border cursor-pointer transition-colors ${
                  targetZone === "deals"
                    ? "border-blue-500 bg-blue-50 dark:bg-blue-500/10 text-blue-600"
                    : "border-slate-200 dark:border-slate-700 text-slate-500"
                }`}
              >
                案件知識
              </button>
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">分類</label>
            {categories.length > 0 && (
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full px-3 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-50 focus:outline-none focus:border-blue-500 mb-2"
              >
                <option value="">選擇現有分類...</option>
                {categories.map((c) => (
                  <option key={c.name} value={c.name}>{c.name} ({c.count})</option>
                ))}
              </select>
            )}
            <input
              value={newCategory}
              onChange={(e) => setNewCategory(e.target.value)}
              placeholder="或輸入新分類..."
              className="w-full px-3 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-50 focus:outline-none focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">標題 *</label>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-50 focus:outline-none focus:border-blue-500"
              placeholder="知識標題"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">標籤（逗號分隔）</label>
            <input
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              className="w-full px-3 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-50 focus:outline-none focus:border-blue-500"
              placeholder="AI, 食品製造, ..."
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">內容（Markdown）</label>
            <textarea
              value={body}
              onChange={(e) => setBody(e.target.value)}
              rows={8}
              className="w-full px-3 py-2 text-sm font-mono rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-50 focus:outline-none focus:border-blue-500 resize-none"
              placeholder="# 標題&#10;&#10;內容..."
            />
          </div>
        </div>
        <div className="flex justify-end gap-2 px-5 py-4 border-t border-slate-200 dark:border-slate-700">
          <button onClick={onClose} className="px-4 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 cursor-pointer transition-colors">
            取消
          </button>
          <button
            onClick={handleCreate}
            disabled={!title.trim() || !finalCategory || saving}
            className="px-4 py-2 text-sm font-medium rounded-lg bg-blue-500 text-white hover:bg-blue-600 cursor-pointer transition-colors disabled:opacity-50"
          >
            {saving ? <Loader2 size={14} className="animate-spin" /> : "建立"}
          </button>
        </div>
      </div>
    </div>
  );
}
