"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { House, LogOut, UserRound } from "lucide-react";
import { clearSession } from "@/lib/session";
import { useToast } from "@/components/ui/toast-provider";

const links = [
  { href: "/", label: "Inicio", icon: House },
  { href: "/perfil", label: "Perfil", icon: UserRound },
];

export function TabBar() {
  const pathname = usePathname();
  const router = useRouter();
  const { showToast } = useToast();

  function handleLogout() {
    clearSession();

    showToast({
      type: "info",
      title: "Sesión cerrada",
      description: "Volviendo al login.",
    });

    router.replace("/login");
  }

  return (
    <nav className="fixed bottom-4 left-1/2 z-40 w-[calc(100%-24px)] max-w-md -translate-x-1/2 rounded-[26px] border border-white/20 bg-white/80 p-2 shadow-[0_18px_40px_rgba(0,0,0,0.12)] backdrop-blur-xl dark:border-white/10 dark:bg-neutral-900/80 lg:hidden">
      <div className="grid grid-cols-3 gap-2">
        {links.map((link) => {
          const active = pathname === link.href;
          const Icon = link.icon;

          return (
            <Link
              key={link.href}
              href={link.href}
              className={`inline-flex items-center justify-center gap-2 rounded-2xl px-3 py-3 text-sm font-semibold transition ${
                active
                  ? "primary-button"
                  : "text-black/65 hover:bg-black/5 dark:text-white/65 dark:hover:bg-white/5"
              }`}
            >
              <Icon className="h-4 w-4" />
              <span className="hidden sm:inline">{link.label}</span>
            </Link>
          );
        })}

        <button
          onClick={handleLogout}
          className="inline-flex items-center justify-center gap-2 rounded-2xl px-3 py-3 text-sm font-semibold text-red-600 transition hover:bg-red-500/10 dark:text-red-300"
        >
          <LogOut className="h-4 w-4" />
          <span className="hidden sm:inline">Salir</span>
        </button>
      </div>
    </nav>
  );
}