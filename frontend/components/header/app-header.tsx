"use client";

import { useEffect, useMemo, useState } from "react";
import { usePathname } from "next/navigation";
import {
  Camera,
  ClipboardList,
  History,
  LayoutDashboard,
  UserRound,
  Wifi,
  WifiOff,
} from "lucide-react";
import { LogoMark } from "@/components/brand/logo-mark";
import { ThemeToggle } from "@/components/theme/theme-toggle";
import { formatLongDate } from "@/lib/format-date";

function getPageMeta(pathname: string) {
  if (pathname === "/perfil") {
    return {
      title: "Perfil de usuario",
      subtitle: "Información de cuenta y permisos",
      icon: UserRound,
    };
  }

  if (pathname === "/captura") {
    return {
      title: "Cámara IA",
      subtitle: "Detecta pollos, gallinas y huevos en una sola imagen",
      icon: Camera,
    };
  }

  if (pathname === "/registro") {
    return {
      title: "Registro avícola",
      subtitle: "Gestión de aves y producción",
      icon: ClipboardList,
    };
  }

  if (pathname === "/historial") {
    return {
      title: "Historial",
      subtitle: "Capturas y registros anteriores",
      icon: History,
    };
  }

  if (pathname === "/ia-metricas") {
    return {
      title: "Métricas de IA",
      subtitle: "Panel técnico de rendimiento",
      icon: LayoutDashboard,
    };
  }

  return {
    title: "Dashboard",
    subtitle: "Resumen general del sistema avícola",
    icon: LayoutDashboard,
  };
}

export function AppHeader() {
  const pathname = usePathname();
  const [isOnline, setIsOnline] = useState(() =>
    typeof navigator === "undefined" ? true : navigator.onLine,
  );

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);

    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, []);

  const currentDate = useMemo(() => formatLongDate(), []);
  const page = getPageMeta(pathname || "/");
  const PageIcon = page.icon;

  return (
    <header className="glass-card sticky top-3 z-30 rounded-[24px] px-3 py-3 shadow-[0_12px_40px_rgba(0,0,0,0.06)] sm:rounded-[28px] sm:px-5 sm:py-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex min-w-0 items-center gap-3 sm:gap-4">
          <div className="lg:hidden">
            <LogoMark />
          </div>

          <div className="hidden h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-[var(--egg)] ring-1 ring-black/5 dark:ring-white/10 sm:flex lg:h-12 lg:w-12">
            <PageIcon className="h-5 w-5 text-[var(--primary-strong)]" />
          </div>

          <div className="min-w-0">
            <p className="truncate text-xs font-medium text-[var(--muted)] sm:text-sm">
              {page.subtitle}
            </p>
            <h1 className="truncate text-xl font-semibold tracking-tight sm:text-2xl">
              {page.title}
            </h1>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2 sm:justify-end">
          <span className="rounded-full bg-white/70 px-3 py-1.5 text-xs font-medium text-[var(--muted)] ring-1 ring-black/5 dark:bg-white/5 dark:ring-white/10">
            {currentDate}
          </span>

          <span
            className={`inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-xs font-semibold ring-1 ${
              isOnline
                ? "bg-green-500/10 text-green-700 ring-green-500/15 dark:text-green-300"
                : "bg-red-500/10 text-red-700 ring-red-500/15 dark:text-red-300"
            }`}
          >
            {isOnline ? (
              <Wifi className="h-3.5 w-3.5" />
            ) : (
              <WifiOff className="h-3.5 w-3.5" />
            )}
            {isOnline ? "Conectado" : "Sin conexión"}
          </span>

          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
