"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { House, ClipboardList, Camera, History, Bell, UserRound, LogOut } from "lucide-react";

const links = [
  { href: "/", label: "Inicio", icon: House },
  { href: "/registro", label: "Registro", icon: ClipboardList },
  { href: "/conteo-ia", label: "Cámara IA", icon: Camera },
  { href: "/historial", label: "Historial", icon: History },
  { href: "/alertas", label: "Alertas", icon: Bell },
  { href: "/perfil", label: "Perfil", icon: UserRound },
];

export function Sidebar() {
  const pathname = usePathname();

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    document.cookie = "token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
    window.location.href = "/login";
  };

  return (
    <aside className="hidden lg:flex flex-col w-64 min-h-screen bg-[#141414] border-r border-zinc-800/50 px-4 py-6 fixed left-0 top-0">
      
      {/* Logo */}
      <div className="flex items-center gap-3 mb-10 px-2">
        <div className="w-10 h-10 bg-[#fbb100] rounded-xl flex items-center justify-center">
          <span className="text-black font-black text-sm">PIO</span>
        </div>
        <div>
          <p className="text-[10px] text-zinc-500 uppercase tracking-widest">Sistema Avícola</p>
          <p className="text-white font-black text-lg leading-none">PIO AI</p>
        </div>
      </div>

      {/* Links */}
      <nav className="flex flex-col gap-1 flex-1">
        {links.map((link) => {
          const active = pathname === link.href;
          const Icon = link.icon;

          return (
            <Link
              key={link.href}
              href={link.href}
              className={`flex items-center gap-3 px-4 py-3 rounded-2xl text-sm font-semibold transition-all ${
                active
                  ? "bg-[#fbb100] text-black"
                  : "text-zinc-400 hover:bg-zinc-800/50 hover:text-white"
              }`}
            >
              <Icon className="h-4 w-4" />
              {link.label}
            </Link>
          );
        })}
      </nav>

      {/* Logout */}
      <button
        onClick={handleLogout}
        className="flex items-center gap-3 px-4 py-3 rounded-2xl text-sm font-semibold text-zinc-400 hover:bg-red-500/10 hover:text-red-400 transition-all"
      >
        <LogOut className="h-4 w-4" />
        Cerrar sesión
      </button>
    </aside>
  );
}