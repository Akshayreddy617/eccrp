"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/store/authStore";

const NAV_ITEMS = [
  { href: "/dashboard",       icon: "🏠", label: "Dashboard" },
  { href: "/elections",       icon: "🗳️", label: "Elections" },
  { href: "/candidates",      icon: "👤", label: "Candidates" },
  { href: "/eligibility",     icon: "✅", label: "Eligibility" },
  { href: "/nomination",      icon: "📄", label: "Nomination" },
  { href: "/affidavit",       icon: "📋", label: "Affidavit" },
  { href: "/compliance",      icon: "⚠️", label: "Risk Engine" },
  { href: "/expenditure",     icon: "💰", label: "Expenditure" },
  { href: "/mcc",             icon: "📢", label: "MCC Checker" },
  { href: "/timeline",        icon: "📅", label: "Timeline" },
  { href: "/knowledge",       icon: "📚", label: "Knowledge" },
  { href: "/judgments",       icon: "⚖️", label: "Judgments" },
  { href: "/ai-assistant",    icon: "🤖", label: "AI Assistant" },
  { href: "/graph",           icon: "🕸️", label: "Knowledge Graph" },
  { href: "/public",          icon: "🌐", label: "Public Portal" },
];

const ADMIN_ITEMS = [
  { href: "/admin",           icon: "⚙️", label: "Admin Panel" },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuthStore();

  const isActive = (href: string) => pathname.startsWith(href);

  return (
    <aside className="fixed inset-y-0 left-0 z-40 w-64 bg-white border-r border-gray-200 flex flex-col">
      {/* Logo */}
      <div className="px-4 py-5 border-b border-gray-100">
        <div className="flex items-center gap-2">
          <span className="text-2xl">🗳️</span>
          <div>
            <p className="text-sm font-bold text-gray-900 leading-tight">ECCRP</p>
            <p className="text-[10px] text-gray-400 leading-tight">Election Compliance Platform</p>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-0.5">
        {NAV_ITEMS.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              isActive(item.href) ? "sidebar-link-active" : "sidebar-link"
            )}
          >
            <span className="text-base">{item.icon}</span>
            <span>{item.label}</span>
          </Link>
        ))}

        {user?.role && ["super_admin", "admin"].includes(user.role) && (
          <>
            <div className="my-2 border-t border-gray-100 pt-2">
              <p className="px-3 text-[10px] uppercase tracking-wider text-gray-400 mb-1">Admin</p>
              {ADMIN_ITEMS.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(isActive(item.href) ? "sidebar-link-active" : "sidebar-link")}
                >
                  <span className="text-base">{item.icon}</span>
                  <span>{item.label}</span>
                </Link>
              ))}
            </div>
          </>
        )}
      </nav>

      {/* User */}
      <div className="border-t border-gray-100 px-3 py-3">
        <div className="flex items-center gap-2 mb-2 px-2">
          <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-700 font-semibold text-sm">
            {user?.full_name?.[0]?.toUpperCase() ?? "U"}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-medium text-gray-900 truncate">{user?.full_name}</p>
            <p className="text-[10px] text-gray-400 capitalize">{user?.role?.replace("_", " ")}</p>
          </div>
        </div>
        <button
          onClick={() => logout()}
          className="w-full sidebar-link text-red-600 hover:bg-red-50 hover:text-red-700"
        >
          <span>🚪</span>
          <span>Sign Out</span>
        </button>
      </div>
    </aside>
  );
}
