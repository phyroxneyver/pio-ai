"use client";

import { useEffect, useMemo, useState } from "react";
import { Bell, Plus, Wifi, WifiOff } from "lucide-react";
import { LogoMark } from "@/components/brand/logo-mark";
import { ThemeToggle } from "@/components/theme/theme-toggle";

export function AppHeader() {
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

  const currentDate = useMemo(() => {
    return new Intl.DateTimeFormat("es-BO", {
      weekday: "long",
      day: "2-digit",
      month: "long",
      year: "numeric",
    }).format(new Date());
  }, []);

  return (
    <header className="glass-card sticky top-3 z-30 rounded-[28px] px-4 py-4 shadow-[0_12px_40px_rgba(0,0,0,0.06)] sm:px-5 animate-fade-up">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex items-center justify-between gap-4">
          <LogoMark />

          <div className="hidden md:flex items-center gap-2">
            <span className="rounded-full bg-white/75 px-3 py-1 text-xs font-medium text-black/70 ring-1 ring-black/5 dark:bg-white/5 dark:text-white/70 dark:ring-white/10">
              {currentDate}
            </span>

            <span
              className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold ring-1 ${
                isOnline
                  ? "bg-green-500/10 text-green-700 ring-green-500/15 dark:text-green-300"
                  : "bg-red-500/10 text-red-700 ring-red-500/15 dark:text-red-300"
              }`}
            >
              {isOnline ? <Wifi className="h-3.5 w-3.5" /> : <WifiOff className="h-3.5 w-3.5" />}
              {isOnline ? "Conectado" : "Sin conexión"}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button className="secondary-button inline-flex items-center gap-2 rounded-2xl px-4 py-2 text-sm font-medium transition hover:scale-[1.01] hover:shadow-sm">
            <Bell className="h-4 w-4" />
            <span className="hidden sm:inline">Notificaciones</span>
          </button>

          <button className="primary-button inline-flex items-center gap-2 rounded-2xl px-4 py-2 text-sm font-semibold transition duration-300 hover:-translate-y-0.5 animate-pulse-soft">
            <Plus className="h-4 w-4" />
            <span className="hidden sm:inline">Nuevo registro</span>
          </button>

          <ThemeToggle />
        </div>

        <div className="flex flex-wrap items-center gap-2 md:hidden">
          <span className="rounded-full bg-white/75 px-3 py-1 text-xs font-medium text-black/70 ring-1 ring-black/5 dark:bg-white/5 dark:text-white/70 dark:ring-white/10">
            {currentDate}
          </span>

          <span
            className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold ring-1 ${
              isOnline
                ? "bg-green-500/10 text-green-700 ring-green-500/15 dark:text-green-300"
                : "bg-red-500/10 text-red-700 ring-red-500/15 dark:text-red-300"
            }`}
          >
            {isOnline ? <Wifi className="h-3.5 w-3.5" /> : <WifiOff className="h-3.5 w-3.5" />}
            {isOnline ? "Conectado" : "Sin conexión"}
          </span>
        </div>
      </div>
    </header>
  );
}