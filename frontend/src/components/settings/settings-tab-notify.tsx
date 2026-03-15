"use client";

import { useState, useEffect } from "react";
import { Bell, Loader2 } from "lucide-react";
import { nxApi } from "@/lib/nexus-api";

interface NotificationPrefs {
  email_enabled: boolean;
  telegram_enabled: boolean;
  frequency: string;
  events: {
    deal_stage_change: boolean;
    meeting_reminder: boolean;
    document_expiry: boolean;
    intel_received: boolean;
  };
}

const EVENT_LABELS: Record<string, string> = {
  deal_stage_change: "商機階段變更",
  meeting_reminder: "會議提醒",
  document_expiry: "文件到期",
  intel_received: "新情報收到",
};

const FREQUENCY_OPTIONS = [
  { value: "realtime", label: "即時" },
  { value: "daily", label: "每日摘要" },
  { value: "weekly", label: "每週摘要" },
];

export function SettingsTabNotify() {
  const [prefs, setPrefs] = useState<NotificationPrefs>({
    email_enabled: false,
    telegram_enabled: false,
    frequency: "daily",
    events: {
      deal_stage_change: true,
      meeting_reminder: true,
      document_expiry: true,
      intel_received: false,
    },
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    loadPrefs();
  }, []);

  async function loadPrefs() {
    try {
      const data = await nxApi.settings.getNotifications();
      setPrefs(data);
    } catch {
      // use defaults
    } finally {
      setLoading(false);
    }
  }

  async function handleSave() {
    setSaving(true);
    setMessage(null);
    try {
      await nxApi.settings.updateNotifications(prefs);
      setMessage("通知偏好已儲存");
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

  return (
    <div className="space-y-6">
      <div className="border border-slate-200 dark:border-slate-700 rounded-xl p-5">
        <div className="flex items-center gap-3 mb-5">
          <div className="w-10 h-10 bg-amber-500/10 rounded-lg flex items-center justify-center">
            <Bell size={20} className="text-amber-500" />
          </div>
          <div>
            <h3 className="font-medium text-slate-900 dark:text-slate-100">通知偏好</h3>
            <p className="text-xs text-slate-500">設定通知管道和觸發事件</p>
          </div>
        </div>

        {/* Channels */}
        <div className="space-y-3 mb-6">
          <label className="text-sm font-medium text-slate-700 dark:text-slate-300">通知管道</label>
          <div className="space-y-2">
            <ToggleRow
              label="Email 通知"
              checked={prefs.email_enabled}
              onChange={(v) => setPrefs({ ...prefs, email_enabled: v })}
            />
            <ToggleRow
              label="Telegram 通知"
              checked={prefs.telegram_enabled}
              onChange={(v) => setPrefs({ ...prefs, telegram_enabled: v })}
            />
          </div>
        </div>

        {/* Frequency */}
        <div className="space-y-3 mb-6">
          <label className="text-sm font-medium text-slate-700 dark:text-slate-300">通知頻率</label>
          <div className="flex gap-2">
            {FREQUENCY_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={() => setPrefs({ ...prefs, frequency: opt.value })}
                className={`px-4 py-2 rounded-lg text-sm border transition-colors ${
                  prefs.frequency === opt.value
                    ? "border-amber-500 bg-amber-50 dark:bg-amber-900/20 text-amber-700 dark:text-amber-300"
                    : "border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:border-slate-300"
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        {/* Events */}
        <div className="space-y-3 mb-6">
          <label className="text-sm font-medium text-slate-700 dark:text-slate-300">觸發事件</label>
          <div className="space-y-2">
            {Object.entries(EVENT_LABELS).map(([key, label]) => (
              <ToggleRow
                key={key}
                label={label}
                checked={prefs.events[key as keyof typeof prefs.events] || false}
                onChange={(v) =>
                  setPrefs({
                    ...prefs,
                    events: { ...prefs.events, [key]: v },
                  })
                }
              />
            ))}
          </div>
        </div>

        <button
          onClick={handleSave}
          disabled={saving}
          className="flex items-center gap-2 px-4 py-2 text-sm text-white bg-amber-500 rounded-lg hover:bg-amber-600 disabled:opacity-50"
        >
          {saving && <Loader2 size={14} className="animate-spin" />}
          儲存偏好
        </button>

        {message && (
          <p className="mt-3 text-sm text-green-600 dark:text-green-400">{message}</p>
        )}
      </div>
    </div>
  );
}

function ToggleRow({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: (value: boolean) => void;
}) {
  return (
    <label className="flex items-center justify-between px-4 py-2.5 rounded-lg border border-slate-200 dark:border-slate-700 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800">
      <span className="text-sm text-slate-700 dark:text-slate-300">{label}</span>
      <div
        onClick={() => onChange(!checked)}
        className={`relative w-10 h-5 rounded-full transition-colors cursor-pointer ${
          checked ? "bg-amber-500" : "bg-slate-300 dark:bg-slate-600"
        }`}
      >
        <div
          className={`absolute top-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform ${
            checked ? "translate-x-5" : "translate-x-0.5"
          }`}
        />
      </div>
    </label>
  );
}
