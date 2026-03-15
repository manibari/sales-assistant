"use client";

import { useState, useEffect } from "react";
import { Brain, CheckCircle2, XCircle, Loader2 } from "lucide-react";
import { SecretInput } from "./secret-input";
import { nxApi } from "@/lib/nexus-api";

const AI_PROVIDERS = [
  { value: "gemini", label: "Google Gemini", envKey: "GOOGLE_API_KEY" },
  { value: "anthropic", label: "Anthropic Claude", envKey: "ANTHROPIC_API_KEY" },
  { value: "azure_openai", label: "Azure OpenAI", envKey: "AZURE_OPENAI_KEY" },
] as const;

export function SettingsTabAI() {
  const [provider, setProvider] = useState("gemini");
  const [apiKey, setApiKey] = useState("");
  const [hasKey, setHasKey] = useState(false);
  const [status, setStatus] = useState<string>("unknown");
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSettings();
  }, []);

  async function loadSettings() {
    try {
      const settings = await nxApi.settings.getAI();
      setProvider(settings.provider || "gemini");
      setHasKey(settings.has_api_key || false);
      setStatus(settings.status || "unknown");
    } catch {
      // fallback to defaults
    } finally {
      setLoading(false);
    }
  }

  async function handleSave() {
    setSaving(true);
    setTestResult(null);
    try {
      await nxApi.settings.updateAI({ provider, api_key: apiKey || undefined });
      setHasKey(apiKey ? true : hasKey);
      setApiKey("");
      setTestResult({ success: true, message: "設定已儲存" });
    } catch (err) {
      setTestResult({ success: false, message: `儲存失敗: ${err}` });
    } finally {
      setSaving(false);
    }
  }

  async function handleTest() {
    setTesting(true);
    setTestResult(null);
    try {
      const result = await nxApi.settings.testAI({ provider });
      setTestResult({
        success: result.success,
        message: result.success
          ? `連線成功 — ${result.response || ""}`
          : `連線失敗: ${result.error || "unknown error"}`,
      });
    } catch (err) {
      setTestResult({ success: false, message: `測試失敗: ${err}` });
    } finally {
      setTesting(false);
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
      <div className="border border-slate-200 dark:border-slate-700 rounded-xl p-5">
        <div className="flex items-center gap-3 mb-5">
          <div className="w-10 h-10 bg-purple-500/10 rounded-lg flex items-center justify-center">
            <Brain size={20} className="text-purple-500" />
          </div>
          <div>
            <h3 className="font-medium text-slate-900 dark:text-slate-100">AI 引擎設定</h3>
            <p className="text-xs text-slate-500">選擇 AI Provider 和 API Key</p>
          </div>
        </div>

        {/* Provider selection */}
        <div className="space-y-3 mb-5">
          <label className="text-sm font-medium text-slate-700 dark:text-slate-300">Provider</label>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {AI_PROVIDERS.map((p) => (
              <button
                key={p.value}
                onClick={() => setProvider(p.value)}
                className={`px-4 py-3 rounded-lg border text-sm text-left transition-colors ${
                  provider === p.value
                    ? "border-purple-500 bg-purple-50 dark:bg-purple-900/20 text-purple-700 dark:text-purple-300"
                    : "border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:border-slate-300"
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>

        {/* API Key input */}
        <div className="space-y-2 mb-5">
          <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
            API Key
            {hasKey && (
              <span className="ml-2 text-xs text-green-600 font-normal">
                (已設定 — 留空保留現有 key)
              </span>
            )}
          </label>
          <SecretInput
            value={apiKey}
            onChange={setApiKey}
            placeholder={hasKey ? "••••••••••••••••" : "輸入 API Key"}
          />
        </div>

        {/* Actions */}
        <div className="flex items-center gap-3">
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex items-center gap-2 px-4 py-2 text-sm text-white bg-purple-500 rounded-lg hover:bg-purple-600 disabled:opacity-50"
          >
            {saving && <Loader2 size={14} className="animate-spin" />}
            儲存設定
          </button>
          <button
            onClick={handleTest}
            disabled={testing}
            className="flex items-center gap-2 px-4 py-2 text-sm text-slate-700 dark:text-slate-300 border border-slate-300 dark:border-slate-600 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800 disabled:opacity-50"
          >
            {testing && <Loader2 size={14} className="animate-spin" />}
            測試連線
          </button>
        </div>

        {/* Test result */}
        {testResult && (
          <div
            className={`mt-4 flex items-center gap-2 text-sm px-4 py-3 rounded-lg ${
              testResult.success
                ? "bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300"
                : "bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300"
            }`}
          >
            {testResult.success ? <CheckCircle2 size={16} /> : <XCircle size={16} />}
            {testResult.message}
          </div>
        )}
      </div>
    </div>
  );
}
