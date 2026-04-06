"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { House, LogOut, UserRound } from "lucide-react";
import { LogoMark } from "@/components/brand/logo-mark";
import { clearSession } from "@/lib/session";
import { useToast } from "@/components/ui/toast-provider";

const links = [
  { href: "/", label: "Inicio", icon: House },
  { href: "/perfil", label: "Perfil", icon: UserRound },
];

export function Sidebar() {
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
    <aside className="glass-card sticky top-24 rounded-[28px] p-4 shadow-[0_18px_40px_rgba(0,0,0,0.06)]">
      <LogoMark />

      <div className="mt-6 space-y-2">
        {links.map((link) => {
          const active = pathname === link.href;
          const Icon = link.icon;

          return (
            <Link
              key={link.href}
              href={link.href}
              className={`flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-semibold transition duration-300 ${
                active
                  ? "primary-button"
                  : "secondary-button hover:-translate-y-0.5"
              }`}
            >
              <Icon className="h-4 w-4" />
              {link.label}
            </Link>
          );
        })}
      </div>

      <button
        onClick={handleLogout}
        className="secondary-button mt-6 flex w-full items-center justify-center gap-2 rounded-2xl px-4 py-3 text-sm font-semibold transition duration-300 hover:-translate-y-0.5"
      >
        <LogOut className="h-4 w-4" />
        Cerrar sesión
      </button>
    </aside>
  );
}