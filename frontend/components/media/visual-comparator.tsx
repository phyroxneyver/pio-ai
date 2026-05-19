"use client";

import { useMemo } from "react";
import { Eye, Sparkles } from "lucide-react";
import type { IAVisualDetection } from "@/types/media";
import {
  EMPTY_IA_COUNTS,
  IA_CATEGORIES,
  countDetectionsByCategory,
  getIACountDifference,
  normalizeDetectionLabel,
  totalIACounts,
  type IACategoryKey,
  type IACounts,
} from "@/lib/ia-counts";

type VisualComparatorProps = {
  imageUrl: string;
  detections: IAVisualDetection[];
  iaCounts: IACounts;
  correctedCounts: IACounts;
};

const MARKER_STYLES: Record<IACategoryKey, string> = {
  pollitos: "border-yellow-300 bg-yellow-400/25 shadow-[0_0_20px_rgba(250,204,21,0.45)]",
  gallinas: "border-sky-300 bg-sky-400/25 shadow-[0_0_20px_rgba(56,189,248,0.35)]",
  huevos: "border-emerald-300 bg-emerald-400/25 shadow-[0_0_20px_rgba(52,211,153,0.35)]",
};

const DOT_STYLES: Record<IACategoryKey, string> = {
  pollitos: "bg-yellow-300 shadow-[0_0_10px_rgba(250,204,21,0.9)]",
  gallinas: "bg-sky-300 shadow-[0_0_10px_rgba(56,189,248,0.8)]",
  huevos: "bg-emerald-300 shadow-[0_0_10px_rgba(52,211,153,0.8)]",
};

function buildFallbackDetections(counts: IACounts): IAVisualDetection[] {
  const total = Math.min(totalIACounts(counts), 90);
  if (total <= 0) return [];

  const cols = Math.ceil(Math.sqrt(total));
  const rows = Math.ceil(total / cols);
  const points: IAVisualDetection[] = [];

  IA_CATEGORIES.forEach((category) => {
    const amount = Math.min(counts[category.key], 90 - points.length);

    for (let i = 0; i < amount; i += 1) {
      const index = points.length;
      const col = index % cols;
      const row = Math.floor(index / cols);
      const baseX = (col + 1) / (cols + 1);
      const baseY = (row + 1) / (rows + 1);
      const jitterX = Math.sin(index * 7.13) * 0.025;
      const jitterY = Math.cos(index * 5.91) * 0.025;

      points.push({
        x: Math.max(0.06, Math.min(0.94, baseX + jitterX)),
        y: Math.max(0.06, Math.min(0.94, baseY + jitterY)),
        label: category.key,
        confidence: null,
      });
    }
  });

  return points;
}

export function VisualComparator({
  imageUrl,
  detections,
  iaCounts,
  correctedCounts,
}: VisualComparatorProps) {
  const points = useMemo(() => {
    if (detections.length > 0) return detections;
    return buildFallbackDetections(iaCounts);
  }, [detections, iaCounts]);

  const detectionCounts = useMemo(() => countDetectionsByCategory(points), [points]);
  const totalIA = totalIACounts(iaCounts);
  const totalCorrected = totalIACounts(correctedCounts);
  const totalDifference = totalCorrected - totalIA;
  const differences = getIACountDifference(correctedCounts, iaCounts);
  const isCorrected = totalDifference !== 0 || IA_CATEGORIES.some((category) => differences[category.key] !== 0);

  return (
    <div className="glass-card rounded-[32px] p-5 shadow-[0_18px_40px_rgba(0,0,0,0.06)]">
      <div className="mb-4 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm font-medium text-[var(--muted)]">
            Comparador visual
          </p>
          <h3 className="mt-1 flex items-center gap-2 text-xl font-semibold tracking-tight">
            <Sparkles className="h-5 w-5 text-[var(--primary-strong)]" />
            Resultado por categoría
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
            ? `Corrección total: ${totalDifference > 0 ? "+" : ""}${totalDifference}`
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
              alt="Foto con detecciones resaltadas por la IA"
              className="h-[320px] w-full object-cover"
            />

            <div className="absolute inset-0">
              {points.map((point, index) => {
                const category = normalizeDetectionLabel(point.label) ?? "pollitos";

                return (
                  <div
                    key={`${point.x}-${point.y}-${point.label}-${index}`}
                    className={`absolute flex h-8 w-8 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full border-2 ${MARKER_STYLES[category]}`}
                    style={{
                      left: `${point.x * 100}%`,
                      top: `${point.y * 100}%`,
                    }}
                    title={`${IA_CATEGORIES.find((item) => item.key === category)?.title ?? "Detección"} ${index + 1}`}
                  >
                    <span className={`h-2.5 w-2.5 rounded-full ${DOT_STYLES[category]}`} />
                  </div>
                );
              })}
            </div>

            <div className="absolute left-3 top-3 inline-flex items-center gap-2 rounded-full bg-black/65 px-3 py-1 text-xs font-semibold text-white backdrop-blur">
              <Eye className="h-3.5 w-3.5" />
              Detecciones IA
            </div>
          </div>
        </div>
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        {IA_CATEGORIES.map((category) => (
          <div
            key={category.key}
            className="rounded-2xl bg-[var(--card-strong)] p-4 ring-1 ring-black/5 dark:ring-white/10"
          >
            <p className="text-xs uppercase tracking-widest text-[var(--muted)]">
              {category.title}
            </p>
            <p className="mt-1 text-2xl font-black">
              {iaCounts[category.key]}
            </p>
            <p className="mt-1 text-xs text-[var(--muted)]">
              Marcas: {detectionCounts[category.key] ?? EMPTY_IA_COUNTS[category.key]}
            </p>
          </div>
        ))}
      </div>

      {detections.length === 0 && totalIA > 0 ? (
        <p className="mt-3 rounded-2xl bg-yellow-500/10 px-4 py-3 text-xs leading-5 text-yellow-600 dark:text-yellow-300">
          La IA entregó conteos, pero no devolvió coordenadas exactas. Por eso se muestra una guía visual aproximada por categoría.
        </p>
      ) : null}
    </div>
  );
}
