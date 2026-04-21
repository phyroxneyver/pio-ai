"use client";
import {
  Activity, AlertTriangle, ChartColumn, ClipboardList,
  Egg, ShieldCheck, Thermometer, Warehouse, Plus, User
} from "lucide-react";
import { useEffect, useState } from "react";
import { fetchWithAuth, listarAlertas } from "@/lib/api";
import { RouteGuard } from "@/components/auth/route-guard";
import { AppHeader } from "@/components/header/app-header";
import { AppShell } from "@/components/layout/app-shell";
import { PageContainer } from "@/components/layout/page-container";
import { Sidebar } from "@/components/layout/sidebar";
import { TabBar } from "@/components/layout/tab-bar";
import Link from "next/link";

type Ave = { id: number; tipo: string; cantidad: number; fecha_ingreso: string };
type Alerta = { id: number; titulo: string; prioridad: string; estado: string };

export default function HomePage() {
  const [totalAves, setTotalAves] = useState("...");
  const [totalHuevos, setTotalHuevos] = useState("...");
  const [alertasActivas, setAlertasActivas] = useState(0);
  const [ultimoRegistro, setUltimoRegistro] = useState<Ave | null>(null);
  const [alertaCritica, setAlertaCritica] = useState<Alerta | null>(null);
  const [bannerVisible, setBannerVisible] = useState(false);

  useEffect(() => {
    // Cargar aves
    fetchWithAuth("/aves")
      .then(r => r.json())
      .then(data => {
        if (Array.isArray(data)) {
          const total = data.reduce((sum: number, a: { cantidad: number }) => sum + a.cantidad, 0);
          setTotalAves(total.toLocaleString());
          // Último registro
          const ultimo = data[data.length - 1];
          if (ultimo) setUltimoRegistro(ultimo);
        }
      })
      .catch(() => setTotalAves("N/A"));

    // Cargar huevos
    fetchWithAuth("/produccion-huevos")
      .then(r => r.json())
      .then(data => {
        if (Array.isArray(data)) {
          const total = data.reduce((sum: number, p: { cantidad_huevos: number }) => sum + p.cantidad_huevos, 0);
          setTotalHuevos(total.toLocaleString());
        }
      })
      .catch(() => setTotalHuevos("N/A"));

    // Cargar alertas
    listarAlertas("activa")
      .then(data => {
        const lista = Array.isArray(data) ? data : data.alertas || [];
        setAlertasActivas(lista.length);
        const critica = lista.find((a: Alerta) => a.prioridad === "critica" || a.prioridad === "alta");
        if (critica) {
          setAlertaCritica(critica);
          setBannerVisible(true);
        }
      })
      .catch(() => {});
  }, []);

  const hayAlerta = alertasActivas > 0;

  const stats = [
    {
      title: "Aves registradas",
      value: totalAves,
      note: "Actualizado hoy",
      icon: Egg,
      alerta: false
    },
    {
      title: "Galpones activos",
      value: "08",
      note: "Todos operativos",
      icon: Warehouse,
      alerta: false
    },
    {
      title: "Alertas activas",
      value: alertasActivas.toString(),
      note: hayAlerta ? "Revisión recomendada" : "Sin incidencias",
      icon: AlertTriangle,
      alerta: hayAlerta
    },
    {
      title: "Huevos producidos",
      value: totalHuevos,
      note: "Total registrado",
      icon: Egg,
      alerta: false
    },
  ];

  return (
    <RouteGuard>
      <AppShell header={<AppHeader />} sidebar={<Sidebar />} tabBar={<TabBar />}>
        <PageContainer>

          {/* BANNER DE ALERTA - Tarea 4 Etapa 4 */}
          {bannerVisible && alertaCritica && (
            <div className="mb-5 flex items-center justify-between gap-3 rounded-2xl bg-red-500/10 border border-red-500/20 px-4 py-3">
              <div className="flex items-center gap-3">
                <AlertTriangle className="h-5 w-5 text-red-500 shrink-0" />
                <div>
                  <p className="text-sm font-semibold text-red-500">⚠️ Alerta activa</p>
                  <p className="text-xs text-red-400">{alertaCritica.titulo}</p>
                </div>
              </div>
              <button
                onClick={() => setBannerVisible(false)}
                className="text-xs font-semibold text-red-400 hover:text-red-300 transition shrink-0"
              >
                Entendido ✓
              </button>
            </div>
          )}

          <section className="grid gap-5 2xl:grid-cols-[1.4fr_0.95fr]">
            <div className="space-y-5 min-w-0">
              <div className="glass-card rounded-[32px] p-5 shadow-[0_20px_50px_rgba(0,0,0,0.07)] sm:p-8">
                <div className="flex flex-col gap-6">
                  <div className="max-w-2xl min-w-0">
                    <span className="inline-flex max-w-full items-center gap-2 rounded-full bg-[var(--egg)] px-3 py-1 text-xs font-semibold text-[var(--primary-strong)] dark:bg-white/5">
                      <ChartColumn className="h-3.5 w-3.5 shrink-0" />
                      <span className="truncate">Vista general del sistema</span>
                    </span>
                    <h2 className="mt-4 text-3xl font-semibold leading-tight tracking-tight sm:text-4xl">
                      Panel administrativo del sistema avícola
                    </h2>
                    <p className="mt-4 text-sm leading-7 text-[var(--muted)] sm:text-base">
                      Supervisa el estado general, registros, alertas y actividad
                      operativa desde una interfaz más ordenada y profesional.
                    </p>
                  </div>
                  <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap">
                    <Link href="/historial" className="primary-button w-full rounded-2xl px-4 py-3 text-sm font-semibold transition duration-300 hover:-translate-y-0.5 sm:w-auto text-center">
                      Ver registros
                    </Link>
                    <Link href="/alertas" className="secondary-button w-full rounded-2xl px-4 py-3 text-sm font-medium transition duration-300 hover:-translate-y-0.5 sm:w-auto text-center">
                      Ver alertas
                    </Link>
                  </div>
                </div>
              </div>

              {/* TARJETAS - Tarea 1 y 2 Etapa 3 */}
              <div className="grid gap-4 sm:grid-cols-2 2xl:grid-cols-4">
                {stats.map((item) => {
                  const Icon = item.icon;
                  return (
                    <div
                      key={item.title}
                      className={`glass-card card-interactive min-w-0 rounded-[28px] p-5 shadow-[0_10px_30px_rgba(0,0,0,0.05)] transition-all ${
                        item.alerta ? "ring-2 ring-red-500/50 bg-red-500/5" : ""
                      }`}
                    >
                      <div className="flex items-center justify-between gap-3">
                        <p className="min-w-0 text-sm font-medium text-[var(--muted)]">
                          {item.title}
                        </p>
                        <div className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl ring-1 ring-black/5 dark:ring-white/10 ${
                          item.alerta ? "bg-red-500/20" : "bg-[var(--egg)]"
                        }`}>
                          <Icon className={`h-5 w-5 ${item.alerta ? "text-red-500" : "text-[var(--primary-strong)]"}`} />
                        </div>
                      </div>
                      <p className={`mt-5 text-3xl font-semibold tracking-tight ${item.alerta ? "text-red-500" : ""}`}>
                        {item.value}
                      </p>
                      <p className="mt-2 text-sm text-[var(--muted)]">
                        {item.note}
                      </p>
                    </div>
                  );
                })}
              </div>

              {/* ÚLTIMO REGISTRO - Tarea 3 Etapa 3 */}
              {ultimoRegistro && (
                <div className="glass-card rounded-[32px] p-6 shadow-[0_20px_50px_rgba(0,0,0,0.07)]">
                  <p className="text-sm font-medium text-[var(--muted)]">Último registro</p>
                  <h3 className="mt-1 text-2xl font-semibold tracking-tight">Registro reciente</h3>
                  <div className="mt-4 flex items-center justify-between rounded-2xl bg-[var(--card-strong)] px-4 py-4">
                    <div>
                      <p className="text-sm font-semibold capitalize">{ultimoRegistro.tipo}</p>
                      <p className="text-xs text-[var(--muted)]">
                        {new Date(ultimoRegistro.fecha_ingreso).toLocaleDateString("es-ES")}
                      </p>
                    </div>
                    <span className="text-3xl font-black">{ultimoRegistro.cantidad}</span>
                  </div>
                </div>
              )}

              {/* ACTIVIDAD RECIENTE */}
              <div className="glass-card rounded-[32px] p-6 shadow-[0_20px_50px_rgba(0,0,0,0.07)]">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p className="text-sm font-medium text-[var(--muted)]">Actividad reciente</p>
                    <h3 className="mt-1 text-2xl font-semibold tracking-tight">Últimos movimientos</h3>
                  </div>
                  <Link href="/historial" className="secondary-button w-full rounded-2xl px-4 py-2 text-sm font-medium sm:w-auto text-center">
                    Ver todo
                  </Link>
                </div>
                <div className="mt-6 space-y-3">
                  {["Registro de lote actualizado", "Sensor de temperatura sincronizado", "Ingreso local realizado correctamente"].map((event) => (
                    <div key={event} className="flex items-center gap-3 rounded-2xl bg-[var(--card-strong)] px-4 py-4 ring-1 ring-black/5 dark:ring-white/10">
                      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-[var(--egg)]">
                        <ClipboardList className="h-4 w-4 text-[var(--primary-strong)]" />
                      </div>
                      <div className="min-w-0">
                        <p className="truncate text-sm font-medium text-[var(--foreground)]">{event}</p>
                        <p className="mt-1 text-xs text-[var(--muted)]">Registro del sistema</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="space-y-5 min-w-0">
              <div className="glass-card rounded-[32px] p-6 shadow-[0_20px_50px_rgba(0,0,0,0.07)]">
                <div className="flex items-center justify-between gap-3">
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-[var(--muted)]">Estado general</p>
                    <h3 className={`mt-1 text-2xl font-semibold tracking-tight ${hayAlerta ? "text-red-500" : ""}`}>
                      {hayAlerta ? "⚠️ Con alertas" : "Operativo"}
                    </h3>
                  </div>
                  <div className={`flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl ring-1 ring-black/5 dark:ring-white/10 ${hayAlerta ? "bg-red-500/20" : "bg-[var(--egg)]"}`}>
                    <ShieldCheck className={`h-6 w-6 ${hayAlerta ? "text-red-500" : "text-[var(--primary-strong)]"}`} />
                  </div>
                </div>
                <div className="mt-6 space-y-4">
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
                      <span className="text-sm text-[var(--muted)]">Incidencias</span>
                      <AlertTriangle className="h-4 w-4 shrink-0 text-[var(--primary-strong)]" />
                    </div>
                    <p className={`mt-3 text-2xl font-semibold ${hayAlerta ? "text-red-500" : ""}`}>
                      {hayAlerta ? `${alertasActivas} activa(s)` : "Bajas"}
                    </p>
                  </div>
                </div>
              </div>

              <div className="glass-card rounded-[32px] p-6 shadow-[0_20px_50px_rgba(0,0,0,0.07)]">
                <p className="text-sm font-medium text-[var(--muted)]">Acciones rápidas</p>
                <h3 className="mt-1 text-2xl font-semibold tracking-tight">Gestión</h3>
                <div className="mt-6 grid gap-3">
                  <Link href="/registro" className="primary-button rounded-2xl px-4 py-3 text-sm font-semibold transition duration-300 hover:-translate-y-0.5 text-center flex items-center justify-center gap-2">
                    <Plus className="h-4 w-4" /> Registrar aves
                  </Link>
                  <Link href="/alertas" className="secondary-button rounded-2xl px-4 py-3 text-sm font-medium transition duration-300 hover:-translate-y-0.5 text-center">
                    Ver alertas
                  </Link>
                  <Link href="/perfil" className="secondary-button rounded-2xl px-4 py-3 text-sm font-medium transition duration-300 hover:-translate-y-0.5 text-center flex items-center justify-center gap-2">
                    <User className="h-4 w-4" /> Abrir perfil
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