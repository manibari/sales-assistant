"use client";

import { useState, useEffect, useCallback, useMemo, useRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  Loader2,
  Search,
  FolderOpen,
  Folder,
  FileText,
  LayoutGrid,
  LayoutList,
  ChevronRight,
  ArrowLeft,
  Plus,
  Trash2,
  RefreshCw,
  X,
  Brain,
  FolderPlus,
  File,
  Upload,
  MessageSquare,
  Send,
  Sparkles,
} from "lucide-react";
import {
  nxApi,
  type NxMemory,
  type NxFile,
} from "@/lib/nexus-api";

type ViewMode = "icon" | "list";

// Build folder tree from flat memory paths
interface FolderNode {
  name: string;
  path: string;
  children: Map<string, FolderNode>;
  files: NxMemory[];
}

function buildTree(memories: NxMemory[]): FolderNode {
  const root: FolderNode = { name: "知識庫", path: "", children: new Map(), files: [] };

  for (const m of memories) {
    const parts = m.path.split("/");
    const fileName = parts.pop()!;
    let current = root;

    for (const part of parts) {
      if (!current.children.has(part)) {
        const childPath = current.path ? `${current.path}/${part}` : part;
        current.children.set(part, {
          name: part,
          path: childPath,
          children: new Map(),
          files: [],
        });
      }
      current = current.children.get(part)!;
    }

    current.files.push(m);
  }

  return root;
}

function getNode(root: FolderNode, path: string): FolderNode | null {
  if (!path) return root;
  const parts = path.split("/");
  let current = root;
  for (const part of parts) {
    const child = current.children.get(part);
    if (!child) return null;
    current = child;
  }
  return current;
}

