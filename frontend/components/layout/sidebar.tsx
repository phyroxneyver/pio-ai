"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  House,
  ClipboardList,
  Camera,
  History,
  Bell,
  UserRound,
  LogOut,
} from "lucide-react";
import { LogoMark } from "@/components/brand/logo-mark";
import { clearSession } from "@/lib/session";

const links = [
  { href: "/", label: "Inicio", icon: House },
  { href: "/registro", label: "Registro", icon: ClipboardList },
  { href: "/captura", label: "Cámara IA", icon: Camera },
  { href: "/historial", label: "Historial", icon: History },
  { href: "/alertas", label: "Alertas", icon: Bell },
  { href: "/perfil", label: "Perfil", icon: UserRound },
];

export function Sidebar() {
  const pathname = usePathname();

  const handleLogout = () => {
    clearSession();
    document.cookie = "token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
    window.location.href = "/login";
  };

  return (
    <aside className="hidden lg:flex flex-col w-64 min-h-screen bg-[var(--card)] border-r border-black/10 dark:border-white/10 px-4 py-6">
      <div className="mb-8">
        <LogoMark />
      </div>

      <nav className="flex flex-col gap-1 flex-1">
        {links.map((link) => {
          const active = pathname === link.href;
          const Icon = link.icon;

          return (
            <Link
              key={link.href}
              href={link.href}
              className={`flex items-center gap-3 px-4 py-3 rounded-2xl text-sm font-semibold transition-all ${active
                  ? "bg-[var(--egg)] text-[var(--primary-strong)]"
                  : "text-[var(--muted)] hover:bg-[var(--card-strong)] hover:text-[var(--foreground)]"
                }`}
            >
              <Icon className="h-4 w-4" />
              {link.label}
            </Link>
          );
        })}
      </nav>

      <button
        onClick={handleLogout}
        className="flex items-center gap-3 px-4 py-3 rounded-2xl text-sm font-semibold text-[var(--muted)] hover:bg-red-500/10 hover:text-red-400 transition-all"
      >
        <LogOut className="h-4 w-4" />
        Cerrar sesión
      </button>
    </aside>
  );
}