"use client";

import { useEffect, useState } from "react";
import {
  Activity,
  AlertTriangle,
  BarChart3,
  BrainCircuit,
  CheckCircle2,
  Clock,
  Gauge,
  ImageIcon,
  RefreshCw,
} from "lucide-react";

import { RouteGuard } from "@/components/auth/route-guard";
import { AppHeader } from "@/components/header/app-header";
import { AppShell } from "@/components/layout/app-shell";
import { PageContainer } from "@/components/layout/page-container";
import { Sidebar } from "@/components/layout/sidebar";
import { TabBar } from "@/components/layout/tab-bar";
import { obtenerUltimaMetricaIA } from "@/lib/api";
import type { LastAIMetrics } from "@/types/media";

const LAST_AI_METRICS_KEY = "pioai_last_ai_metrics";

type ServerMetric = {
  imagen_id: number;
  resultado_id: number;
  conteo_pollitos: number | null;
  confianza: string | null;
  estado: string;
  duracion_ms: number | null;
  precision_estimada: number | null;
  notas_ia: string | null;
  procesado_at: string | null;
  imagen_url: string;
};

function formatPercent(value: number | null | undefined) {
  if (value === null || value === undefined) return "Sin dato";
  return `${Math.round(value * 100)}%`;
}

function formatMs(value: number | null | undefined) {
  if (value === null || value === undefined) return "Sin dato";
  return `${value} ms`;
}

