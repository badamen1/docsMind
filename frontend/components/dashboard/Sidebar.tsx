"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/contexts/AuthContext";
import { subscriptionAPI } from "@/lib/api-endpoints";
import { Subscription } from "@/lib/types";
import { useEffect, useState } from "react";

const NAV_ITEMS = [
  {
    section: "PRINCIPAL",
    items: [
      { label: "Biblioteca", href: "/dashboard", icon: "📁" },
      { label: "Chats Recientes", href: "/dashboard/chats", icon: "💬" },
    ],
  },
  {
    section: "CONFIGURACIÓN",
    items: [
      { label: "Ajustes", href: "/dashboard/settings", icon: "⚙️" },
    ],
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [showUserMenu, setShowUserMenu] = useState(false);

  useEffect(() => {
    subscriptionAPI.get().then(setSubscription).catch(() => {});
  }, []);

  const storagePercent = subscription
    ? Math.min(100, Math.round((0 / (subscription.max_storage_mb || 10)) * 100))
    : 0;

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col h-full">
      {/* Logo */}
      <div className="p-4 border-b border-slate-800">
        <Link href="/dashboard" className="flex items-center gap-2">
          <div className="w-8 h-8 bg-blue-500 rounded flex items-center justify-center">
            <span className="text-white font-bold text-sm">D</span>
          </div>
          <span className="font-bold text-lg text-white">DocsMind</span>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3 space-y-6 overflow-auto">
        {NAV_ITEMS.map((section) => (
          <div key={section.section}>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider px-3 mb-2">
              {section.section}
            </p>
            <ul className="space-y-1">
              {section.items.map((item) => {
                const isActive =
                  item.href === "/dashboard"
                    ? pathname === "/dashboard"
                    : pathname.startsWith(item.href);
                return (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition ${
                        isActive
                          ? "bg-blue-600/20 text-blue-400"
                          : "text-slate-400 hover:text-white hover:bg-slate-800"
                      }`}
                    >
                      <span className="text-base">{item.icon}</span>
                      {item.label}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>

      {/* Storage & Plan */}
      {subscription && (
        <div className="m-3 p-3 bg-slate-800/50 rounded-lg border border-slate-700">
          <div className="flex justify-between text-sm mb-1">
            <span className="text-slate-400">Almacenamiento</span>
            <span className="text-blue-400 font-medium">{storagePercent}%</span>
          </div>
          <div className="w-full bg-slate-700 rounded-full h-1.5 mb-2">
            <div
              className="bg-blue-500 h-1.5 rounded-full transition-all"
              style={{ width: `${storagePercent}%` }}
            />
          </div>
          <p className="text-xs text-slate-500 mb-3">
            {subscription.max_documents || 5} documentos máx.
          </p>
          <div className="text-xs text-slate-500 mb-1">PLANES DISPONIBLES</div>
          <div className="flex justify-between text-sm">
            <span className="text-slate-300">Free</span>
            <span className="text-slate-400">$0</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-slate-300">Pro</span>
            <span className="text-slate-400">$9.99/mes</span>
          </div>
        </div>
      )}

      {/* User Profile */}
      <div className="border-t border-slate-800 p-3">
        <button
          onClick={() => setShowUserMenu(!showUserMenu)}
          className="flex items-center gap-3 w-full px-2 py-2 rounded-lg hover:bg-slate-800 transition"
        >
          <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-500 rounded-full flex items-center justify-center">
            <span className="text-white text-sm font-bold">
              {user?.username?.charAt(0).toUpperCase() || "U"}
            </span>
          </div>
          <div className="flex-1 text-left">
            <p className="text-sm font-medium text-white truncate">
              {user?.username || "Usuario"}
            </p>
            <p className="text-xs text-slate-500">
              Plan {subscription?.plan || "Free"}
            </p>
          </div>
          <span className="text-slate-500 text-xs">▼</span>
        </button>

        {showUserMenu && (
          <div className="mt-1 bg-slate-800 rounded-lg border border-slate-700 overflow-hidden">
            <button
              onClick={logout}
              className="w-full text-left px-4 py-2 text-sm text-red-400 hover:bg-slate-700 transition"
            >
              Cerrar Sesión
            </button>
          </div>
        )}
      </div>
    </aside>
  );
}
