"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/layout/app-shell";
import { AppHeader } from "@/components/header/app-header";
import { Sidebar } from "@/components/layout/sidebar";
import { TabBar } from "@/components/layout/tab-bar";
import { PageContainer } from "@/components/layout/page-container";
import { RouteGuard } from "@/components/auth/route-guard";
import { fetchWithAuth } from "@/lib/api";
import { History, Egg, Bird, Baby } from "lucide-react";

type Ave = { id: number; tipo: string; cantidad: number; fecha_ingreso: string; notas?: string };
type Produccion = { id: number; ave_id: number; cantidad_huevos: number; fecha: string; notas?: string };

export default function HistorialPage() {
  const [aves, setAves] = useState<Ave[]>([]);
  const [produccion, setProduccion] = useState<Produccion[]>([]);
  const [loading, setLoading] = useState(true);
  const [filtro, setFiltro] = useState<"todo" | "pollitos" | "gallinas" | "huevos">("todo");

  useEffect(() => {
    Promise.all([
      fetchWithAuth("/aves").then(r => r.json()),
      fetchWithAuth("/produccion-huevos").then(r => r.json()),
    ])
      .then(([avesData, prodData]) => {
        setAves(Array.isArray(avesData) ? avesData : []);
        setProduccion(Array.isArray(prodData) ? prodData : []);
      })
      .finally(() => setLoading(false));
  }, []);

  const totalPollitos = aves.filter(a => a.tipo === "pollito").reduce((s, a) => s + a.cantidad, 0);
  const totalGallinas = aves.filter(a => a.tipo === "gallina").reduce((s, a) => s + a.cantidad, 0);
  const totalHuevos = produccion.reduce((s, p) => s + p.cantidad_huevos, 0);

  const avesFiltradas = aves.filter(a => {
    if (filtro === "pollitos") return a.tipo === "pollito";
    if (filtro === "gallinas") return a.tipo === "gallina";
    return true;
  });

  const mostrarHuevos = filtro === "todo" || filtro === "huevos";
  const mostrarAves = filtro === "todo" || filtro === "pollitos" || filtro === "gallinas";

  return (
    <RouteGuard>
      <AppShell header={<AppHeader />} sidebar={<Sidebar />} tabBar={<TabBar />}>
        <PageContainer>
          <div className="w-full space-y-6">

            {/* Título */}
            <div>
              <span className="inline-flex items-center gap-2 rounded-full bg-[var(--egg)] px-3 py-1 text-xs font-semibold text-[var(--primary-strong)]">
                <History className="h-3.5 w-3.5" />
                Historial
              </span>
              <h1 className="mt-3 text-3xl font-semibold tracking-tight">Registros anteriores</h1>
              <p className="mt-1 text-sm text-[var(--muted)]">Todos los conteos registrados en la granja.</p>
            </div>

            {loading ? (
              <div className="flex items-center justify-center py-16">
                <div className="h-8 w-8 animate-spin rounded-full border-4 border-[var(--egg)] border-t-transparent" />
              </div>
            ) : (
              <>
                {/* Tarjetas resumen */}
                <div className="grid grid-cols-3 gap-3">
                  <div className="glass-card rounded-[24px] p-4 text-center">
                    <div className="flex justify-center mb-2">
                      <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-yellow-500/10">
                        <Baby className="h-5 w-5 text-yellow-500" />
                      </div>
                    </div>
                    <p className="text-2xl font-black">{totalPollitos}</p>
                    <p className="text-xs text-[var(--muted)] mt-1">Pollitos</p>
                  </div>
                  <div className="glass-card rounded-[24px] p-4 text-center">
                    <div className="flex justify-center mb-2">
                      <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-orange-500/10">
                        <Bird className="h-5 w-5 text-orange-500" />
                      </div>
                    </div>
                    <p className="text-2xl font-black">{totalGallinas}</p>
                    <p className="text-xs text-[var(--muted)] mt-1">Gallinas</p>
                  </div>
                  <div className="glass-card rounded-[24px] p-4 text-center">
                    <div className="flex justify-center mb-2">
                      <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--egg)]">
                        <Egg className="h-5 w-5 text-[var(--primary-strong)]" />
                      </div>
                    </div>
                    <p className="text-2xl font-black">{totalHuevos}</p>
                    <p className="text-xs text-[var(--muted)] mt-1">Huevos</p>
                  </div>
                </div>

                {/* Filtros */}
                <div className="flex gap-2 flex-wrap">
                  {(["todo", "pollitos", "gallinas", "huevos"] as const).map(f => (
                    <button
                      key={f}
                      onClick={() => setFiltro(f)}
                      className={`rounded-2xl px-4 py-2 text-xs font-semibold min-h-[44px] transition capitalize ${
                        filtro === f
                          ? "bg-[var(--egg)] text-[var(--primary-strong)]"
                          : "bg-[var(--card-strong)] text-[var(--muted)] hover:text-[var(--foreground)]"
                      }`}
                    >
                      {f === "todo" ? "Todos" : f}
                    </button>
                  ))}
                </div>

                {/* Lista de aves */}
                {mostrarAves && (
                  <div className="glass-card rounded-[32px] p-6">
                    <h2 className="mb-4 text-lg font-semibold">
                      {filtro === "pollitos" ? "Pollitos" : filtro === "gallinas" ? "Gallinas" : "Aves registradas"}
                    </h2>
                    {avesFiltradas.length === 0 ? (
                      <p className="text-sm text-[var(--muted)] py-4 text-center">No hay registros aún.</p>
                    ) : (
                      <div className="space-y-2">
                        {avesFiltradas.map(ave => (
                          <div key={ave.id} className="flex items-center justify-between rounded-2xl bg-[var(--card-strong)] px-4 py-3">
                            <div className="flex items-center gap-3">
                              <div className={`flex h-9 w-9 items-center justify-center rounded-xl ${
                                ave.tipo === "pollito" ? "bg-yellow-500/10" : "bg-orange-500/10"
                              }`}>
                                {ave.tipo === "pollito"
                                  ? <Baby className="h-4 w-4 text-yellow-500" />
                                  : <Bird className="h-4 w-4 text-orange-500" />
                                }
                              </div>
                              <div>
                                <p className="text-sm font-semibold capitalize">{ave.tipo}</p>
                                <p className="text-xs text-[var(--muted)]">
                                  {new Date(ave.fecha_ingreso).toLocaleDateString("es-ES", {
                                    day: "numeric", month: "short", year: "numeric"
                                  })}
                                </p>
                              </div>
                            </div>
                            <div className="text-right">
                              <span className="text-2xl font-black">{ave.cantidad}</span>
                              <p className="text-xs text-[var(--muted)]">unidades</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Lista de huevos */}
                {mostrarHuevos && (
                  <div className="glass-card rounded-[32px] p-6">
                    <h2 className="mb-4 text-lg font-semibold">Producción de huevos</h2>
                    {produccion.length === 0 ? (
                      <p className="text-sm text-[var(--muted)] py-4 text-center">No hay registros aún.</p>
                    ) : (
                      <div className="space-y-2">
                        {produccion.map(p => (
                          <div key={p.id} className="flex items-center justify-between rounded-2xl bg-[var(--card-strong)] px-4 py-3">
                            <div className="flex items-center gap-3">
                              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[var(--egg)]">
                                <Egg className="h-4 w-4 text-[var(--primary-strong)]" />
                              </div>
                              <div>
                                <p className="text-sm font-semibold">Huevos</p>
                                <p className="text-xs text-[var(--muted)]">
                                  {new Date(p.fecha).toLocaleDateString("es-ES", {
                                    day: "numeric", month: "short", year: "numeric"
                                  })}
                                </p>
                              </div>
                            </div>
                            <div className="text-right">
                              <span className="text-2xl font-black">{p.cantidad_huevos}</span>
                              <p className="text-xs text-[var(--muted)]">huevos</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </>
            )}
          </div>
        </PageContainer>
      </AppShell>
    </RouteGuard>
  );
}