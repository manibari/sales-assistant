"use client";

import { useState, useEffect, useCallback } from "react";
import { Mail, Link2, Unlink, Loader2, CheckCircle2, XCircle, RefreshCw } from "lucide-react";
import { SecretInput } from "./secret-input";
import { nxApi, type NxIntegrationConfig } from "@/lib/nexus-api";

export function SettingsTabEmail() {
  const [outlookConfig, setOutlookConfig] = useState<NxIntegrationConfig | null>(null);
  const [loading, setLoading] = useState(true);

  // IMAP/SMTP state
  const [imapHost, setImapHost] = useState("imap.gmail.com");
  const [imapPort, setImapPort] = useState("993");
  const [smtpHost, setSmtpHost] = useState("smtp.gmail.com");
  const [smtpPort, setSmtpPort] = useState("587");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [imapSsl, setImapSsl] = useState(true);
  const [smtpTls, setSmtpTls] = useState(true);
  const [imapConfigured, setImapConfigured] = useState(false);
  const [imapStatus, setImapStatus] = useState("disconnected");
  const [hasPassword, setHasPassword] = useState(false);

  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState<string | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const loadConfig = useCallback(async () => {
    try {
      const [outlookCfg, imapCfg] = await Promise.allSettled([
        nxApi.settings.getIntegration("microsoft_graph"),
        nxApi.settings.getImapSmtp(),
      ]);
      if (outlookCfg.status === "fulfilled") setOutlookConfig(outlookCfg.value);
      if (imapCfg.status === "fulfilled" && imapCfg.value.configured) {
        const c = imapCfg.value;
        setImapHost(c.imap_host);
        setImapPort(String(c.imap_port));
        setSmtpHost(c.smtp_host);
        setSmtpPort(String(c.smtp_port));
        setUsername(c.username);
        setImapSsl(c.imap_ssl);
        setSmtpTls(c.smtp_tls);
        setImapConfigured(true);
        setImapStatus(c.status);
        setHasPassword(c.has_password);
      }
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadConfig();
  }, [loadConfig]);

  // OAuth popup listener
  useEffect(() => {
    function handleMessage(event: MessageEvent) {
      if (event.data === "oauth_complete") loadConfig();
    }
    window.addEventListener("message", handleMessage);
    return () => window.removeEventListener("message", handleMessage);
  }, [loadConfig]);

  async function handleOutlookConnect() {
    try {
      const { url } = await nxApi.outlook.getAuthUrl();
      window.open(url, "oauth_popup", "width=600,height=700");
    } catch (err) {
      console.error("Failed to get auth URL:", err);
    }
  }

  async function handleOutlookDisconnect() {
    try {
      await nxApi.outlook.disconnect();
      setOutlookConfig(null);
    } catch (err) {
      console.error("Disconnect failed:", err);
    }
  }

  async function handleSaveImap() {
    if (!username || !password) {
      setMessage({ type: "error", text: "請填寫帳號和密碼" });
      return;
    }
    setSaving(true);
    setMessage(null);
    try {
      await nxApi.settings.saveImapSmtp({
        imap_host: imapHost,
        imap_port: parseInt(imapPort),
        smtp_host: smtpHost,
        smtp_port: parseInt(smtpPort),
        username,
        password,
        imap_ssl: imapSsl,
        smtp_tls: smtpTls,
      });
      setImapConfigured(true);
      setHasPassword(true);
      setPassword("");
      setMessage({ type: "success", text: "IMAP/SMTP 設定已儲存" });
    } catch (err) {
      setMessage({ type: "error", text: `儲存失敗: ${err}` });
    } finally {
      setSaving(false);
    }
  }

  async function handleTestConnection(protocol: "imap" | "smtp") {
    if (!password && !hasPassword) {
      setMessage({ type: "error", text: "請先輸入密碼" });
      return;
    }
    setTesting(protocol);
    setMessage(null);
    try {
      const host = protocol === "imap" ? imapHost : smtpHost;
      const port = parseInt(protocol === "imap" ? imapPort : smtpPort);
      const useSsl = protocol === "imap" ? imapSsl : smtpTls;

      const result = await nxApi.settings.testImapSmtp({
        protocol,
        host,
        port,
        username,
        password: password || "___USE_STORED___",
        use_ssl: useSsl,
      });

      if (result.success) {
        setImapStatus("connected");
        setMessage({ type: "success", text: `${protocol.toUpperCase()} 連線成功` });
      } else {
        setMessage({ type: "error", text: `${protocol.toUpperCase()} 連線失敗: ${result.error || "unknown"}` });
      }
    } catch (err) {
      setMessage({ type: "error", text: `測試失敗: ${err}` });
    } finally {
      setTesting(null);
    }
  }

  async function handleSync() {
    setSyncing(true);
    setMessage(null);
    try {
      const result = await nxApi.settings.fetchImapEmails();
      setMessage({ type: "success", text: `同步完成：取得 ${result.fetched} 封，新增 ${result.new} 封` });
    } catch (err) {
      setMessage({ type: "error", text: `同步失敗: ${err}` });
    } finally {
      setSyncing(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="animate-spin text-slate-400" size={24} />
      </div>
    );
  }

  const outlookConnected = outlookConfig?.status === "connected";

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
              <p className="text-xs text-slate-500">OAuth 整合（需要 Azure AD 設定）</p>
            </div>
          </div>
          <StatusBadge status={outlookConfig?.status || "disconnected"} />
        </div>

        {outlookConnected ? (
          <div className="space-y-3">
            <p className="text-sm text-slate-600 dark:text-slate-400">
              已連接 Microsoft 帳戶。
            </p>
            <button
              onClick={handleOutlookDisconnect}
              className="flex items-center gap-2 px-4 py-2 text-sm text-red-600 border border-red-200 dark:border-red-800 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20"
            >
              <Unlink size={16} />
              斷開連接
            </button>
          </div>
        ) : (
          <button
            onClick={handleOutlookConnect}
            className="flex items-center gap-2 px-4 py-2 text-sm text-white bg-blue-500 rounded-lg hover:bg-blue-600"
          >
            <Link2 size={16} />
            連接 Microsoft 帳戶
          </button>
        )}
      </div>

      {/* IMAP/SMTP */}
      <div className="border border-slate-200 dark:border-slate-700 rounded-xl p-5">
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-emerald-500/10 rounded-lg flex items-center justify-center">
              <Mail size={20} className="text-emerald-500" />
            </div>
            <div>
              <h3 className="font-medium text-slate-900 dark:text-slate-100">IMAP / SMTP</h3>
              <p className="text-xs text-slate-500">Gmail、Yahoo 等通用郵件服務</p>
            </div>
          </div>
          <StatusBadge status={imapStatus} />
        </div>

        {/* Preset buttons */}
        <div className="flex gap-2 mb-4">
          <button
            onClick={() => { setImapHost("imap.gmail.com"); setImapPort("993"); setSmtpHost("smtp.gmail.com"); setSmtpPort("587"); setImapSsl(true); setSmtpTls(true); }}
            className="px-3 py-1.5 text-xs border border-slate-200 dark:border-slate-700 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-400"
          >
            Gmail 預設
          </button>
          <button
            onClick={() => { setImapHost("outlook.office365.com"); setImapPort("993"); setSmtpHost("smtp-mail.outlook.com"); setSmtpPort("587"); setImapSsl(true); setSmtpTls(true); }}
            className="px-3 py-1.5 text-xs border border-slate-200 dark:border-slate-700 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-400"
          >
            Outlook 預設
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
          <div className="space-y-2">
            <label className="text-xs font-medium text-slate-600 dark:text-slate-400">IMAP Server</label>
            <input
              value={imapHost}
              onChange={(e) => setImapHost(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-sm text-slate-900 dark:text-slate-100"
            />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-medium text-slate-600 dark:text-slate-400">IMAP Port</label>
            <input
              value={imapPort}
              onChange={(e) => setImapPort(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-sm text-slate-900 dark:text-slate-100"
            />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-medium text-slate-600 dark:text-slate-400">SMTP Server</label>
            <input
              value={smtpHost}
              onChange={(e) => setSmtpHost(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-sm text-slate-900 dark:text-slate-100"
            />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-medium text-slate-600 dark:text-slate-400">SMTP Port</label>
            <input
              value={smtpPort}
              onChange={(e) => setSmtpPort(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-sm text-slate-900 dark:text-slate-100"
            />
          </div>
        </div>

        <div className="space-y-4 mb-4">
          <div className="space-y-2">
            <label className="text-xs font-medium text-slate-600 dark:text-slate-400">Email 帳號</label>
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="your@gmail.com"
              className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-sm text-slate-900 dark:text-slate-100 placeholder:text-slate-400"
            />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-medium text-slate-600 dark:text-slate-400">
              App Password
              {hasPassword && <span className="ml-2 text-green-600 font-normal">(已設定)</span>}
            </label>
            <SecretInput
              value={password}
              onChange={setPassword}
              placeholder={hasPassword ? "留空保留現有密碼" : "輸入 App Password"}
            />
          </div>
        </div>

        {/* SSL/TLS toggles */}
        <div className="flex gap-6 mb-5">
          <label className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400 cursor-pointer">
            <input type="checkbox" checked={imapSsl} onChange={(e) => setImapSsl(e.target.checked)} className="rounded" />
            IMAP SSL
          </label>
          <label className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400 cursor-pointer">
            <input type="checkbox" checked={smtpTls} onChange={(e) => setSmtpTls(e.target.checked)} className="rounded" />
            SMTP TLS
          </label>
        </div>

        {/* Actions */}
        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={handleSaveImap}
            disabled={saving}
            className="flex items-center gap-2 px-4 py-2 text-sm text-white bg-emerald-500 rounded-lg hover:bg-emerald-600 disabled:opacity-50"
          >
            {saving && <Loader2 size={14} className="animate-spin" />}
            儲存設定
          </button>
          <button
            onClick={() => handleTestConnection("imap")}
            disabled={!!testing}
            className="flex items-center gap-2 px-4 py-2 text-sm text-slate-700 dark:text-slate-300 border border-slate-300 dark:border-slate-600 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800 disabled:opacity-50"
          >
            {testing === "imap" && <Loader2 size={14} className="animate-spin" />}
            測試 IMAP
          </button>
          <button
            onClick={() => handleTestConnection("smtp")}
            disabled={!!testing}
            className="flex items-center gap-2 px-4 py-2 text-sm text-slate-700 dark:text-slate-300 border border-slate-300 dark:border-slate-600 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800 disabled:opacity-50"
          >
            {testing === "smtp" && <Loader2 size={14} className="animate-spin" />}
            測試 SMTP
          </button>
          {imapConfigured && (
            <button
              onClick={handleSync}
              disabled={syncing}
              className="flex items-center gap-2 px-4 py-2 text-sm text-emerald-600 border border-emerald-300 dark:border-emerald-700 rounded-lg hover:bg-emerald-50 dark:hover:bg-emerald-900/20 disabled:opacity-50"
            >
              {syncing ? <Loader2 size={14} className="animate-spin" /> : <RefreshCw size={14} />}
              同步郵件
            </button>
          )}
        </div>

        {/* Message */}
        {message && (
          <div
            className={`mt-4 flex items-center gap-2 text-sm px-4 py-3 rounded-lg ${
              message.type === "success"
                ? "bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300"
                : "bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300"
            }`}
          >
            {message.type === "success" ? <CheckCircle2 size={16} /> : <XCircle size={16} />}
            {message.text}
          </div>
        )}
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
