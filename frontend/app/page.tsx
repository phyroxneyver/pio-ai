"use client";

import Link from "next/link";
import {
  Activity,
  Camera,
  ChartColumn,
  ClipboardList,
  Egg,
  History,
  Plus,
  ShieldCheck,
  Thermometer,
  User,
  Warehouse,
} from "lucide-react";
import { useEffect, useState } from "react";
import { fetchWithAuth } from "@/lib/api";
import { RouteGuard } from "@/components/auth/route-guard";
import { AppHeader } from "@/components/header/app-header";
import { AppShell } from "@/components/layout/app-shell";
import { PageContainer } from "@/components/layout/page-container";
import { Sidebar } from "@/components/layout/sidebar";
import { TabBar } from "@/components/layout/tab-bar";

type Ave = { id: number; tipo: string; cantidad: number; fecha_ingreso: string };

export default function HomePage() {
  const [totalAves, setTotalAves] = useState("...");
  const [totalHuevos, setTotalHuevos] = useState("...");
  const [ultimoRegistro, setUltimoRegistro] = useState<Ave | null>(null);

  useEffect(() => {
    fetchWithAuth("/aves")
      .then((r) => r.json())
      .then((data) => {
        if (Array.isArray(data)) {
          const total = data.reduce(
            (sum: number, ave: { cantidad: number }) => sum + Number(ave.cantidad || 0),
            0,
          );
          setTotalAves(total.toLocaleString("es-BO"));

          const ultimo = data[data.length - 1];
          if (ultimo) setUltimoRegistro(ultimo);
        }
      })
      .catch(() => setTotalAves("N/A"));

    fetchWithAuth("/produccion-huevos")
      .then((r) => r.json())
      .then((data) => {
        if (Array.isArray(data)) {
          const total = data.reduce(
            (sum: number, item: { cantidad_huevos: number }) =>
              sum + Number(item.cantidad_huevos || 0),
            0,
          );
          setTotalHuevos(total.toLocaleString("es-BO"));
        }
      })
      .catch(() => setTotalHuevos("N/A"));
  }, []);

  const stats = [
    {
      title: "Aves registradas",
      value: totalAves,
      note: "Pollitos y gallinas",
      icon: Egg,
    },
    {
      title: "Huevos producidos",
      value: totalHuevos,
      note: "Total registrado",
      icon: Egg,
    },
    {
      title: "Galpones activos",
      value: "08",
      note: "Control operativo",
      icon: Warehouse,
    },
    {
      title: "Último conteo",
      value: ultimoRegistro ? ultimoRegistro.cantidad.toLocaleString("es-BO") : "--",
      note: ultimoRegistro ? ultimoRegistro.tipo : "Sin registros",
      icon: ClipboardList,
    },
  ];

  return (
    <RouteGuard>
      <AppShell header={<AppHeader />} sidebar={<Sidebar />} tabBar={<TabBar />}>
        <PageContainer>
          <section className="grid gap-5 2xl:grid-cols-[1.4fr_0.95fr]">
            <div className="min-w-0 space-y-5">
              <div className="glass-card rounded-[28px] p-5 shadow-[0_20px_50px_rgba(0,0,0,0.07)] sm:rounded-[32px] sm:p-8">
                <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
                  <div className="max-w-2xl min-w-0">
                    <span className="inline-flex max-w-full items-center gap-2 rounded-full bg-[var(--egg)] px-3 py-1 text-xs font-semibold text-[var(--primary-strong)] dark:bg-white/5">
                      <ChartColumn className="h-3.5 w-3.5 shrink-0" />
                      <span className="truncate">Vista general del sistema</span>
                    </span>
                    <h2 className="mt-4 text-2xl font-semibold leading-tight tracking-tight sm:text-4xl">
                      Panel administrativo del sistema avícola
                    </h2>
                    <p className="mt-4 text-sm leading-7 text-[var(--muted)] sm:text-base">
                      Supervisa registros, producción y capturas con IA desde una interfaz más limpia,
                      sin módulos desconectados del flujo real.
                    </p>
                  </div>

                  <div className="grid gap-3 sm:flex sm:flex-wrap lg:justify-end">
                    <Link
                      href="/captura"
                      className="primary-button rounded-2xl px-4 py-3 text-center text-sm font-semibold transition duration-300 hover:-translate-y-0.5"
                    >
                      Escanear con IA
                    </Link>
                    <Link
                      href="/historial"
                      className="secondary-button rounded-2xl px-4 py-3 text-center text-sm font-medium transition duration-300 hover:-translate-y-0.5"
                    >
                      Ver historial
                    </Link>
                  </div>
                </div>
              </div>

              <div className="grid gap-4 sm:grid-cols-2 2xl:grid-cols-4">
                {stats.map((item) => {
                  const Icon = item.icon;
                  return (
                    <div
                      key={item.title}
                      className="glass-card card-interactive min-w-0 rounded-[28px] p-5 shadow-[0_10px_30px_rgba(0,0,0,0.05)]"
                    >
                      <div className="flex items-center justify-between gap-3">
                        <p className="min-w-0 text-sm font-medium text-[var(--muted)]">
                          {item.title}
                        </p>
                        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-[var(--egg)] ring-1 ring-black/5 dark:ring-white/10">
                          <Icon className="h-5 w-5 text-[var(--primary-strong)]" />
                        </div>
                      </div>
                      <p className="mt-5 truncate text-3xl font-semibold tracking-tight">
                        {item.value}
                      </p>
                      <p className="mt-2 truncate text-sm capitalize text-[var(--muted)]">
                        {item.note}
                      </p>
                    </div>
                  );
                })}
              </div>

              {ultimoRegistro ? (
                <div className="glass-card rounded-[28px] p-5 shadow-[0_20px_50px_rgba(0,0,0,0.07)] sm:rounded-[32px] sm:p-6">
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <p className="text-sm font-medium text-[var(--muted)]">Último registro</p>
                      <h3 className="mt-1 text-2xl font-semibold tracking-tight">
                        Registro reciente
                      </h3>
                    </div>
                    <Link
                      href="/historial"
                      className="secondary-button rounded-2xl px-4 py-2.5 text-center text-sm font-medium"
                    >
                      Ver detalle
                    </Link>
                  </div>

                  <div className="mt-4 flex flex-col gap-3 rounded-2xl bg-[var(--card-strong)] px-4 py-4 sm:flex-row sm:items-center sm:justify-between">
                    <div className="min-w-0">
                      <p className="text-sm font-semibold capitalize">{ultimoRegistro.tipo}</p>
                      <p className="text-xs text-[var(--muted)]">
                        {new Date(ultimoRegistro.fecha_ingreso).toLocaleDateString("es-BO")}
                      </p>
                    </div>
                    <span className="text-3xl font-black">{ultimoRegistro.cantidad}</span>
                  </div>
                </div>
              ) : null}

              <div className="glass-card rounded-[28px] p-5 shadow-[0_20px_50px_rgba(0,0,0,0.07)] sm:rounded-[32px] sm:p-6">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p className="text-sm font-medium text-[var(--muted)]">Actividad reciente</p>
                    <h3 className="mt-1 text-2xl font-semibold tracking-tight">
                      Últimos movimientos
                    </h3>
                  </div>
                  <Link
                    href="/historial"
                    className="secondary-button rounded-2xl px-4 py-2 text-center text-sm font-medium"
                  >
                    Ver todo
                  </Link>
                </div>

                <div className="mt-6 grid gap-3 md:grid-cols-3 2xl:grid-cols-1">
                  {[
                    "Registro de lote actualizado",
                    "Captura IA disponible",
                    "Ingreso local realizado correctamente",
                  ].map((event) => (
                    <div
                      key={event}
                      className="flex min-w-0 items-center gap-3 rounded-2xl bg-[var(--card-strong)] px-4 py-4 ring-1 ring-black/5 dark:ring-white/10"
                    >
                      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-[var(--egg)]">
                        <ClipboardList className="h-4 w-4 text-[var(--primary-strong)]" />
                      </div>
                      <div className="min-w-0">
                        <p className="truncate text-sm font-medium text-[var(--foreground)]">
                          {event}
                        </p>
                        <p className="mt-1 text-xs text-[var(--muted)]">Registro del sistema</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="min-w-0 space-y-5">
              <div className="glass-card rounded-[28px] p-5 shadow-[0_20px_50px_rgba(0,0,0,0.07)] sm:rounded-[32px] sm:p-6">
                <div className="flex items-center justify-between gap-3">
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-[var(--muted)]">Estado general</p>
                    <h3 className="mt-1 text-2xl font-semibold tracking-tight">Operativo</h3>
                  </div>
                  <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-[var(--egg)] ring-1 ring-black/5 dark:ring-white/10">
                    <ShieldCheck className="h-6 w-6 text-[var(--primary-strong)]" />
                  </div>
                </div>

                <div className="mt-6 grid gap-4 sm:grid-cols-3 2xl:grid-cols-1">
                  <div className="rounded-2xl bg-[var(--card-strong)] p-4 ring-1 ring-black/5 dark:ring-white/10">
                    <div className="flex items-center justify-between gap-3">
                      <span className="text-sm text-[var(--muted)]">Temperatura media</span>
                      <Thermometer className="h-4 w-4 shrink-0 text-[var(--primary-strong)]" />
                    </div>
                    <p className="mt-3 text-2xl font-semibold">27°C</p>
                  </div>

                  <div className="rounded-2xl bg-[var(--card-strong)] p-4 ring-1 ring-black/5 dark:ring-white/10">
                    <div className="flex items-center justify-between gap-3">
                      <span className="text-sm text-[var(--muted)]">Conectividad</span>
                      <Activity className="h-4 w-4 shrink-0 text-[var(--primary-strong)]" />
                    </div>
                    <p className="mt-3 text-2xl font-semibold">Estable</p>
                  </div>

                  <div className="rounded-2xl bg-[var(--card-strong)] p-4 ring-1 ring-black/5 dark:ring-white/10">
                    <div className="flex items-center justify-between gap-3">
                      <span className="text-sm text-[var(--muted)]">Control</span>
                      <ShieldCheck className="h-4 w-4 shrink-0 text-[var(--primary-strong)]" />
                    </div>
                    <p className="mt-3 text-2xl font-semibold">Normal</p>
                  </div>
                </div>
              </div>

              <div className="glass-card rounded-[28px] p-5 shadow-[0_20px_50px_rgba(0,0,0,0.07)] sm:rounded-[32px] sm:p-6">
                <p className="text-sm font-medium text-[var(--muted)]">Acciones rápidas</p>
                <h3 className="mt-1 text-2xl font-semibold tracking-tight">Gestión</h3>
                <div className="mt-6 grid gap-3 sm:grid-cols-3 2xl:grid-cols-1">
                  <Link
                    href="/registro"
                    className="primary-button flex items-center justify-center gap-2 rounded-2xl px-4 py-3 text-center text-sm font-semibold transition duration-300 hover:-translate-y-0.5"
                  >
                    <Plus className="h-4 w-4" /> Registrar aves
                  </Link>
                  <Link
                    href="/captura"
                    className="secondary-button flex items-center justify-center gap-2 rounded-2xl px-4 py-3 text-center text-sm font-medium transition duration-300 hover:-translate-y-0.5"
                  >
                    <Camera className="h-4 w-4" /> Cámara IA
                  </Link>
                  <Link
                    href="/perfil"
                    className="secondary-button flex items-center justify-center gap-2 rounded-2xl px-4 py-3 text-center text-sm font-medium transition duration-300 hover:-translate-y-0.5"
                  >
                    <User className="h-4 w-4" /> Abrir perfil
                  </Link>
                </div>
              </div>

              <div className="glass-card rounded-[28px] p-5 shadow-[0_20px_50px_rgba(0,0,0,0.07)] sm:rounded-[32px] sm:p-6">
                <p className="text-sm font-medium text-[var(--muted)]">Accesos de consulta</p>
                <h3 className="mt-1 text-2xl font-semibold tracking-tight">Revisión rápida</h3>
                <div className="mt-6 grid gap-3 sm:grid-cols-2 2xl:grid-cols-1">
                  <Link
                    href="/historial"
                    className="secondary-button flex items-center justify-center gap-2 rounded-2xl px-4 py-3 text-center text-sm font-medium"
                  >
                    <History className="h-4 w-4" /> Historial
                  </Link>
                  <Link
                    href="/captura"
                    className="secondary-button flex items-center justify-center gap-2 rounded-2xl px-4 py-3 text-center text-sm font-medium"
                  >
                    <Camera className="h-4 w-4" /> Nueva captura
                  </Link>
                </div>
              </div>
            </div>
          </section>
        </PageContainer>
      </AppShell>
    </RouteGuard>
  );
}
