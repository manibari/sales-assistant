"use client";

import { usePathname } from "next/navigation";
import { DesktopSidebar } from "@/components/desktop-sidebar";
import { BottomNav } from "@/components/bottom-nav";
import { AssistantChat } from "@/components/assistant-chat";
import { AuthProvider } from "@/lib/auth-context";

const AUTH_PATHS = ["/login"];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isAuthPage = AUTH_PATHS.some((p) => pathname.startsWith(p));

  if (isAuthPage) {
    return <>{children}</>;
  }

  return (
    <AuthProvider>
      <div className="flex h-screen">
        <DesktopSidebar />
        <div className="flex-1 flex flex-col overflow-hidden">
          <main className="flex-1 overflow-auto pb-20 md:pb-0">
            {children}
          </main>
        </div>
      </div>
      <BottomNav />
      <AssistantChat />
    </AuthProvider>
  );
}
