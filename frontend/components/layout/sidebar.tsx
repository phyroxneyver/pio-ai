"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  House,
  ClipboardList,
  Camera,
  History,
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
    <aside className="sticky top-5 hidden max-h-[calc(100vh-2.5rem)] min-h-[calc(100vh-2.5rem)] flex-col overflow-y-auto rounded-[32px] border border-black/10 bg-[var(--card)] px-4 py-6 shadow-[0_20px_50px_rgba(0,0,0,0.06)] dark:border-white/10 lg:flex">
      <div className="mb-8">
        <LogoMark />
      </div>

      <nav className="flex flex-1 flex-col gap-1">
        {links.map((link) => {
          const active = pathname === link.href;
          const Icon = link.icon;

          return (
            <Link
              key={link.href}
              href={link.href}
              className={`flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-semibold transition-all ${
                active
                  ? "bg-[var(--egg)] text-[var(--primary-strong)]"
                  : "text-[var(--muted)] hover:bg-[var(--card-strong)] hover:text-[var(--foreground)]"
              }`}
            >
              <Icon className="h-4 w-4 shrink-0" />
              <span className="truncate">{link.label}</span>
            </Link>
          );
        })}
      </nav>

      <button
        onClick={handleLogout}
        className="mt-4 flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-semibold text-[var(--muted)] transition-all hover:bg-red-500/10 hover:text-red-500"
      >
        <LogOut className="h-4 w-4 shrink-0" />
        <span className="truncate">Cerrar sesión</span>
      </button>
    </aside>
  );
}
