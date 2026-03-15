"use client";

import { useState, useEffect } from "react";
import { Mail, Link2, Unlink, Loader2, CheckCircle2, XCircle } from "lucide-react";
import { nxApi, type NxIntegrationConfig } from "@/lib/nexus-api";

export function SettingsTabEmail() {
  const [config, setConfig] = useState<NxIntegrationConfig | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadConfig();
  }, []);

  async function loadConfig() {
    try {
      const cfg = await nxApi.settings.getIntegration("microsoft_graph");
      setConfig(cfg);
    } catch {
      setConfig(null);
    } finally {
      setLoading(false);
    }
  }

  const isConnected = config?.status === "connected";

  // Listen for OAuth completion message from popup
  useEffect(() => {
    function handleMessage(event: MessageEvent) {
      if (event.data === "oauth_complete") {
        loadConfig();
      }
    }
    window.addEventListener("message", handleMessage);
    return () => window.removeEventListener("message", handleMessage);
  }, []);

  async function handleConnect() {
    try {
      const { url } = await nxApi.outlook.getAuthUrl();
      window.open(url, "oauth_popup", "width=600,height=700");
    } catch (err) {
      console.error("Failed to get auth URL:", err);
    }
  }

  async function handleDisconnect() {
    try {
      await nxApi.outlook.disconnect();
      setConfig(null);
    } catch (err) {
      console.error("Disconnect failed:", err);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="animate-spin text-slate-400" size={24} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Microsoft Graph OAuth */}
      <div className="border border-slate-200 dark:border-slate-700 rounded-xl p-5">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-500/10 rounded-lg flex items-center justify-center">
              <Mail size={20} className="text-blue-500" />
            </div>
            <div>
              <h3 className="font-medium text-slate-900 dark:text-slate-100">Microsoft Outlook</h3>
              <p className="text-xs text-slate-500">郵件、行事曆、聯絡人同步</p>
            </div>
          </div>
          <StatusBadge status={config?.status || "disconnected"} />
        </div>

        {isConnected ? (
          <div className="space-y-3">
            <p className="text-sm text-slate-600 dark:text-slate-400">
              已連接 Microsoft 帳戶。郵件和行事曆將自動同步。
            </p>
            <button
              onClick={handleDisconnect}
              className="flex items-center gap-2 px-4 py-2 text-sm text-red-600 border border-red-200 dark:border-red-800 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20"
            >
              <Unlink size={16} />
              斷開連接
            </button>
          </div>
        ) : (
          <button
            onClick={handleConnect}
            className="flex items-center gap-2 px-4 py-2 text-sm text-white bg-blue-500 rounded-lg hover:bg-blue-600"
          >
            <Link2 size={16} />
            連接 Microsoft 帳戶
          </button>
        )}
      </div>

      {/* IMAP/SMTP fallback - Phase D */}
      <div className="border border-slate-200 dark:border-slate-700 rounded-xl p-5 opacity-60">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-10 h-10 bg-slate-100 dark:bg-slate-800 rounded-lg flex items-center justify-center">
            <Mail size={20} className="text-slate-400" />
          </div>
          <div>
            <h3 className="font-medium text-slate-900 dark:text-slate-100">IMAP / SMTP</h3>
            <p className="text-xs text-slate-500">通用郵件協定（非 Microsoft 信箱適用）</p>
          </div>
        </div>
        <p className="text-sm text-slate-400">即將推出 — Phase D 實作</p>
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  if (status === "connected") {
    return (
      <span className="flex items-center gap-1 text-xs font-medium text-green-600 bg-green-50 dark:bg-green-900/20 px-2.5 py-1 rounded-full">
        <CheckCircle2 size={12} />
        已連接
      </span>
    );
  }
  if (status === "error") {
    return (
      <span className="flex items-center gap-1 text-xs font-medium text-red-600 bg-red-50 dark:bg-red-900/20 px-2.5 py-1 rounded-full">
        <XCircle size={12} />
        錯誤
      </span>
    );
  }
  return (
    <span className="text-xs font-medium text-slate-400 bg-slate-100 dark:bg-slate-800 px-2.5 py-1 rounded-full">
      未連接
    </span>
  );
}
