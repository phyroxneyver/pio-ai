"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/layout/app-shell";
import { AppHeader } from "@/components/header/app-header";
import { Sidebar } from "@/components/layout/sidebar";
import { TabBar } from "@/components/layout/tab-bar";
import { PageContainer } from "@/components/layout/page-container";
import { RouteGuard } from "@/components/auth/route-guard";
import { listarAlertas, marcarAlertaLeida } from "@/lib/api";
import { Bell, AlertTriangle, CheckCircle, X } from "lucide-react";

type Alerta = {
  id: number;
  tipo: string;
  titulo: string;
  descripcion: string;
  prioridad: string;
  estado: string;
  created_at: string;
};

export default function AlertasPage() {
  const [alertas, setAlertas] = useState<Alerta[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalAlerta, setModalAlerta] = useState<Alerta | null>(null);

  useEffect(() => {
    listarAlertas()
      .then(data => {
        const lista = Array.isArray(data) ? data : data.alertas || [];
        setAlertas(lista);
      })
      .catch(() => setAlertas([]))
      .finally(() => setLoading(false));
  }, []);

  const handleMarcarLeida = async (id: number) => {
    await marcarAlertaLeida(id).catch(() => {});
    setAlertas(prev => prev.map(a => a.id === id ? { ...a, estado: "leida" } : a));
    if (modalAlerta?.id === id) setModalAlerta(null);
  };

  const colorPrioridad = (prioridad: string) => {
    if (prioridad === "critica") return "text-red-500 bg-red-500/10 border border-red-500/20";
    if (prioridad === "alta") return "text-orange-500 bg-orange-500/10 border border-orange-500/20";
    if (prioridad === "media") return "text-yellow-500 bg-yellow-500/10 border border-yellow-500/20";
    return "text-green-500 bg-green-500/10 border border-green-500/20";
  };

  const ringPrioridad = (prioridad: string) => {
    if (prioridad === "critica") return "ring-red-500/30";
    if (prioridad === "alta") return "ring-orange-500/30";
    if (prioridad === "media") return "ring-yellow-500/30";
    return "ring-green-500/30";
  };

  return (
    <RouteGuard>
      <AppShell header={<AppHeader />} sidebar={<Sidebar />} tabBar={<TabBar />}>
        <PageContainer>
          <div className="mx-auto max-w-3xl space-y-8">
            <div>
              <span className="inline-flex items-center gap-2 rounded-full bg-[var(--egg)] px-3 py-1 text-xs font-semibold text-[var(--primary-strong)]">
                <Bell className="h-3.5 w-3.5" />
                Alertas
              </span>
              <h1 className="mt-3 text-3xl font-semibold tracking-tight">Centro de alertas</h1>
              <p className="mt-2 text-sm text-[var(--muted)]">
                Aquí aparecen las alertas cuando el conteo baja repentinamente.
              </p>
            </div>

            <div className="glass-card rounded-[32px] p-6">
              {loading ? (
                <p className="text-sm text-[var(--muted)]">Cargando alertas...</p>
              ) : alertas.length === 0 ? (
                <div className="flex flex-col items-center gap-4 py-8 text-center">
                  <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-[var(--egg)]">
                    <AlertTriangle className="h-8 w-8 text-[var(--primary-strong)]" />
                  </div>
                  <div>
                    <p className="font-semibold">Sin alertas activas</p>
                    <p className="mt-1 text-sm text-[var(--muted)]">El sistema está operando normalmente.</p>
                  </div>
                </div>
              ) : (
                <div className="space-y-3">
                  {alertas.map(alerta => (
                    <div
                      key={alerta.id}
                      className={`rounded-2xl bg-[var(--card-strong)] px-4 py-4 ring-1 ${ringPrioridad(alerta.prioridad)} cursor-pointer transition hover:brightness-105`}
                      onClick={() => setModalAlerta(alerta)}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0">
                          <div className="flex items-center gap-2 mb-2">
                            <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${colorPrioridad(alerta.prioridad)}`}>
                              {alerta.prioridad?.toUpperCase()}
                            </span>
                            <span className="text-xs text-[var(--muted)]">
                              {new Date(alerta.created_at).toLocaleDateString("es-ES")}
                            </span>
                            {alerta.estado === "leida" && (
                              <span className="text-xs text-green-500 font-semibold">✓ Leída</span>
                            )}
                          </div>
                          <p className="text-sm font-semibold">{alerta.titulo}</p>
                          <p className="mt-1 text-xs text-[var(--muted)] line-clamp-1">{alerta.descripcion}</p>
                        </div>
                        {alerta.estado === "activa" && (
                          <button
                            onClick={(e) => { e.stopPropagation(); handleMarcarLeida(alerta.id); }}
                            className="shrink-0 flex items-center gap-1 text-xs font-semibold text-green-500 hover:text-green-400 transition min-h-[44px] px-2"
                          >
                            <CheckCircle className="h-4 w-4" />
                            Entendido
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* MODAL - Tarea 3 Etapa 4 */}
          {modalAlerta && (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4" onClick={() => setModalAlerta(null)}>
              <div className="w-full max-w-md rounded-[32px] bg-[var(--background)] p-6 shadow-2xl" onClick={e => e.stopPropagation()}>
                <div className="flex items-start justify-between gap-3 mb-4">
                  <div>
                    <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${colorPrioridad(modalAlerta.prioridad)}`}>
                      {modalAlerta.prioridad?.toUpperCase()}
                    </span>
                    <h2 className="mt-2 text-xl font-semibold">{modalAlerta.titulo}</h2>
                  </div>
                  <button onClick={() => setModalAlerta(null)} className="text-[var(--muted)] hover:text-[var(--foreground)] transition">
                    <X className="h-5 w-5" />
                  </button>
                </div>
                <p className="text-sm text-[var(--muted)] leading-6">{modalAlerta.descripcion}</p>
                <p className="mt-3 text-xs text-[var(--muted)]">
                  Fecha: {new Date(modalAlerta.created_at).toLocaleDateString("es-ES")}
                </p>
                <div className="mt-6 flex gap-3">
                  {modalAlerta.estado === "activa" && (
                    <button
                      onClick={() => handleMarcarLeida(modalAlerta.id)}
                      className="primary-button flex-1 rounded-2xl py-3 text-sm font-semibold min-h-[44px]"
                    >
                      ✓ Entendido
                    </button>
                  )}
                  <button
                    onClick={() => setModalAlerta(null)}
                    className="secondary-button flex-1 rounded-2xl py-3 text-sm font-medium min-h-[44px]"
                  >
                    Cerrar
                  </button>
                </div>
              </div>
            </div>
          )}
        </PageContainer>
      </AppShell>
    </RouteGuard>
  );
}