export default function IAMetricasPage() {
  const [localMetric, setLocalMetric] = useState<LastAIMetrics | null>(null);
  const [serverMetric, setServerMetric] = useState<ServerMetric | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function cargarMetricas() {
    setLoading(true);
    setError("");

    try {
      const raw = localStorage.getItem(LAST_AI_METRICS_KEY);

      if (raw) {
        setLocalMetric(JSON.parse(raw) as LastAIMetrics);
      } else {
        setLocalMetric(null);
      }

      const metric = (await obtenerUltimaMetricaIA()) as ServerMetric;
      setServerMetric(metric);
    } catch (err) {
      const message = err instanceof Error ? err.message : "No se pudo cargar la métrica.";
      setError(message);
      setServerMetric(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    cargarMetricas();
  }, []);

  return (
    <RouteGuard>
      <AppShell header={<AppHeader />} sidebar={<Sidebar />} tabBar={<TabBar />}>
        <PageContainer>
          <div className="space-y-6">
            <div className="glass-card rounded-[32px] p-6">
              <span className="inline-flex items-center gap-2 rounded-full bg-[var(--egg)] px-3 py-1 text-xs font-semibold text-[var(--primary-strong)]">
                <BarChart3 className="h-3.5 w-3.5" />
                Panel técnico oculto
              </span>

              <div className="mt-4 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
                <div>
                  <h1 className="text-3xl font-semibold tracking-tight">
                    Métricas internas de IA
                  </h1>

                  <p className="mt-2 max-w-2xl text-sm leading-6 text-[var(--muted)]">
                    Esta pantalla no aparece en el menú principal. Sirve para revisar el último tiempo
                    exacto de procesamiento, confianza y precisión estimada de la IA.
                  </p>
                </div>

                <button
                  onClick={cargarMetricas}
                  className="secondary-button inline-flex min-h-[44px] items-center justify-center gap-2 rounded-2xl px-4 py-3 text-sm font-semibold"
                >
                  <RefreshCw className="h-4 w-4" />
                  Actualizar
                </button>
              </div>
            </div>

            {loading ? (
              <div className="glass-card rounded-[32px] p-8 text-center">
                <div className="mx-auto h-8 w-8 animate-spin rounded-full border-4 border-[var(--egg)] border-t-transparent" />
                <p className="mt-3 text-sm text-[var(--muted)]">
                  Cargando métricas...
                </p>
              </div>
            ) : null}

            {!loading && error ? (
              <div className="rounded-[28px] border border-orange-500/20 bg-orange-500/10 p-5">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="mt-0.5 h-5 w-5 text-orange-500" />

                  <div>
                    <p className="text-sm font-semibold text-orange-500">
                      No hay métrica del servidor todavía
                    </p>

                    <p className="mt-1 text-sm leading-6 text-[var(--muted)]">
                      {error}
                    </p>
                  </div>
                </div>
              </div>
            ) : null}

            {serverMetric ? (
              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                <div className="glass-card rounded-[28px] p-5">
                  <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[var(--egg)]">
                    <Clock className="h-5 w-5 text-[var(--primary-strong)]" />
                  </div>

                  <p className="mt-4 text-sm text-[var(--muted)]">
                    Tiempo servidor
                  </p>

                  <p className="mt-1 text-3xl font-black">
                    {formatMs(serverMetric.duracion_ms)}
                  </p>
                </div>

                <div className="glass-card rounded-[28px] p-5">
                  <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-green-500/10">
                    <Gauge className="h-5 w-5 text-green-500" />
                  </div>

                  <p className="mt-4 text-sm text-[var(--muted)]">
                    Precisión estimada
                  </p>

                  <p className="mt-1 text-3xl font-black">
                    {formatPercent(serverMetric.precision_estimada)}
                  </p>
                </div>

                <div className="glass-card rounded-[28px] p-5">
                  <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-blue-500/10">
                    <BrainCircuit className="h-5 w-5 text-blue-500" />
                  </div>

                  <p className="mt-4 text-sm text-[var(--muted)]">
                    Confianza IA
                  </p>

                  <p className="mt-1 text-3xl font-black capitalize">
                    {serverMetric.confianza || "Sin dato"}
                  </p>
                </div>

                <div className="glass-card rounded-[28px] p-5">
                  <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-purple-500/10">
                    <Activity className="h-5 w-5 text-purple-500" />
                  </div>

                  <p className="mt-4 text-sm text-[var(--muted)]">
                    Conteo IA
                  </p>

                  <p className="mt-1 text-3xl font-black">
                    {serverMetric.conteo_pollitos ?? "Sin dato"}
                  </p>
                </div>
              </div>
            ) : null}

            <div className="grid gap-5 xl:grid-cols-[0.9fr_1.1fr]">
              <div className="glass-card rounded-[32px] p-6">
                <h2 className="flex items-center gap-2 text-xl font-semibold tracking-tight">
                  <CheckCircle2 className="h-5 w-5 text-green-500" />
                  Último registro local
                </h2>

                <p className="mt-2 text-sm leading-6 text-[var(--muted)]">
                  Este bloque sale del navegador del usuario. Sirve para verificar qué pasó
                  en la última captura desde el frontend.
                </p>

                {localMetric ? (
                  <div className="mt-5 space-y-3">
                    <div className="rounded-2xl bg-[var(--card-strong)] p-4">
                      <p className="text-xs uppercase tracking-widest text-[var(--muted)]">
                        Imagen ID
                      </p>

                      <p className="mt-1 text-sm font-semibold">
                        {localMetric.imagenId ?? "Sin dato"}
                      </p>
                    </div>

                    <div className="rounded-2xl bg-[var(--card-strong)] p-4">
                      <p className="text-xs uppercase tracking-widest text-[var(--muted)]">
                        Conteo IA / corregido
                      </p>

                      <p className="mt-1 text-sm font-semibold">
                        IA: {localMetric.conteoIA ?? "Sin dato"} · Corregido:{" "}
                        {localMetric.conteoCorregido ?? "Sin dato"}
                      </p>
                    </div>

                    <div className="rounded-2xl bg-[var(--card-strong)] p-4">
                      <p className="text-xs uppercase tracking-widest text-[var(--muted)]">
                        Feedback enviado
                      </p>

                      <p className="mt-1 text-sm font-semibold">
                        {localMetric.feedbackEnviado ? "Sí" : "No"}
                      </p>
                    </div>

                    <div className="rounded-2xl bg-[var(--card-strong)] p-4">
                      <p className="text-xs uppercase tracking-widest text-[var(--muted)]">
                        Fecha local
                      </p>

                      <p className="mt-1 text-sm font-semibold">
                        {new Date(localMetric.fecha).toLocaleString("es-BO")}
                      </p>
                    </div>
                  </div>
                ) : (
                  <p className="mt-5 rounded-2xl bg-[var(--card-strong)] p-4 text-sm text-[var(--muted)]">
                    Todavía no hay métrica local. Analiza una imagen desde la pantalla Cámara IA.
                  </p>
                )}
              </div>

              <div className="glass-card rounded-[32px] p-6">
                <h2 className="flex items-center gap-2 text-xl font-semibold tracking-tight">
                  <ImageIcon className="h-5 w-5 text-[var(--primary-strong)]" />
                  Última imagen analizada
                </h2>

                {serverMetric?.imagen_url ? (
                  <div className="mt-5">
                    <div className="overflow-hidden rounded-[28px] bg-[var(--card-strong)] ring-1 ring-black/5 dark:ring-white/10">
                      <img
                        src={serverMetric.imagen_url}
                        alt="Última imagen procesada por IA"
                        className="h-[360px] w-full object-cover"
                      />
                    </div>

                    <div className="mt-4 rounded-2xl bg-[var(--card-strong)] p-4">
                      <p className="text-xs uppercase tracking-widest text-[var(--muted)]">
                        Observación IA
                      </p>

                      <p className="mt-2 text-sm leading-6">
                        {serverMetric.notas_ia || "Sin observación técnica."}
                      </p>
                    </div>
                  </div>
                ) : (
                  <p className="mt-5 rounded-2xl bg-[var(--card-strong)] p-4 text-sm text-[var(--muted)]">
                    No hay imagen disponible.
                  </p>
                )}
              </div>
            </div>
          </div>
        </PageContainer>
      </AppShell>
    </RouteGuard>
  );
}