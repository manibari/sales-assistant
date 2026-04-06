"use client";

import { useState } from "react";
import { TopBar } from "@/components/top-bar";
import { SettingsTabEmail } from "@/components/settings/settings-tab-email";
import { SettingsTabAI } from "@/components/settings/settings-tab-ai";
import { SettingsTabTelegram } from "@/components/settings/settings-tab-telegram";
import { SettingsTabGDrive } from "@/components/settings/settings-tab-gdrive";
import { SettingsTabNotify } from "@/components/settings/settings-tab-notify";
import { SettingsTabAccount } from "@/components/settings/settings-tab-account";
import { Mail, Brain, MessageCircle, HardDrive, Bell, UserCircle } from "lucide-react";

const TABS = [
  { id: "account", label: "我的帳號", icon: UserCircle },
  { id: "email", label: "郵件 / Outlook", icon: Mail },
  { id: "ai", label: "AI 引擎", icon: Brain },
  { id: "telegram", label: "Telegram", icon: MessageCircle },
  { id: "gdrive", label: "Google Drive", icon: HardDrive },
  { id: "notify", label: "通知偏好", icon: Bell },
] as const;

type TabId = (typeof TABS)[number]["id"];

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<TabId>("account");

  return (
    <div>
      <TopBar title="設定" />

      <div className="p-4 md:p-6 max-w-4xl mx-auto">
        {/* Tab bar */}
        <div className="flex gap-1 mb-6 overflow-x-auto pb-1 border-b border-slate-200 dark:border-slate-700">
          {TABS.map((tab) => {
            const Icon = tab.icon;
            const active = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2.5 text-sm whitespace-nowrap border-b-2 transition-colors -mb-px ${
                  active
                    ? "border-blue-500 text-blue-600 dark:text-blue-400 font-medium"
                    : "border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"
                }`}
              >
                <Icon size={16} />
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Tab content */}
        {activeTab === "account" && <SettingsTabAccount />}
        {activeTab === "email" && <SettingsTabEmail />}
        {activeTab === "ai" && <SettingsTabAI />}
        {activeTab === "telegram" && <SettingsTabTelegram />}
        {activeTab === "gdrive" && <SettingsTabGDrive />}
        {activeTab === "notify" && <SettingsTabNotify />}
      </div>
    </div>
  );
}
