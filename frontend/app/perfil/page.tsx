"use client";

import { useState } from "react";
import {
    BadgeCheck,
    KeyRound,
    Mail,
    Shield,
    UserRound,
    UserCog,
} from "lucide-react";
import { RouteGuard } from "@/components/auth/route-guard";
import { AppHeader } from "@/components/header/app-header";
import { AppShell } from "@/components/layout/app-shell";
import { PageContainer } from "@/components/layout/page-container";
import { Sidebar } from "@/components/layout/sidebar";
import { TabBar } from "@/components/layout/tab-bar";
import { getUser, type SessionUser } from "@/lib/session";
import { MOCK_USER } from "@/lib/mock-user";

export default function PerfilPage() {
    const [user] = useState<SessionUser>(() => getUser() ?? MOCK_USER);

    return (
        <RouteGuard>
            <AppShell
                header={<AppHeader />}
                sidebar={<Sidebar />}
                tabBar={<TabBar />}
            >
                <PageContainer>
                    <section className="grid gap-5 2xl:grid-cols-[1.1fr_0.9fr]">
                        <div className="glass-card rounded-[32px] p-6 shadow-[0_20px_50px_rgba(0,0,0,0.07)] sm:p-8">
                            <div className="flex items-center gap-4">
                                <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-[24px] bg-[var(--egg)] ring-1 ring-black/5 dark:ring-white/10">
                                    <UserCog className="h-7 w-7 text-[var(--primary-strong)]" />
                                </div>

                                <div className="min-w-0">
                                    <p className="text-sm font-medium text-[var(--muted)]">
                                        Cuenta de usuario
                                    </p>
                                    <h2 className="truncate text-2xl font-semibold tracking-tight">
                                        Perfil personal
                                    </h2>
                                </div>
                            </div>

                            <div className="mt-8 grid gap-4 sm:grid-cols-2">
                                <div className="card-interactive rounded-[24px] bg-[var(--card-strong)] p-5 ring-1 ring-black/5 dark:ring-white/10">
                                    <div className="flex items-center gap-2 text-[var(--muted)]">
                                        <UserRound className="h-4 w-4" />
                                        <p className="text-sm">Nombre</p>
                                    </div>
                                    <p className="mt-2 break-words text-lg font-semibold">
                                        {user.nombre}
                                    </p>
                                </div>

                                <div className="card-interactive rounded-[24px] bg-[var(--card-strong)] p-5 ring-1 ring-black/5 dark:ring-white/10">
                                    <div className="flex items-center gap-2 text-[var(--muted)]">
                                        <BadgeCheck className="h-4 w-4" />
                                        <p className="text-sm">Rol</p>
                                    </div>
                                    <p className="mt-2 break-words text-lg font-semibold">
                                        {user.rol}
                                    </p>
                                </div>

                                <div className="card-interactive rounded-[24px] bg-[var(--card-strong)] p-5 ring-1 ring-black/5 dark:ring-white/10 sm:col-span-2">
                                    <div className="flex items-center gap-2 text-[var(--muted)]">
                                        <Mail className="h-4 w-4" />
                                        <p className="text-sm">Correo</p>
                                    </div>
                                    <p className="mt-2 break-all text-lg font-semibold">
                                        {user.correo || "Sin correo"}
                                    </p>
                                </div>
                            </div>

                            <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:flex-wrap">
                                <button className="primary-button w-full rounded-2xl px-4 py-2.5 text-sm font-semibold transition duration-300 hover:-translate-y-0.5 sm:w-auto">
                                    Editar perfil
                                </button>

                                <button className="secondary-button inline-flex w-full items-center justify-center gap-2 rounded-2xl px-4 py-2.5 text-sm font-medium transition duration-300 hover:-translate-y-0.5 sm:w-auto">
                                    <KeyRound className="h-4 w-4" />
                                    Cambiar contraseña
                                </button>
                            </div>
                        </div>

                        <div className="space-y-5">
                            <div className="glass-card rounded-[32px] p-6 shadow-[0_20px_50px_rgba(0,0,0,0.07)]">
                                <p className="text-sm font-medium text-[var(--muted)]">
                                    Estado de cuenta
                                </p>
                                <h3 className="mt-1 text-2xl font-semibold tracking-tight">
                                    Activa
                                </h3>

                                <div className="mt-6 rounded-[24px] bg-[var(--card-strong)] p-5 ring-1 ring-black/5 dark:ring-white/10">
                                    <div className="flex items-center gap-2 text-[var(--muted)]">
                                        <Shield className="h-4 w-4" />
                                        <p className="text-sm">Permisos del sistema</p>
                                    </div>
                                    <p className="mt-3 text-lg font-semibold">
                                        Acceso administrativo
                                    </p>
                                </div>
                            </div>

                            <div className="glass-card rounded-[32px] p-6 shadow-[0_20px_50px_rgba(0,0,0,0.07)]">
                                <p className="text-sm font-medium text-[var(--muted)]">
                                    Actividad reciente
                                </p>
                                <h3 className="mt-1 text-2xl font-semibold tracking-tight">
                                    Últimas acciones
                                </h3>

                                <div className="mt-6 space-y-3">
                                    <div className="rounded-2xl bg-[var(--card-strong)] px-4 py-4 ring-1 ring-black/5 dark:ring-white/10">
                                        <p className="text-sm font-medium">Inicio de sesión local</p>
                                        <p className="mt-1 text-xs text-[var(--muted)]">
                                            Acceso mediante cuenta demo
                                        </p>
                                    </div>

                                    <div className="rounded-2xl bg-[var(--card-strong)] px-4 py-4 ring-1 ring-black/5 dark:ring-white/10">
                                        <p className="text-sm font-medium">Consulta de perfil</p>
                                        <p className="mt-1 text-xs text-[var(--muted)]">
                                            Visualización de datos del usuario
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </section>
                </PageContainer>
            </AppShell>
        </RouteGuard>
    );
}