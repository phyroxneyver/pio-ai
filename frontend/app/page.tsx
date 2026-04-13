import {
  Activity,
  AlertTriangle,
  ChartColumn,
  ClipboardList,
  Egg,
  ShieldCheck,
  Thermometer,
  Warehouse,
} from "lucide-react";

import ImageUploadButton from "@/components/modal/ImageUploadButton";
import { RouteGuard } from "@/components/auth/route-guard";
import { AppHeader } from "@/components/header/app-header";
import { AppShell } from "@/components/layout/app-shell";
import { PageContainer } from "@/components/layout/page-container";
import { Sidebar } from "@/components/layout/sidebar";
import { TabBar } from "@/components/layout/tab-bar";

const stats = [
  {
    title: "Aves registradas",
    value: "1,248",
    note: "Actualizado hoy",
    icon: Egg,
  },
  {
    title: "Galpones activos",
    value: "08",
    note: "Todos operativos",
    icon: Warehouse,
  },
  {
    title: "Alertas",
    value: "03",
    note: "Revisión recomendada",
    icon: AlertTriangle,
  },
  {
    title: "Sensores",
    value: "16",
    note: "Conectados",
    icon: Activity,
  },
];

const recentEvents = [
  "Registro de lote actualizado hace 8 min",
  "Sensor de temperatura sincronizado",
  "Ingreso local realizado correctamente",
  "Perfil de usuario consultado",
];

export default function HomePage() {
  return (
    <RouteGuard>
      <AppShell
        header={<AppHeader />}
        sidebar={<Sidebar />}
        tabBar={<TabBar />}
      >
        <PageContainer>
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
                    <button className="primary-button w-full rounded-2xl px-4 py-3 text-sm font-semibold transition duration-300 hover:-translate-y-0.5 sm:w-auto">
                      Ver registros
                    </button>

                    <button className="secondary-button w-full rounded-2xl px-4 py-3 text-sm font-medium transition duration-300 hover:-translate-y-0.5 sm:w-auto">
                      Ver métricas
                    </button>
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

                      <p className="mt-5 text-3xl font-semibold tracking-tight">
                        {item.value}
                      </p>

                      <p className="mt-2 text-sm text-[var(--muted)]">
                        {item.note}
                      </p>
                    </div>
                  );
                })}
              </div>

              <div className="glass-card rounded-[32px] p-6 shadow-[0_20px_50px_rgba(0,0,0,0.07)]">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p className="text-sm font-medium text-[var(--muted)]">
                      Actividad reciente
                    </p>
                    <h3 className="mt-1 text-2xl font-semibold tracking-tight">
                      Últimos movimientos
                    </h3>
                  </div>

                  <button className="secondary-button w-full rounded-2xl px-4 py-2 text-sm font-medium sm:w-auto">
                    Ver todo
                  </button>
                </div>

                <div className="mt-6 space-y-3">
                  {recentEvents.map((event) => (
                    <div
                      key={event}
                      className="flex items-center gap-3 rounded-2xl bg-[var(--card-strong)] px-4 py-4 ring-1 ring-black/5 dark:ring-white/10"
                    >
                      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-[var(--egg)]">
                        <ClipboardList className="h-4 w-4 text-[var(--primary-strong)]" />
                      </div>

                      <div className="min-w-0">
                        <p className="truncate text-sm font-medium text-[var(--foreground)]">
                          {event}
                        </p>
                        <p className="mt-1 text-xs text-[var(--muted)]">
                          Registro del sistema
                        </p>
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
                    <p className="text-sm font-medium text-[var(--muted)]">
                      Estado general
                    </p>
                    <h3 className="mt-1 text-2xl font-semibold tracking-tight">
                      Operativo
                    </h3>
                  </div>

                  <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-[var(--egg)] ring-1 ring-black/5 dark:ring-white/10">
                    <ShieldCheck className="h-6 w-6 text-[var(--primary-strong)]" />
                  </div>
                </div>

                <div className="mt-6 space-y-4">
                  <div className="rounded-2xl bg-[var(--card-strong)] p-4 ring-1 ring-black/5 dark:ring-white/10">
                    <div className="flex items-center justify-between gap-3">
                      <span className="text-sm text-[var(--muted)]">
                        Temperatura media
                      </span>
                      <Thermometer className="h-4 w-4 shrink-0 text-[var(--primary-strong)]" />
                    </div>
                    <p className="mt-3 text-2xl font-semibold">27°C</p>
                  </div>

                  <div className="rounded-2xl bg-[var(--card-strong)] p-4 ring-1 ring-black/5 dark:ring-white/10">
                    <div className="flex items-center justify-between gap-3">
                      <span className="text-sm text-[var(--muted)]">
                        Conectividad
                      </span>
                      <Activity className="h-4 w-4 shrink-0 text-[var(--primary-strong)]" />
                    </div>
                    <p className="mt-3 text-2xl font-semibold">Estable</p>
                  </div>

                  <div className="rounded-2xl bg-[var(--card-strong)] p-4 ring-1 ring-black/5 dark:ring-white/10">
                    <div className="flex items-center justify-between gap-3">
                      <span className="text-sm text-[var(--muted)]">
                        Incidencias
                      </span>
                      <AlertTriangle className="h-4 w-4 shrink-0 text-[var(--primary-strong)]" />
                    </div>
                    <p className="mt-3 text-2xl font-semibold">Bajas</p>
                  </div>
                </div>
              </div>

              <div className="glass-card rounded-[32px] p-6 shadow-[0_20px_50px_rgba(0,0,0,0.07)]">
                <p className="text-sm font-medium text-[var(--muted)]">
                  Acciones rápidas
                </p>
                <h3 className="mt-1 text-2xl font-semibold tracking-tight">
                  Gestión
                </h3>

                <div className="mt-6 grid gap-3">
                  <button className="primary-button rounded-2xl px-4 py-3 text-sm font-semibold transition duration-300 hover:-translate-y-0.5">
                    Registrar aves
                  </button>

                  <button className="secondary-button rounded-2xl px-4 py-3 text-sm font-medium transition duration-300 hover:-translate-y-0.5">
                    Validar sensores
                  </button>

                  <button className="secondary-button rounded-2xl px-4 py-3 text-sm font-medium transition duration-300 hover:-translate-y-0.5">
                    Abrir perfil
                  </button>
                </div>
              </div>
            </div>
          </section>
        </PageContainer>
      </AppShell>
    </RouteGuard>
  );
}