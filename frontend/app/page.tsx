import {
  Activity,
  ChartColumn,
  ClipboardList,
  ShieldCheck,
  Sparkles,
  Warehouse,
} from "lucide-react";
import { RouteGuard } from "@/components/auth/route-guard";
import { AppHeader } from "@/components/header/app-header";
import { AppShell } from "@/components/layout/app-shell";
import { Sidebar } from "@/components/layout/sidebar";
import { TabBar } from "@/components/layout/tab-bar";

const stats = [
  {
    title: "Aves registradas",
    value: "1,248",
    note: "Monitoreo activo",
    icon: ClipboardList,
  },
  {
    title: "Galpones activos",
    value: "08",
    note: "Todos en línea",
    icon: Warehouse,
  },
  {
    title: "Alertas recientes",
    value: "03",
    note: "Revisión recomendada",
    icon: Activity,
  },
];

export default function HomePage() {
  return (
    <RouteGuard>
      <AppShell
        header={<AppHeader />}
        sidebar={<Sidebar />}
        tabBar={<TabBar />}
      >
        <section className="glass-card animate-fade-up overflow-hidden rounded-[32px] p-6 shadow-[0_20px_50px_rgba(0,0,0,0.07)] sm:p-8">
          <div className="grid gap-8 lg:grid-cols-[1.3fr_0.9fr]">
            <div>
              <span className="inline-flex items-center gap-2 rounded-full bg-[var(--egg)] px-3 py-1 text-xs font-semibold text-[var(--primary-strong)] dark:bg-white/5 animate-pulse-soft">
                <Sparkles className="h-3.5 w-3.5" />
                Panel principal
              </span>

              <h2 className="mt-4 max-w-xl text-3xl font-semibold tracking-tight sm:text-4xl">
                Control inteligente y visual de tu producción avícola
              </h2>

              <p className="mt-4 max-w-2xl text-sm leading-6 text-[var(--muted)] sm:text-base">
                Supervisa registros, estado del sistema, conectividad y actividad
                reciente desde una interfaz más limpia y adaptable.
              </p>

              <div className="mt-6 flex flex-wrap gap-3">
                <button className="primary-button inline-flex items-center gap-2 rounded-2xl px-5 py-3 text-sm font-semibold transition duration-300 hover:-translate-y-0.5">
                  <ClipboardList className="h-4 w-4" />
                  Ver registros
                </button>

                <button className="secondary-button inline-flex items-center gap-2 rounded-2xl px-5 py-3 text-sm font-medium transition duration-300 hover:-translate-y-0.5">
                  <ChartColumn className="h-4 w-4" />
                  Ver métricas
                </button>
              </div>
            </div>

            <div className="grid gap-4">
              <div className="rounded-[28px] bg-[var(--card-strong)] p-5 shadow-sm ring-1 ring-black/5 dark:ring-white/10 animate-float-soft">
                <p className="text-sm text-[var(--muted)]">Estado general</p>
                <div className="mt-4 flex items-end justify-between">
                  <div>
                    <h3 className="text-3xl font-semibold">Operativo</h3>
                    <p className="mt-1 text-sm text-[var(--muted)]">
                      Sin incidentes críticos
                    </p>
                  </div>

                  <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-[var(--egg)] ring-1 ring-black/5 dark:ring-white/10">
                    <ShieldCheck className="h-7 w-7 text-[var(--primary-strong)]" />
                  </div>
                </div>
              </div>

              <div className="grid gap-4 sm:grid-cols-3 lg:grid-cols-1 xl:grid-cols-3">
                {stats.map((item, index) => {
                  const Icon = item.icon;

                  return (
                    <div
                      key={item.title}
                      className="card-interactive rounded-[24px] bg-[var(--card-strong)] p-4 shadow-sm ring-1 ring-black/5 dark:ring-white/10 animate-fade-up"
                      style={{ animationDelay: `${index * 100}ms` }}
                    >
                      <div className="flex items-center justify-between">
                        <p className="text-sm text-[var(--muted)]">{item.title}</p>
                        <Icon className="h-5 w-5 text-[var(--primary-strong)]" />
                      </div>

                      <p className="mt-3 text-2xl font-semibold">{item.value}</p>
                      <p className="mt-1 text-xs text-[var(--muted)]">{item.note}</p>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </section>
      </AppShell>
    </RouteGuard>
  );
}