"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/layout/app-shell";
import { AppHeader } from "@/components/header/app-header";
import { Sidebar } from "@/components/layout/sidebar";
import { TabBar } from "@/components/layout/tab-bar";
import { PageContainer } from "@/components/layout/page-container";
import { RouteGuard } from "@/components/auth/route-guard";
import { fetchWithAuth } from "@/lib/api";
import { History } from "lucide-react";

type Ave = { id: number; tipo: string; cantidad: number; fecha_ingreso: string; notas?: string };
type Produccion = { id: number; ave_id: number; cantidad_huevos: number; fecha: string; notas?: string };

export default function HistorialPage() {
  const [aves, setAves] = useState<Ave[]>([]);
  const [produccion, setProduccion] = useState<Produccion[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetchWithAuth("/aves").then(r => r.json()),
      fetchWithAuth("/produccion-huevos").then(r => r.json()),
    ])
      .then(([avesData, prodData]) => {
        setAves(avesData);
        setProduccion(prodData);
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <RouteGuard>
      <AppShell header={<AppHeader />} sidebar={<Sidebar />} tabBar={<TabBar />}>
        <PageContainer>
          <div className="mx-auto max-w-3xl space-y-8">
            <div>
              <span className="inline-flex items-center gap-2 rounded-full bg-[var(--egg)] px-3 py-1 text-xs font-semibold text-[var(--primary-strong)]">
                <History className="h-3.5 w-3.5" />
                Historial
              </span>
              <h1 className="mt-3 text-3xl font-semibold tracking-tight">Registros anteriores</h1>
            </div>

            {loading ? (
              <p className="text-sm text-[var(--muted)]">Cargando...</p>
            ) : (
              <>
                <div className="glass-card rounded-[32px] p-6">
                  <h2 className="mb-4 text-lg font-semibold">Aves registradas</h2>
                  {aves.length === 0 ? (
                    <p className="text-sm text-[var(--muted)]">No hay registros aún.</p>
                  ) : (
                    <div className="space-y-3">
                      {aves.map(ave => (
                        <div key={ave.id} className="flex items-center justify-between rounded-2xl bg-[var(--card-strong)] px-4 py-3">
                          <div>
                            <p className="text-sm font-semibold capitalize">{ave.tipo}</p>
                            <p className="text-xs text-[var(--muted)]">{new Date(ave.fecha_ingreso).toLocaleDateString("es-ES")}</p>
                          </div>
                          <span className="text-2xl font-black">{ave.cantidad}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div className="glass-card rounded-[32px] p-6">
                  <h2 className="mb-4 text-lg font-semibold">Producción de huevos</h2>
                  {produccion.length === 0 ? (
                    <p className="text-sm text-[var(--muted)]">No hay registros aún.</p>
                  ) : (
                    <div className="space-y-3">
                      {produccion.map(p => (
                        <div key={p.id} className="flex items-center justify-between rounded-2xl bg-[var(--card-strong)] px-4 py-3">
                          <div>
                            <p className="text-sm font-semibold">Huevos</p>
                            <p className="text-xs text-[var(--muted)]">{new Date(p.fecha).toLocaleDateString("es-ES")}</p>
                          </div>
                          <span className="text-2xl font-black">{p.cantidad_huevos}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        </PageContainer>
      </AppShell>
    </RouteGuard>
  );
}