"use client";

import { useEffect, useMemo, useState } from "react";
import { usePathname } from "next/navigation";
import {
  Bell,
  LayoutDashboard,
  UserRound,
  Wifi,
  WifiOff,
  Plus,
  Camera,
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
      subtitle: "Captura, previsualiza y sube imágenes",
      icon: Camera,
    };
  }

  if (pathname === "/ia-metricas") {
    return {
      title: "Métricas de IA",
      subtitle: "Panel técnico oculto de rendimiento",
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
  const [isOnline, setIsOnline] = useState(true);

  useEffect(() => {
    setIsOnline(window.navigator.onLine);

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

  const primaryActionLabel =
    pathname === "/captura" ? "Subir imagen" : "Nuevo registro";

  return (
    <header className="glass-card sticky top-3 z-30 rounded-[28px] px-4 py-4 shadow-[0_12px_40px_rgba(0,0,0,0.06)] sm:px-5">
      <div className="flex items-center justify-between gap-4">
        <div className="flex min-w-0 items-center gap-4">
          <div className="lg:hidden">
            <LogoMark />
          </div>

          <div className="hidden min-w-0 lg:flex lg:items-center lg:gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[var(--egg)] ring-1 ring-black/5 dark:ring-white/10">
              <PageIcon className="h-5 w-5 text-[var(--primary-strong)]" />
            </div>

            <div className="min-w-0">
              <p className="text-sm font-medium text-[var(--muted)]">
                {page.subtitle}
              </p>
              <h1 className="truncate text-2xl font-semibold tracking-tight">
                {page.title}
              </h1>
            </div>
          </div>
        </div>

        <div className="hidden items-center gap-2 xl:flex">
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
        </div>

        <div className="flex items-center gap-2">
          <button className="secondary-button inline-flex h-11 w-11 items-center justify-center rounded-2xl transition duration-300 hover:-translate-y-0.5">
            <Bell className="h-4 w-4" />
          </button>

          <button className="primary-button hidden items-center gap-2 rounded-2xl px-4 py-2.5 text-sm font-semibold transition duration-300 hover:-translate-y-0.5 sm:inline-flex">
            {pathname === "/captura" ? (
              <Camera className="h-4 w-4" />
            ) : (
              <Plus className="h-4 w-4" />
            )}
            {primaryActionLabel}
          </button>

          <ThemeToggle />
        </div>
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-2 xl:hidden">
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
      </div>
    </header>
  );
}