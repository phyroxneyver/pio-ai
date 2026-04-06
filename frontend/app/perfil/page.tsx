"use client";

import { useEffect, useState } from "react";
import { BadgeCheck, KeyRound, Mail, Shield, UserRound } from "lucide-react";
import { RouteGuard } from "@/components/auth/route-guard";
import { AppHeader } from "@/components/header/app-header";
import { LogoMark } from "@/components/brand/logo-mark";
import { AppShell } from "@/components/layout/app-shell";
import { Sidebar } from "@/components/layout/sidebar";
import { TabBar } from "@/components/layout/tab-bar";
import { getUser, type SessionUser } from "@/lib/session";

export default function PerfilPage() {
  const [user, setUser] = useState<SessionUser | null>(null);

  useEffect(() => {
    setUser(getUser());
  }, []);

  return (
    <RouteGuard>
      <AppShell
        header={<AppHeader />}
        sidebar={<Sidebar />}
        tabBar={<TabBar />}
      >
        <section className="mx-auto w-full max-w-3xl animate-fade-up">
          <div className="glass-card overflow-hidden rounded-[32px] p-5 shadow-[0_20px_50px_rgba(0,0,0,0.07)] sm:p-8">
            <div className="flex flex-col gap-5 sm:gap-6">
              <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div className="flex min-w-0 items-center gap-4">
                  <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-[24px] bg-[var(--egg)] ring-1 ring-black/5 dark:ring-white/10">
                    <LogoMark showText={false} />
                  </div>

                  <div className="min-w-0">
                    <p className="text-sm font-medium text-[var(--muted)]">
                      Perfil de usuario
                    </p>
                    <h2 className="truncate text-2xl font-semibold tracking-tight">
                      Información personal
                    </h2>
                  </div>
                </div>

                <button className="primary-button w-full rounded-2xl px-4 py-2.5 text-sm font-semibold transition duration-300 hover:-translate-y-0.5 sm:w-auto">
                  Editar perfil
                </button>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div className="card-interactive rounded-[24px] bg-[var(--card-strong)] p-5 ring-1 ring-black/5 dark:ring-white/10">
                  <div className="flex items-center gap-2 text-[var(--muted)]">
                    <UserRound className="h-4 w-4" />
                    <p className="text-sm">Nombre</p>
                  </div>
                  <p className="mt-2 break-words text-lg font-semibold">
                    {user?.nombre || "Sin nombre"}
                  </p>
                </div>

                <div className="card-interactive rounded-[24px] bg-[var(--card-strong)] p-5 ring-1 ring-black/5 dark:ring-white/10">
                  <div className="flex items-center gap-2 text-[var(--muted)]">
                    <BadgeCheck className="h-4 w-4" />
                    <p className="text-sm">Rol</p>
                  </div>
                  <p className="mt-2 break-words text-lg font-semibold">
                    {user?.rol || "Sin rol"}
                  </p>
                </div>

                <div className="card-interactive rounded-[24px] bg-[var(--card-strong)] p-5 ring-1 ring-black/5 dark:ring-white/10 sm:col-span-2">
                  <div className="flex items-center gap-2 text-[var(--muted)]">
                    <Mail className="h-4 w-4" />
                    <p className="text-sm">Correo</p>
                  </div>
                  <p className="mt-2 break-all text-lg font-semibold">
                    {user?.correo || "Sin correo"}
                  </p>
                </div>

                <div className="card-interactive rounded-[24px] bg-[var(--card-strong)] p-5 ring-1 ring-black/5 dark:ring-white/10">
                  <div className="flex items-center gap-2 text-[var(--muted)]">
                    <Shield className="h-4 w-4" />
                    <p className="text-sm">Estado</p>
                  </div>
                  <p className="mt-2 text-lg font-semibold text-green-600 dark:text-green-400">
                    Activo
                  </p>
                </div>

                <div className="card-interactive rounded-[24px] bg-[var(--card-strong)] p-5 ring-1 ring-black/5 dark:ring-white/10">
                  <div className="flex items-center gap-2 text-[var(--muted)]">
                    <BadgeCheck className="h-4 w-4" />
                    <p className="text-sm">Permisos</p>
                  </div>
                  <p className="mt-2 text-lg font-semibold">Acceso total</p>
                </div>
              </div>

              <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap">
                <button className="secondary-button inline-flex items-center justify-center gap-2 rounded-2xl px-4 py-2.5 text-sm font-medium transition duration-300 hover:-translate-y-0.5">
                  <KeyRound className="h-4 w-4" />
                  Cambiar contraseña
                </button>

                <button className="secondary-button rounded-2xl px-4 py-2.5 text-sm font-medium transition duration-300 hover:-translate-y-0.5">
                  Ver actividad
                </button>
              </div>
            </div>
          </div>
        </section>
      </AppShell>
    </RouteGuard>
  );
}