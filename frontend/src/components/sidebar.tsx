"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_SECTIONS = [
  {
    title: "戰略中心",
    items: [
      { label: "關係網絡", href: "/network" },
    ],
  },
  {
    title: "售前管理",
    items: [
      { label: "客戶列表", href: "/clients" },
      { label: "案件列表", href: "/projects" },
    ],
  },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-56 bg-gray-900 border-r border-gray-800 flex flex-col">
      <div className="p-4 border-b border-gray-800">
        <h1 className="text-lg font-bold tracking-tight">Project Nexus</h1>
        <p className="text-xs text-gray-500 mt-0.5">Strategic Console</p>
      </div>
      <nav className="flex-1 p-3 space-y-4 overflow-auto">
        {NAV_SECTIONS.map((section) => (
          <div key={section.title}>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 px-2">
              {section.title}
            </p>
            <ul className="space-y-0.5">
              {section.items.map((item) => {
                const active = pathname === item.href;
                return (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      className={`block px-2 py-1.5 rounded text-sm transition-colors ${
                        active
                          ? "bg-gray-800 text-white"
                          : "text-gray-400 hover:text-gray-200 hover:bg-gray-800/50"
                      }`}
                    >
                      {item.label}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>
    </aside>
  );
}