function formatSize(memory: NxMemory): string {
  const body = memory._body || memory.snippet || "";
  const bytes = new TextEncoder().encode(body).length;
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

const TYPE_LABELS: Record<string, string> = {
  "client-profile": "客戶資料",
  "deal-overview": "案件總覽",
  intel: "情報摘要",
  meeting: "會議紀錄",
  "file-summary": "文件摘要",
  "domain-insight": "領域知識",
  "deal-note": "案件筆記",
  manual: "手動筆記",
};

const TYPE_ICONS: Record<string, string> = {
  "client-profile": "👤",
  "deal-overview": "💼",
  intel: "🔍",
  meeting: "📅",
  "file-summary": "📄",
  "domain-insight": "🧠",
  "deal-note": "📝",
  manual: "✏️",
};

export default function KnowledgePage() {
  const [memories, setMemories] = useState<NxMemory[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [viewMode, setViewMode] = useState<ViewMode>("list");
  const [currentPath, setCurrentPath] = useState("");
  const [selectedFile, setSelectedFile] = useState<NxMemory | null>(null);
  const [query, setQuery] = useState("");
  const [searchResults, setSearchResults] = useState<NxMemory[] | null>(null);
  const [showNewFolder, setShowNewFolder] = useState(false);
  const [newFolderName, setNewFolderName] = useState("");
  const [creating, setCreating] = useState(false);

  // Drag & drop upload
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<string[]>([]);

  // AI ask panel
  const [showAsk, setShowAsk] = useState(false);
  const [askQuestion, setAskQuestion] = useState("");
  const [askLoading, setAskLoading] = useState(false);
  const [askAnswer, setAskAnswer] = useState<string | null>(null);
  const [askSources, setAskSources] = useState<Array<{ source_type: string; id: number; text: string; score: number }>>([]);
  const askInputRef = useRef<HTMLInputElement>(null);

  // Load all memories
  const loadMemories = useCallback(() => {
    setLoading(true);
    nxApi.memory
      .list()
      .then(setMemories)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    loadMemories();
  }, [loadMemories]);

  // Build tree
  const tree = useMemo(() => buildTree(memories), [memories]);
  const currentNode = useMemo(() => getNode(tree, currentPath), [tree, currentPath]);

  // Breadcrumb
  const breadcrumbs = useMemo(() => {
    const crumbs = [{ name: "知識庫", path: "" }];
    if (currentPath) {
      const parts = currentPath.split("/");
      let accumulated = "";
      for (const part of parts) {
        accumulated = accumulated ? `${accumulated}/${part}` : part;
        crumbs.push({ name: part, path: accumulated });
      }
    }
    return crumbs;
  }, [currentPath]);

  // Search
  const handleSearch = useCallback(async () => {
    if (!query.trim()) {
      setSearchResults(null);
      return;
    }
    try {
      const results = await nxApi.memory.search(query);
      setSearchResults(results);
    } catch (err) {
      console.error(err);
    }
  }, [query]);

  // AI ask
  const handleAsk = async () => {
    if (!askQuestion.trim() || askLoading) return;
    setAskLoading(true);
    setAskAnswer(null);
    setAskSources([]);
    try {
      const res = await fetch("/api/nx/agent/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: askQuestion }),
      });
      const data = await res.json();
      setAskAnswer(data.answer ?? "（無回答）");
      setAskSources(data.sources ?? []);
    } catch (err) {
      setAskAnswer("發生錯誤，請稍後再試。");
      console.error(err);
    } finally {
      setAskLoading(false);
    }
  };

  // Sync
  const handleSync = async () => {
    setSyncing(true);
    try {
      await nxApi.memory.syncAll();
      loadMemories();
    } catch (err) {
      console.error(err);
    } finally {
      setSyncing(false);
    }
  };

  // Delete file
  const handleDelete = async (m: NxMemory) => {
    if (!confirm(`確定要刪除「${m.title}」？`)) return;
    try {
      await nxApi.memory.delete(m.path);
      setMemories((prev) => prev.filter((x) => x.path !== m.path));
      if (selectedFile?.path === m.path) setSelectedFile(null);
    } catch (err) {
      console.error(err);
    }
  };

  // Create folder (create a placeholder file in the folder)
  const handleCreateFolder = async () => {
    if (!newFolderName.trim()) return;
    setCreating(true);
    try {
      const folder = currentPath
        ? `${currentPath}/${newFolderName.trim()}`
        : newFolderName.trim();
      await nxApi.memory.create({
        title: "README",
        type: "manual",
        scope: "long-term",
        body: `# ${newFolderName.trim()}\n\n資料夾建立於 ${new Date().toLocaleDateString("zh-TW")}`,
        folder,
      });
      setShowNewFolder(false);
      setNewFolderName("");
      loadMemories();
    } catch (err) {
      console.error(err);
    } finally {
      setCreating(false);
    }
  };

  // File upload
  const handleFiles = async (files: FileList | File[]) => {
    const fileArr = Array.from(files);
    if (fileArr.length === 0) return;
    setUploading(true);
    setUploadProgress([]);

    for (const file of fileArr) {
      setUploadProgress((prev) => [...prev, `上傳 ${file.name}...`]);
      try {
        const formData = new FormData();
        formData.append("file", file);
        formData.append("file_type", "knowledge");
        await nxApi.files.upload(formData);
        setUploadProgress((prev) => [
          ...prev.slice(0, -1),
          `✅ ${file.name} — 已上傳，排入解析佇列`,
        ]);
      } catch (err) {
        console.error(err);
        setUploadProgress((prev) => [
          ...prev.slice(0, -1),
          `❌ ${file.name} — 上傳失敗`,
        ]);
      }
    }

    setUploading(false);
    // Refresh after sync so new file-summary memories appear
    setTimeout(() => {
      nxApi.memory.syncAll().then(loadMemories).catch(console.error);
    }, 1000);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    handleFiles(e.dataTransfer.files);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    // Only set false if leaving the container, not entering a child
    if (e.currentTarget === e.target) setDragging(false);
  };

  // Navigate
  const navigateTo = (path: string) => {
    setCurrentPath(path);
    setSelectedFile(null);
    setSearchResults(null);
    setQuery("");
  };

  // Items to display
  const displayItems = searchResults || (currentNode ? currentNode.files : []);
  const folders = currentNode
    ? Array.from(currentNode.children.values()).sort((a, b) => a.name.localeCompare(b.name))
    : [];

  return (
    <div
      className="flex flex-col h-full relative"
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
    >
      {/* Drag overlay */}
      {dragging && (
        <div className="absolute inset-0 z-50 bg-purple-500/10 border-2 border-dashed border-purple-500 rounded-xl flex items-center justify-center pointer-events-none">
          <div className="text-center">
            <Upload size={48} className="text-purple-500 mx-auto mb-2" />
            <p className="text-lg font-semibold text-purple-600 dark:text-purple-400">拖放檔案到這裡</p>
            <p className="text-sm text-purple-500/70">支援 PDF、Word、PowerPoint、Excel</p>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="h-14 px-4 flex items-center justify-between border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shrink-0">
        <div className="flex items-center gap-2">
          <Brain size={20} className="text-purple-500" />
          <h1 className="text-xl font-bold text-slate-900 dark:text-slate-50">知識庫</h1>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setViewMode("icon")}
            className={`p-1.5 rounded-lg cursor-pointer transition-colors ${
              viewMode === "icon" ? "text-blue-500 bg-blue-500/10" : "text-slate-400 hover:text-slate-600"
            }`}
          >
            <LayoutGrid size={16} />
          </button>
          <button
            onClick={() => setViewMode("list")}
            className={`p-1.5 rounded-lg cursor-pointer transition-colors ${
              viewMode === "list" ? "text-blue-500 bg-blue-500/10" : "text-slate-400 hover:text-slate-600"
            }`}
          >
            <LayoutList size={16} />
          </button>
          <button
            onClick={handleSync}
            disabled={syncing}
            className="p-1.5 rounded-lg text-slate-400 hover:text-purple-500 hover:bg-purple-500/10 cursor-pointer transition-colors disabled:opacity-50"
            title="同步知識庫 (RAG)"
          >
            <RefreshCw size={16} className={syncing ? "animate-spin" : ""} />
          </button>
        </div>
      </div>

      {/* Toolbar: breadcrumb + search + new folder */}
      <div className="px-4 py-2 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/50 shrink-0">
        <div className="flex items-center gap-3 max-w-4xl mx-auto">
          {/* Breadcrumb */}
          <nav className="flex items-center gap-1 text-sm flex-1 min-w-0 overflow-hidden">
            {breadcrumbs.map((crumb, i) => (
              <span key={crumb.path} className="flex items-center gap-1 shrink-0">
                {i > 0 && <ChevronRight size={12} className="text-slate-300" />}
                <button
                  onClick={() => navigateTo(crumb.path)}
                  className={`hover:text-blue-500 cursor-pointer transition-colors truncate max-w-32 ${
                    i === breadcrumbs.length - 1
                      ? "text-slate-900 dark:text-slate-50 font-medium"
                      : "text-slate-400"
                  }`}
                >
                  {crumb.name}
                </button>
              </span>
            ))}
          </nav>

          {/* Search */}
          <div className="relative w-48">
            <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                if (!e.target.value) setSearchResults(null);
              }}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              placeholder="搜尋..."
              className="w-full pl-8 pr-3 py-1.5 text-xs bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          {/* Upload button */}
          <label
            className="p-1.5 rounded-lg text-slate-400 hover:text-purple-500 hover:bg-purple-500/10 cursor-pointer transition-colors"
            title="上傳檔案"
          >
            <Upload size={16} />
            <input
              type="file"
              multiple
              accept=".pdf,.docx,.pptx,.xlsx,.xls,.doc,.txt,.md,.csv"
              className="hidden"
              onChange={(e) => e.target.files && handleFiles(e.target.files)}
            />
          </label>

          {/* New folder */}
          <button
            onClick={() => setShowNewFolder(true)}
            className="p-1.5 rounded-lg text-slate-400 hover:text-blue-500 hover:bg-blue-500/10 cursor-pointer transition-colors"
            title="新增資料夾"
          >
            <FolderPlus size={16} />
          </button>
        </div>
      </div>

      {/* Upload progress */}
      {uploadProgress.length > 0 && (
        <div className="px-4 py-2 bg-purple-500/5 border-b border-purple-500/20 shrink-0">
          <div className="max-w-4xl mx-auto space-y-1">
            {uploadProgress.map((msg, i) => (
              <p key={i} className="text-xs text-purple-600 dark:text-purple-400">{msg}</p>
            ))}
            {uploading && (
              <div className="flex items-center gap-2 text-xs text-purple-500">
                <Loader2 size={12} className="animate-spin" />
                上傳中...
              </div>
            )}
            {!uploading && (
              <button
                onClick={() => setUploadProgress([])}
                className="text-[10px] text-slate-400 hover:text-slate-600 cursor-pointer mt-1"
              >
                關閉
              </button>
            )}
          </div>
        </div>
      )}

      {/* Main content */}
      <div className="flex-1 overflow-auto">
        <div className="max-w-4xl mx-auto px-4 py-4">
          {loading ? (
            <div className="flex items-center justify-center py-20">
              <Loader2 size={20} className="animate-spin text-purple-500" />
            </div>
          ) : searchResults ? (
            /* Search results */
            <div>
              <div className="flex items-center justify-between mb-3">
                <p className="text-xs text-slate-400">搜尋「{query}」— {searchResults.length} 筆結果</p>
                <button
                  onClick={() => { setSearchResults(null); setQuery(""); }}
                  className="text-xs text-blue-500 cursor-pointer hover:underline"
                >
                  清除搜尋
                </button>
              </div>
              {viewMode === "list" ? (
                <ListView items={searchResults} onOpen={setSelectedFile} onDelete={handleDelete} />
              ) : (
                <IconView items={searchResults} folders={[]} onOpen={setSelectedFile} onNavigate={navigateTo} />
              )}
            </div>
          ) : (
            /* Folder contents */
            <>
              {folders.length === 0 && displayItems.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-20 text-slate-400">
                  <FolderOpen size={40} className="mb-3 opacity-30" />
                  <p className="text-sm">此資料夾為空</p>
                  <p className="text-xs mt-1">點擊同步按鈕匯入資料，或新增資料夾</p>
                </div>
              ) : viewMode === "list" ? (
                <div>
                  {/* List view header */}
                  <div className="flex items-center text-[11px] text-slate-400 uppercase tracking-wide px-3 py-2 border-b border-slate-200 dark:border-slate-700">
                    <span className="flex-1">名稱</span>
                    <span className="w-20 text-right">大小</span>
                    <span className="w-24 text-center">類型</span>
                    <span className="w-28 text-right">新增日期</span>
                    <span className="w-10" />
                  </div>

                  {/* Folders */}
                  {folders.map((folder) => {
                    const totalFiles = countFiles(folder);
                    return (
                      <button
                        key={folder.path}
                        onClick={() => navigateTo(folder.path)}
                        className="w-full flex items-center px-3 py-2.5 hover:bg-slate-50 dark:hover:bg-slate-800/50 rounded-lg cursor-pointer transition-colors text-left group"
                      >
                        <div className="flex items-center gap-2.5 flex-1 min-w-0">
                          <Folder size={18} className="text-blue-400 shrink-0" />
                          <span className="text-sm text-slate-900 dark:text-slate-50 truncate">
                            {folder.name}
                          </span>
                        </div>
                        <span className="w-20 text-right text-xs text-slate-400">{totalFiles} 項目</span>
                        <span className="w-24 text-center text-xs text-slate-400">資料夾</span>
                        <span className="w-28" />
                        <span className="w-10 flex justify-end">
                          <ChevronRight size={14} className="text-slate-300" />
                        </span>
                      </button>
                    );
                  })}

                  {/* Files */}
                  <ListView items={displayItems} onOpen={setSelectedFile} onDelete={handleDelete} />
                </div>
              ) : (
                <IconView
                  items={displayItems}
                  folders={folders}
                  onOpen={setSelectedFile}
                  onNavigate={navigateTo}
                />
              )}
            </>
          )}
        </div>
      </div>

      {/* File preview panel */}
      {selectedFile && (
        <FilePreview
          file={selectedFile}
          onClose={() => setSelectedFile(null)}
          onDelete={() => handleDelete(selectedFile)}
        />
      )}

      {/* New folder dialog */}
      {showNewFolder && (
        <div className="fixed inset-0 bg-slate-950/50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-slate-900 rounded-xl p-6 w-full max-w-sm mx-4 space-y-4">
            <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-50">新增資料夾</h3>
            <input
              type="text"
              value={newFolderName}
              onChange={(e) => setNewFolderName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleCreateFolder()}
              placeholder="資料夾名稱"
              autoFocus
              className="w-full px-3 py-2 text-sm bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            <div className="flex justify-end gap-2">
              <button
                onClick={() => { setShowNewFolder(false); setNewFolderName(""); }}
                className="px-3 py-1.5 text-xs text-slate-500 cursor-pointer"
              >
                取消
              </button>
              <button
                onClick={handleCreateFolder}
                disabled={!newFolderName.trim() || creating}
                className="px-4 py-1.5 text-xs bg-blue-500 text-white rounded-lg disabled:opacity-50 cursor-pointer"
              >
                {creating ? "建立中..." : "建立"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Ask AI FAB */}
      <button
        onClick={() => { setShowAsk(true); setTimeout(() => askInputRef.current?.focus(), 50); }}
        className="fixed bottom-6 right-6 z-40 flex items-center gap-2 px-4 py-2.5 bg-purple-600 hover:bg-purple-700 text-white rounded-full shadow-lg transition-colors text-sm font-medium"
        title="問 AI"
      >
        <Sparkles size={16} />
        問 AI
      </button>

      {/* Ask AI dialog */}
      {showAsk && (
        <div className="fixed inset-0 bg-slate-950/60 flex items-end sm:items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-slate-900 rounded-2xl w-full max-w-2xl flex flex-col max-h-[80vh] shadow-2xl">
            {/* Header */}
            <div className="flex items-center justify-between px-5 py-4 border-b border-slate-200 dark:border-slate-700 shrink-0">
              <div className="flex items-center gap-2">
                <Sparkles size={18} className="text-purple-500" />
                <span className="font-semibold text-slate-900 dark:text-slate-50 text-sm">問 AI 顧問</span>
                <span className="text-[10px] text-slate-400 bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded-full">Graph Agentic</span>
              </div>
              <button
                onClick={() => { setShowAsk(false); setAskAnswer(null); setAskSources([]); setAskQuestion(""); }}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600 cursor-pointer"
              >
                <X size={16} />
              </button>
            </div>

            {/* Answer area */}
            <div className="flex-1 overflow-auto px-5 py-4 space-y-4 min-h-0">
              {!askAnswer && !askLoading && (
                <div className="text-center py-8 text-slate-400">
                  <MessageSquare size={32} className="mx-auto mb-3 opacity-30" />
                  <p className="text-sm">輸入問題，AI 會查詢圖譜後回答</p>
                  <p className="text-xs mt-1">例：「喬山目前有哪些進行中商機？」</p>
                </div>
              )}

              {askLoading && (
                <div className="flex items-center gap-3 py-6">
                  <Loader2 size={20} className="animate-spin text-purple-500 shrink-0" />
                  <div>
                    <p className="text-sm text-slate-700 dark:text-slate-300">AI 正在查詢知識圖譜...</p>
                    <p className="text-xs text-slate-400 mt-0.5">可能需要 10–30 秒</p>
                  </div>
                </div>
              )}

              {askAnswer && (
                <div className="space-y-4">
                  {/* Answer */}
                  <div className="bg-purple-50 dark:bg-purple-950/30 rounded-xl p-4">
                    <p className="text-[11px] text-purple-500 font-medium uppercase tracking-wide mb-2">AI 回答</p>
                    <div className="prose prose-sm dark:prose-invert max-w-none text-slate-800 dark:text-slate-200">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{askAnswer}</ReactMarkdown>
                    </div>
                  </div>

                  {/* Sources */}
                  {askSources.length > 0 && (
                    <div>
                      <p className="text-[11px] text-slate-400 uppercase tracking-wide mb-2">來源 ({askSources.length})</p>
                      <div className="space-y-2">
                        {askSources.map((s, i) => (
                          <div
                            key={i}
                            className="flex items-start gap-2.5 px-3 py-2.5 bg-slate-50 dark:bg-slate-800 rounded-lg"
                          >
                            <span className="text-base shrink-0">
                              {s.source_type === "intel" ? "🔍" : "📄"}
                            </span>
                            <div className="flex-1 min-w-0">
                              <p className="text-xs text-slate-700 dark:text-slate-300 line-clamp-2">{s.text}</p>
                              <div className="flex items-center gap-2 mt-1">
                                <span className="text-[10px] text-slate-400">
                                  {s.source_type === "intel" ? "情報" : "知識庫"} #{s.id}
                                </span>
                                <span className="text-[10px] text-purple-400">
                                  相似度 {(s.score * 100).toFixed(1)}%
                                </span>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Input area */}
            <div className="px-5 py-4 border-t border-slate-200 dark:border-slate-700 shrink-0">
              <div className="flex items-center gap-2 bg-slate-50 dark:bg-slate-800 rounded-xl px-3 py-2 border border-slate-200 dark:border-slate-700 focus-within:ring-1 focus-within:ring-purple-500">
                <input
                  ref={askInputRef}
                  type="text"
                  value={askQuestion}
                  onChange={(e) => setAskQuestion(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleAsk()}
                  placeholder="輸入問題... (Enter 送出)"
                  disabled={askLoading}
                  className="flex-1 bg-transparent text-sm text-slate-900 dark:text-slate-50 placeholder-slate-400 focus:outline-none disabled:opacity-50"
                />
                <button
                  onClick={handleAsk}
                  disabled={!askQuestion.trim() || askLoading}
                  className="p-1.5 rounded-lg bg-purple-600 hover:bg-purple-700 text-white disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer transition-colors shrink-0"
                >
                  <Send size={14} />
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Count total files recursively
function countFiles(node: FolderNode): number {
  let count = node.files.length;
  for (const child of node.children.values()) {
    count += countFiles(child);
  }
  return count;
}

// List view component
function ListView({
  items,
  onOpen,
  onDelete,
}: {
  items: NxMemory[];
  onOpen: (m: NxMemory) => void;
  onDelete: (m: NxMemory) => void;
}) {
  return (
    <>
      {items.map((m) => (
        <div
          key={m.path}
          onClick={() => onOpen(m)}
          className="flex items-center px-3 py-2.5 hover:bg-slate-50 dark:hover:bg-slate-800/50 rounded-lg cursor-pointer transition-colors group"
        >
          <div className="flex items-center gap-2.5 flex-1 min-w-0">
            <span className="text-base shrink-0">{TYPE_ICONS[m.type] || "📄"}</span>
            <div className="min-w-0">
              <p className="text-sm text-slate-900 dark:text-slate-50 truncate">{m.title}</p>
              {m.client && (
                <p className="text-[10px] text-slate-400 truncate">{m.client}</p>
              )}
            </div>
          </div>
          <span className="w-20 text-right text-xs text-slate-400">{formatSize(m)}</span>
          <span className="w-24 text-center text-xs text-slate-400">{TYPE_LABELS[m.type] || m.type}</span>
          <span className="w-28 text-right text-xs text-slate-400">
            {new Date(m.created).toLocaleDateString("zh-TW")}
          </span>
          <span className="w-10 flex justify-end">
            <button
              onClick={(e) => { e.stopPropagation(); onDelete(m); }}
              className="p-1 rounded opacity-0 group-hover:opacity-100 text-slate-400 hover:text-red-500 transition-all"
            >
              <Trash2 size={12} />
            </button>
          </span>
        </div>
      ))}
    </>
  );
}

// Icon view component
function IconView({
  items,
  folders,
  onOpen,
  onNavigate,
}: {
  items: NxMemory[];
  folders: FolderNode[];
  onOpen: (m: NxMemory) => void;
  onNavigate: (path: string) => void;
}) {
  return (
    <div className="grid grid-cols-4 sm:grid-cols-5 md:grid-cols-6 lg:grid-cols-8 gap-2">
      {/* Folders */}
      {folders.map((folder) => (
        <button
          key={folder.path}
          onClick={() => onNavigate(folder.path)}
          className="flex flex-col items-center gap-1.5 p-3 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer transition-colors"
        >
          <Folder size={36} className="text-blue-400" />
          <span className="text-[11px] text-slate-700 dark:text-slate-300 text-center line-clamp-2 leading-tight">
            {folder.name}
          </span>
        </button>
      ))}

      {/* Files */}
      {items.map((m) => (
        <button
          key={m.path}
          onClick={() => onOpen(m)}
          className="flex flex-col items-center gap-1.5 p-3 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer transition-colors"
        >
          <span className="text-3xl">{TYPE_ICONS[m.type] || "📄"}</span>
          <span className="text-[11px] text-slate-700 dark:text-slate-300 text-center line-clamp-2 leading-tight">
            {m.title}
          </span>
        </button>
      ))}
    </div>
  );
}

// File preview panel (slide-in from right)
function FilePreview({
  file,
  onClose,
  onDelete,
}: {
  file: NxMemory;
  onClose: () => void;
  onDelete: () => void;
}) {
  const [content, setContent] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    nxApi.memory
      .get(file.path)
      .then((full) => setContent(full._body || full.snippet || "(無內容)"))
      .catch(() => setContent(file.snippet || "(無法載入)"))
      .finally(() => setLoading(false));
  }, [file.path, file.snippet]);

  return (
    <div className="fixed inset-0 z-50 flex">
      {/* Backdrop */}
      <div className="flex-1 bg-slate-950/30" onClick={onClose} />

      {/* Panel */}
      <div className="w-full max-w-lg bg-white dark:bg-slate-900 border-l border-slate-200 dark:border-slate-800 flex flex-col shadow-xl">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-slate-200 dark:border-slate-800 shrink-0">
          <div className="flex items-center gap-2 min-w-0">
            <span className="text-lg">{TYPE_ICONS[file.type] || "📄"}</span>
            <div className="min-w-0">
              <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-50 truncate">
                {file.title}
              </h3>
              <p className="text-[10px] text-slate-400">
                {TYPE_LABELS[file.type] || file.type}
                {file.client && ` · ${file.client}`}
                {` · ${new Date(file.created).toLocaleDateString("zh-TW")}`}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-1 shrink-0">
            <button
              onClick={onDelete}
              className="p-1.5 rounded-lg text-slate-400 hover:text-red-500 hover:bg-red-500/10 cursor-pointer transition-colors"
            >
              <Trash2 size={14} />
            </button>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer transition-colors"
            >
              <X size={16} />
            </button>
          </div>
        </div>

        {/* Tags */}
        {file.tags && file.tags.length > 0 && (
          <div className="px-4 py-2 flex flex-wrap gap-1 border-b border-slate-200 dark:border-slate-800">
            {file.tags.map((tag) => (
              <span
                key={tag}
                className="text-[10px] px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-500"
              >
                {tag}
              </span>
            ))}
          </div>
        )}

        {/* Content */}
        <div className="flex-1 overflow-auto px-4 py-4">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 size={16} className="animate-spin text-purple-500" />
            </div>
          ) : (
            <div className="prose prose-sm dark:prose-invert max-w-none text-slate-700 dark:text-slate-300">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {content || ""}
              </ReactMarkdown>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
