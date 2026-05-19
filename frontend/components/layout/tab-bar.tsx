"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Camera, ClipboardList, History, House, UserRound } from "lucide-react";

const links = [
  { href: "/", label: "Inicio", icon: House },
  { href: "/registro", label: "Registro", icon: ClipboardList },
  { href: "/captura", label: "Cámara", icon: Camera },
  { href: "/historial", label: "Historial", icon: History },
  { href: "/perfil", label: "Perfil", icon: UserRound },
];

export function TabBar() {
  const pathname = usePathname();

  return (
    <nav className="fixed bottom-3 left-1/2 z-40 w-[calc(100%-16px)] max-w-xl -translate-x-1/2 rounded-[24px] border border-white/20 bg-white/85 p-1.5 shadow-[0_18px_40px_rgba(0,0,0,0.12)] backdrop-blur-xl dark:border-white/10 dark:bg-neutral-900/85 sm:bottom-4 sm:w-[calc(100%-24px)] sm:rounded-[26px] sm:p-2 lg:hidden">
      <div className="grid grid-cols-5 gap-1 sm:gap-2">
        {links.map((link) => {
          const active = pathname === link.href;
          const Icon = link.icon;

          return (
            <Link
              key={link.href}
              href={link.href}
              className={`inline-flex min-h-[46px] min-w-0 flex-col items-center justify-center gap-1 rounded-2xl px-1.5 py-2 text-center text-[11px] font-semibold transition sm:min-h-[50px] sm:px-2 sm:text-xs ${
                active
                  ? "primary-button"
                  : "text-black/65 hover:bg-black/5 dark:text-white/65 dark:hover:bg-white/5"
              }`}
            >
              <Icon className="h-4 w-4 shrink-0" />
              <span className="max-w-full truncate">{link.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
