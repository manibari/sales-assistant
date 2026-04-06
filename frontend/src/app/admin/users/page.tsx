"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { UserPlus, Pencil, Check, X } from "lucide-react";
import { TopBar } from "@/components/top-bar";
import { useAuth } from "@/lib/auth-context";

interface NxUser {
  id: number;
  name: string;
  email: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

const ROLES = ["admin", "sales", "finance"];
const ROLE_LABELS: Record<string, string> = { admin: "管理員", sales: "業務", finance: "財務" };

export default function AdminUsersPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [users, setUsers] = useState<NxUser[]>([]);
  const [fetching, setFetching] = useState(true);
  const [editId, setEditId] = useState<number | null>(null);
  const [editRole, setEditRole] = useState("");
  const [editActive, setEditActive] = useState(true);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({ name: "", email: "", password: "", role: "sales" });
  const [error, setError] = useState("");

  useEffect(() => {
    if (!loading && (!user || user.role !== "admin")) {
      router.push("/home");
    }
  }, [user, loading, router]);

  const fetchUsers = useCallback(async () => {
    setFetching(true);
    const res = await fetch("/api/nx/auth/users", { credentials: "include" });
    if (res.ok) setUsers(await res.json());
    setFetching(false);
  }, []);

  useEffect(() => { if (user?.role === "admin") fetchUsers(); }, [user, fetchUsers]);

  const saveEdit = async (id: number) => {
    await fetch(`/api/nx/auth/users/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ role: editRole, is_active: editActive }),
    });
    setEditId(null);
    fetchUsers();
  };

  const createUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    const res = await fetch("/api/nx/auth/users", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(form),
    });
    if (!res.ok) {
      const d = await res.json().catch(() => ({}));
      setError(d.detail || "建立失敗");
      return;
    }
    setCreating(false);
    setForm({ name: "", email: "", password: "", role: "sales" });
    fetchUsers();
  };

  if (loading || !user) return null;

  return (
    <div className="flex flex-col h-full">
      <TopBar title="使用者管理">
        <button
          onClick={() => setCreating(true)}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition cursor-pointer"
        >
          <UserPlus size={15} />
          新增帳號
        </button>
      </TopBar>

      <div className="flex-1 overflow-auto p-6">
        {creating && (
          <form
            onSubmit={createUser}
            className="mb-6 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl p-5 space-y-4 max-w-lg"
          >
            <h2 className="text-sm font-semibold text-slate-700 dark:text-slate-300">新增帳號</h2>
            {[
              { label: "姓名", key: "name", type: "text", placeholder: "王小明" },
              { label: "Email", key: "email", type: "email", placeholder: "user@company.com" },
              { label: "密碼", key: "password", type: "password", placeholder: "••••••••" },
            ].map(({ label, key, type, placeholder }) => (
              <div key={key}>
                <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">{label}</label>
                <input
                  type={type}
                  value={form[key as keyof typeof form]}
                  onChange={(e) => setForm({ ...form, [key]: e.target.value })}
                  required
                  placeholder={placeholder}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            ))}
            <div>
              <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">角色</label>
              <select
                value={form.role}
                onChange={(e) => setForm({ ...form, role: e.target.value })}
                className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {ROLES.map((r) => <option key={r} value={r}>{ROLE_LABELS[r]}</option>)}
              </select>
            </div>
            {error && <p className="text-xs text-red-500">{error}</p>}
            <div className="flex gap-2">
              <button type="submit" className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition cursor-pointer">
                建立
              </button>
              <button type="button" onClick={() => { setCreating(false); setError(""); }} className="px-4 py-2 text-sm text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition cursor-pointer">
                取消
              </button>
            </div>
          </form>
        )}

        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 dark:border-slate-700 text-xs text-slate-500 dark:text-slate-400">
                <th className="px-4 py-3 text-left font-medium">姓名</th>
                <th className="px-4 py-3 text-left font-medium">Email</th>
                <th className="px-4 py-3 text-left font-medium">角色</th>
                <th className="px-4 py-3 text-left font-medium">狀態</th>
                <th className="px-4 py-3 text-right font-medium">操作</th>
              </tr>
            </thead>
            <tbody>
              {fetching ? (
                <tr><td colSpan={5} className="px-4 py-6 text-center text-slate-400 text-xs">載入中...</td></tr>
              ) : users.map((u) => (
                <tr key={u.id} className="border-b border-slate-100 dark:border-slate-800 last:border-0">
                  <td className="px-4 py-3 font-medium text-slate-900 dark:text-slate-100">{u.name}</td>
                  <td className="px-4 py-3 text-slate-500 dark:text-slate-400">{u.email}</td>
                  <td className="px-4 py-3">
                    {editId === u.id ? (
                      <select
                        value={editRole}
                        onChange={(e) => setEditRole(e.target.value)}
                        className="px-2 py-1 rounded border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs"
                      >
                        {ROLES.map((r) => <option key={r} value={r}>{ROLE_LABELS[r]}</option>)}
                      </select>
                    ) : (
                      <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
                        {ROLE_LABELS[u.role] ?? u.role}
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {editId === u.id ? (
                      <button
                        onClick={() => setEditActive(!editActive)}
                        className={`text-xs px-2 py-0.5 rounded-full transition cursor-pointer ${editActive ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400" : "bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400"}`}
                      >
                        {editActive ? "啟用" : "停用"}
                      </button>
                    ) : (
                      <span className={`text-xs px-2 py-0.5 rounded-full ${u.is_active ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400" : "bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400"}`}>
                        {u.is_active ? "啟用" : "停用"}
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right">
                    {editId === u.id ? (
                      <div className="flex items-center justify-end gap-1">
                        <button onClick={() => saveEdit(u.id)} className="p-1.5 rounded hover:bg-emerald-50 dark:hover:bg-emerald-900/20 text-emerald-600 cursor-pointer" title="儲存"><Check size={14} /></button>
                        <button onClick={() => setEditId(null)} className="p-1.5 rounded hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-500 cursor-pointer" title="取消"><X size={14} /></button>
                      </div>
                    ) : (
                      <button
                        onClick={() => { setEditId(u.id); setEditRole(u.role); setEditActive(u.is_active); }}
                        className="p-1.5 rounded hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-400 cursor-pointer"
                        title="編輯"
                      >
                        <Pencil size={14} />
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
