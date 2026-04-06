"use client";

import { useState } from "react";
import { Check, Loader2 } from "lucide-react";
import { useAuth } from "@/lib/auth-context";

export function SettingsTabAccount() {
  const { user, refresh } = useAuth();

  const [name, setName] = useState(user?.name ?? "");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [savingName, setSavingName] = useState(false);
  const [savingPw, setSavingPw] = useState(false);
  const [nameMsg, setNameMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [pwMsg, setPwMsg] = useState<{ ok: boolean; text: string } | null>(null);

  const handleSaveName = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    setSavingName(true);
    setNameMsg(null);
    try {
      const res = await fetch("/api/nx/auth/me", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ name: name.trim() }),
      });
      if (res.ok) {
        await refresh();
        setNameMsg({ ok: true, text: "姓名已更新" });
      } else {
        const d = await res.json().catch(() => ({}));
        setNameMsg({ ok: false, text: d.detail || "更新失敗" });
      }
    } catch {
      setNameMsg({ ok: false, text: "網路錯誤" });
    } finally {
      setSavingName(false);
    }
  };

  const handleSavePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPwMsg(null);
    if (newPassword.length < 6) {
      setPwMsg({ ok: false, text: "密碼至少需要 6 個字元" });
      return;
    }
    if (newPassword !== confirmPassword) {
      setPwMsg({ ok: false, text: "兩次密碼不一致" });
      return;
    }
    setSavingPw(true);
    try {
      const res = await fetch("/api/nx/auth/me", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ password: newPassword }),
      });
      if (res.ok) {
        setCurrentPassword("");
        setNewPassword("");
        setConfirmPassword("");
        setPwMsg({ ok: true, text: "密碼已更新" });
      } else {
        const d = await res.json().catch(() => ({}));
        setPwMsg({ ok: false, text: d.detail || "更新失敗" });
      }
    } catch {
      setPwMsg({ ok: false, text: "網路錯誤" });
    } finally {
      setSavingPw(false);
    }
  };

  const inputCls =
    "w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm text-slate-900 dark:text-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-500 transition";

  return (
    <div className="space-y-8 max-w-md">
      {/* Display name */}
      <section>
        <h2 className="text-sm font-semibold text-slate-800 dark:text-slate-200 mb-4">顯示名稱</h2>
        <form onSubmit={handleSaveName} className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">姓名</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              className={inputCls}
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">Email</label>
            <input
              type="text"
              value={user?.email ?? ""}
              disabled
              className={`${inputCls} opacity-50 cursor-not-allowed`}
            />
            <p className="text-xs text-slate-400 mt-1">Email 無法自行修改，請聯絡管理員</p>
          </div>
          {nameMsg && (
            <p className={`text-xs flex items-center gap-1 ${nameMsg.ok ? "text-emerald-600" : "text-red-500"}`}>
              {nameMsg.ok && <Check size={12} />}
              {nameMsg.text}
            </p>
          )}
          <button
            type="submit"
            disabled={savingName || name.trim() === user?.name}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium rounded-lg transition cursor-pointer"
          >
            {savingName ? <Loader2 size={14} className="animate-spin" /> : "儲存名稱"}
          </button>
        </form>
      </section>

      {/* Change password */}
      <section>
        <h2 className="text-sm font-semibold text-slate-800 dark:text-slate-200 mb-4">變更密碼</h2>
        <form onSubmit={handleSavePassword} className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">新密碼</label>
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
              placeholder="至少 6 個字元"
              className={inputCls}
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">確認新密碼</label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              placeholder="再輸入一次"
              className={inputCls}
            />
          </div>
          {pwMsg && (
            <p className={`text-xs flex items-center gap-1 ${pwMsg.ok ? "text-emerald-600" : "text-red-500"}`}>
              {pwMsg.ok && <Check size={12} />}
              {pwMsg.text}
            </p>
          )}
          <button
            type="submit"
            disabled={savingPw || !newPassword || !confirmPassword}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium rounded-lg transition cursor-pointer"
          >
            {savingPw ? <Loader2 size={14} className="animate-spin" /> : "更新密碼"}
          </button>
        </form>
      </section>

      {/* Role info (read-only) */}
      <section>
        <h2 className="text-sm font-semibold text-slate-800 dark:text-slate-200 mb-2">角色權限</h2>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          目前角色：
          <span className="ml-1 px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 text-xs font-medium">
            {user?.role === "admin" ? "管理員" : user?.role === "manager" ? "管理者" : "使用者"}
          </span>
        </p>
        <p className="text-xs text-slate-400 mt-1">角色變更請聯絡管理員</p>
      </section>
    </div>
  );
}
