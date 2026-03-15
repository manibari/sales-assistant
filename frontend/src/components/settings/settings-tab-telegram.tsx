"use client";

import { useState, useEffect } from "react";
import { MessageCircle, Loader2 } from "lucide-react";
import { SecretInput } from "./secret-input";
import { nxApi, type NxIntegrationConfig } from "@/lib/nexus-api";

export function SettingsTabTelegram() {
  const [config, setConfig] = useState<NxIntegrationConfig | null>(null);
  const [botToken, setBotToken] = useState("");
  const [webhookSecret, setWebhookSecret] = useState("");
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    loadConfig();
  }, []);

  async function loadConfig() {
    try {
      const cfg = await nxApi.settings.getIntegration("telegram");
      setConfig(cfg);
    } catch {
      setConfig(null);
    } finally {
      setLoading(false);
    }
  }

  async function handleSave() {
    setSaving(true);
    setMessage(null);
    try {
      const configJson: Record<string, string> = {};
      if (botToken) configJson.bot_token = botToken;
      if (webhookSecret) configJson.webhook_secret = webhookSecret;

      const result = await nxApi.settings.updateIntegration("telegram", {
        enabled: true,
        config_json: configJson,
      });
      setConfig(result);
      setBotToken("");
      setWebhookSecret("");
      setMessage("設定已儲存");
    } catch (err) {
      setMessage(`儲存失敗: ${err}`);
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="animate-spin text-slate-400" size={24} />
      </div>
    );
  }

  const hasToken = !!(config?.config_json && typeof config.config_json === "object" && "bot_token" in config.config_json);

  return (
    <div className="space-y-6">
      <div className="border border-slate-200 dark:border-slate-700 rounded-xl p-5">
        <div className="flex items-center gap-3 mb-5">
          <div className="w-10 h-10 bg-sky-500/10 rounded-lg flex items-center justify-center">
            <MessageCircle size={20} className="text-sky-500" />
          </div>
          <div>
            <h3 className="font-medium text-slate-900 dark:text-slate-100">Telegram Bot</h3>
            <p className="text-xs text-slate-500">語音輸入和通知推播</p>
          </div>
        </div>

        <div className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
              Bot Token
              {hasToken && (
                <span className="ml-2 text-xs text-green-600 font-normal">(已設定)</span>
              )}
            </label>
            <SecretInput
              value={botToken}
              onChange={setBotToken}
              placeholder={hasToken ? "••••••••••••••••" : "輸入 Bot Token"}
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
              Webhook Secret
            </label>
            <SecretInput
              value={webhookSecret}
              onChange={setWebhookSecret}
              placeholder="Webhook secret (optional)"
            />
          </div>

          <button
            onClick={handleSave}
            disabled={saving}
            className="flex items-center gap-2 px-4 py-2 text-sm text-white bg-sky-500 rounded-lg hover:bg-sky-600 disabled:opacity-50"
          >
            {saving && <Loader2 size={14} className="animate-spin" />}
            儲存設定
          </button>

          {message && (
            <p className="text-sm text-green-600 dark:text-green-400">{message}</p>
          )}
        </div>
      </div>
    </div>
  );
}
