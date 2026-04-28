"use client";

import { useMemo } from "react";
import { Eye, Sparkles } from "lucide-react";
import type { IAVisualDetection } from "@/types/media";

type VisualComparatorProps = {
  imageUrl: string;
  detections: IAVisualDetection[];
  iaCount: number;
  correctedCount: number;
};

function buildFallbackDetections(count: number): IAVisualDetection[] {
  if (count <= 0) return [];

  const safeCount = Math.min(count, 80);
  const cols = Math.ceil(Math.sqrt(safeCount));
  const rows = Math.ceil(safeCount / cols);
  const points: IAVisualDetection[] = [];

  for (let i = 0; i < safeCount; i += 1) {
    const col = i % cols;
    const row = Math.floor(i / cols);

    const baseX = (col + 1) / (cols + 1);
    const baseY = (row + 1) / (rows + 1);

    const jitterX = Math.sin(i * 7.13) * 0.025;
    const jitterY = Math.cos(i * 5.91) * 0.025;

    points.push({
      x: Math.max(0.06, Math.min(0.94, baseX + jitterX)),
      y: Math.max(0.06, Math.min(0.94, baseY + jitterY)),
      label: "pollito",
      confidence: null,
    });
  }

  return points;
}

export function VisualComparator({
  imageUrl,
  detections,
  iaCount,
  correctedCount,
}: VisualComparatorProps) {
  const points = useMemo(() => {
    if (detections.length > 0) return detections;
    return buildFallbackDetections(iaCount);
  }, [detections, iaCount]);

  const difference = correctedCount - iaCount;
  const isCorrected = difference !== 0;

  return (
    <div className="glass-card rounded-[32px] p-5 shadow-[0_18px_40px_rgba(0,0,0,0.06)]">
      <div className="mb-4 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm font-medium text-[var(--muted)]">
            Comparador visual
          </p>
          <h3 className="mt-1 flex items-center gap-2 text-xl font-semibold tracking-tight">
            <Sparkles className="h-5 w-5 text-[var(--primary-strong)]" />
            Antes y después del análisis
          </h3>
        </div>

        <span
          className={`w-fit rounded-full px-3 py-1 text-xs font-bold ${
            isCorrected
              ? "bg-orange-500/10 text-orange-500"
              : "bg-green-500/10 text-green-500"
          }`}
        >
          {isCorrected
            ? `Corrección: ${difference > 0 ? "+" : ""}${difference}`
            : "Sin corrección"}
        </span>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div>
          <div className="mb-2 flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-[0.2em] text-[var(--muted)]">
              Antes
            </span>
            <span className="text-xs text-[var(--muted)]">
              Foto original
            </span>
          </div>

          <div className="overflow-hidden rounded-[24px] bg-[var(--card-strong)] ring-1 ring-black/5 dark:ring-white/10">
            <img
              src={imageUrl}
              alt="Foto original antes del análisis"
              className="h-[320px] w-full object-cover"
            />
          </div>
        </div>

        <div>
          <div className="mb-2 flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-[0.2em] text-[var(--muted)]">
              Después IA
            </span>
            <span className="text-xs text-[var(--muted)]">
              {points.length} marca(s)
            </span>
          </div>

          <div className="relative overflow-hidden rounded-[24px] bg-[var(--card-strong)] ring-1 ring-black/5 dark:ring-white/10">
            <img
              src={imageUrl}
              alt="Foto con pollitos resaltados por la IA"
              className="h-[320px] w-full object-cover"
            />

            <div className="absolute inset-0">
              {points.map((point, index) => (
                <div
                  key={`${point.x}-${point.y}-${index}`}
                  className="absolute flex h-8 w-8 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full border-2 border-yellow-300 bg-yellow-400/25 shadow-[0_0_20px_rgba(250,204,21,0.45)]"
                  style={{
                    left: `${point.x * 100}%`,
                    top: `${point.y * 100}%`,
                  }}
                  title={`Pollito ${index + 1}`}
                >
                  <span className="h-2.5 w-2.5 rounded-full bg-yellow-300 shadow-[0_0_10px_rgba(250,204,21,0.9)]" />
                </div>
              ))}
            </div>

            <div className="absolute left-3 top-3 inline-flex items-center gap-2 rounded-full bg-black/65 px-3 py-1 text-xs font-semibold text-white backdrop-blur">
              <Eye className="h-3.5 w-3.5" />
              Pollitos resaltados
            </div>
          </div>
        </div>
      </div>

      {detections.length === 0 && iaCount > 0 ? (
        <p className="mt-3 rounded-2xl bg-yellow-500/10 px-4 py-3 text-xs leading-5 text-yellow-600 dark:text-yellow-300">
          La IA entregó el conteo, pero no devolvió coordenadas exactas. Por eso se muestra una guía visual aproximada.
        </p>
      ) : null}
    </div>
  );
}