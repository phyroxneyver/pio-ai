"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  AlertTriangle,
  Bird,
  Camera,
  CheckCircle2,
  CircleDot,
  ImagePlus,
  Minus,
  Plus,
  RefreshCw,
  RotateCcw,
  Send,
  ShieldCheck,
  Scan,
  UploadCloud,
} from "lucide-react";

import { RouteGuard } from "@/components/auth/route-guard";
import { AppHeader } from "@/components/header/app-header";
import { AppShell } from "@/components/layout/app-shell";
import { PageContainer } from "@/components/layout/page-container";
import { Sidebar } from "@/components/layout/sidebar";
import { TabBar } from "@/components/layout/tab-bar";
import { Spinner } from "@/components/feedback/spinner";
import { ErrorAlert } from "@/components/feedback/error-alert";
import { CameraInput } from "@/components/media/camera-input";
import { PhotoPreview } from "@/components/media/photo-preview";
import { VisualComparator } from "@/components/media/visual-comparator";
import { compressImage, formatBytes } from "@/lib/image-compression";
import { useToast } from "@/components/ui/toast-provider";
import { API_URL, enviarFeedbackIA, fetchWithAuth } from "@/lib/api";
import {
  EMPTY_IA_COUNTS,
  IA_CATEGORIES,
  buildCountsNote,
  formatIACounts,
  getIACountDifference,
  hasIACountDifference,
  normalizeIACounts,
  totalIACounts,
  type IACategoryKey,
  type IACounts,
} from "@/lib/ia-counts";
import type {
  CaptureStage,
  IAVisualDetection,
  ImageMeta,
  LastAIMetrics,
} from "@/types/media";

const LAST_AI_METRICS_KEY = "pioai_last_ai_metrics";

type ResultadoIA = {
  id: number;
  imagen_id: number;
  conteo_pollitos: number | null;
  conteo_gallinas?: number | null;
  conteo_huevos?: number | null;
  conteo_pollos?: number | null;
  confianza: string | null;
  estado: string;
  procesado_at: string | null;
  created_at?: string;
  error_detalle: string | null;
  duracion_ms?: number | null;
  precision_estimada?: number | null;
  notas_ia?: string | null;
  detecciones?: IAVisualDetection[];
  conteos?: unknown;
  conteos_ia?: unknown;
};

type UploadStageDetail = "idle" | "subiendo" | "procesando" | "finalizado";

type Ave = {
  id: number;
  tipo: string;
  cantidad: number;
  notas?: string;
  fecha_ingreso?: string;
};

function confianzaComoPrecision(confianza: string | null | undefined) {
  if (confianza === "alta") return 0.92;
  if (confianza === "media") return 0.72;
  if (confianza === "baja") return 0.45;
  return null;
}

function saveLastMetrics(metrics: LastAIMetrics) {
  if (typeof window === "undefined") return;
  localStorage.setItem(LAST_AI_METRICS_KEY, JSON.stringify(metrics));
}

function updateLastMetrics(partial: Partial<LastAIMetrics>) {
  if (typeof window === "undefined") return;

  const raw = localStorage.getItem(LAST_AI_METRICS_KEY);
  if (!raw) return;

  try {
    const current = JSON.parse(raw) as LastAIMetrics;
    localStorage.setItem(LAST_AI_METRICS_KEY, JSON.stringify({ ...current, ...partial }));
  } catch {
    return;
  }
}

function normalizeResultadoIA(data: ResultadoIA): ResultadoIA {
  const counts = normalizeIACounts(data);

  return {
    ...data,
    conteo_pollitos: counts.pollitos,
    conteo_gallinas: counts.gallinas,
    conteo_huevos: counts.huevos,
    detecciones: Array.isArray(data.detecciones) ? data.detecciones : [],
  };
}

function copyCounts(counts: IACounts): IACounts {
  return { ...counts };
}

function countSummaryLines(counts: IACounts) {
  return IA_CATEGORIES.map((category) => `${category.title}: ${counts[category.key]}`).join(" · ");
}

export default function CapturaPage() {
  const { showToast } = useToast();
  const analysisTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const [stage, setStage] = useState<CaptureStage>("idle");
  const [uploadStageDetail, setUploadStageDetail] = useState<UploadStageDetail>("idle");
  const [cameraNonce, setCameraNonce] = useState(0);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState("");
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState("");

  const [originalMeta, setOriginalMeta] = useState<ImageMeta | null>(null);
  const [compressedMeta, setCompressedMeta] = useState<ImageMeta | null>(null);

  const [imagenId, setImagenId] = useState<number | null>(null);
  const [resultadoIA, setResultadoIA] = useState<ResultadoIA | null>(null);
  const [validatedCounts, setValidatedCounts] = useState<IACounts>({ ...EMPTY_IA_COUNTS });

  const [analizando, setAnalizando] = useState(false);
  const [timerExcedido, setTimerExcedido] = useState(false);
  const [correctionReason, setCorrectionReason] = useState("");
  const [feedbackEnviado, setFeedbackEnviado] = useState(false);
  const [enviandoFeedback, setEnviandoFeedback] = useState(false);

  const [confirmado, setConfirmado] = useState(false);
  const [causaBaja, setCausaBaja] = useState("");
  const [mostrarCausaBaja, setMostrarCausaBaja] = useState(false);

  useEffect(() => {
    if (!selectedFile) {
      setPreviewUrl("");
      return;
    }

    const url = URL.createObjectURL(selectedFile);
    setPreviewUrl(url);

    return () => URL.revokeObjectURL(url);
  }, [selectedFile]);

  useEffect(() => {
    return () => {
      if (analysisTimerRef.current) clearTimeout(analysisTimerRef.current);
    };
  }, []);

  const iaCounts = useMemo(
    () => (resultadoIA ? normalizeIACounts(resultadoIA) : { ...EMPTY_IA_COUNTS }),
    [resultadoIA],
  );

  const totalIA = totalIACounts(iaCounts);
  const totalValidated = totalIACounts(validatedCounts);
  const countDifference = getIACountDifference(validatedCounts, iaCounts);
  const totalDifference = totalValidated - totalIA;
  const hasCorrection = Boolean(resultadoIA && hasIACountDifference(validatedCounts, iaCounts));
  const hasImage = Boolean(selectedFile && previewUrl);
  const iaLabel = formatIACounts(iaCounts);

  const stageLabel = useMemo(() => {
    switch (stage) {
      case "idle":
        return "Sin imagen cargada";
      case "preview":
        return "Imagen lista para revisar";
      case "compressing":
        return "Optimizando imagen";
      case "uploading":
        if (uploadStageDetail === "subiendo") return "Subiendo imagen";
        if (uploadStageDetail === "procesando") return "Procesando con IA";
        if (uploadStageDetail === "finalizado") return "Finalizado";
        return "Subiendo imagen";
      case "success":
        return "Análisis completado";
      case "error":
        return "La subida o el análisis falló";
      default:
        return "Sin estado";
    }
  }, [stage, uploadStageDetail]);

  const progressLabel = useMemo(() => {
    if (uploadStageDetail === "subiendo") return "📤 Subiendo imagen...";
    if (uploadStageDetail === "procesando") return "🤖 Detectando pollos, gallinas y huevos...";
    if (uploadStageDetail === "finalizado") return "✅ Finalizado";
    return "Procesando...";
  }, [uploadStageDetail]);

  function handleCapture(file: File) {
    setSelectedFile(file);
    setCompressedMeta(null);
    setProgress(0);
    setError("");
    setResultadoIA(null);
    setImagenId(null);
    setConfirmado(false);
    setCausaBaja("");
    setCorrectionReason("");
    setMostrarCausaBaja(false);
    setFeedbackEnviado(false);
    setValidatedCounts({ ...EMPTY_IA_COUNTS });
    setStage("preview");
    setUploadStageDetail("idle");

    setOriginalMeta({
      name: file.name,
      size: file.size,
      format: file.type || "image/*",
    });

    showToast({
      type: "info",
      title: "Fotografía cargada",
      description: "Revisa la imagen antes de enviarla.",
    });
  }

  function resetCapture() {
    if (analysisTimerRef.current) {
      clearTimeout(analysisTimerRef.current);
      analysisTimerRef.current = null;
    }

    setSelectedFile(null);
    setCompressedMeta(null);
    setOriginalMeta(null);
    setProgress(0);
    setError("");
    setStage("idle");
    setUploadStageDetail("idle");
    setImagenId(null);
    setResultadoIA(null);
    setValidatedCounts({ ...EMPTY_IA_COUNTS });
    setAnalizando(false);
    setTimerExcedido(false);
    setConfirmado(false);
    setCausaBaja("");
    setCorrectionReason("");
    setMostrarCausaBaja(false);
    setFeedbackEnviado(false);
  }

  async function clearCameraCache() {
    try {
      if ("caches" in window) {
        const keys = await window.caches.keys();
        await Promise.all(
          keys
            .filter((key) => key.includes("pio-ai") || key.includes("camera") || key.includes("captura"))
            .map((key) => window.caches.delete(key)),
        );
      }
    } catch {
      // Si el navegador no permite limpiar caché, igual reiniciamos la captura.
    }

    setCameraNonce((current) => current + 1);
  }

  async function handleSmartRetry() {
    resetCapture();
    await clearCameraCache();

    showToast({
      type: "info",
      title: "Listo para reintentar",
      description: "Se limpió la captura anterior. Toma una nueva foto.",
    });
  }

  async function subirImagenReal(fileToUpload: File): Promise<number> {
    const token = localStorage.getItem("pioai_token");
    const formData = new FormData();
    formData.append("file", fileToUpload, fileToUpload.name);

    const res = await fetch(`${API_URL}/imagenes/upload`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Error al subir la imagen al servidor.");
    }

    const data = await res.json();
    if (!data.id) throw new Error("El servidor no devolvió el ID de la imagen.");

    return Number(data.id);
  }

  async function analizarConIA(id: number): Promise<ResultadoIA> {
    setAnalizando(true);
    setTimerExcedido(false);

    const startedAt = performance.now();
    analysisTimerRef.current = setTimeout(() => setTimerExcedido(true), 5000);

    try {
      const res = await fetchWithAuth(`/imagenes/${id}/analizar`, { method: "POST" });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Error al analizar la imagen.");
      }

      const data = (await res.json()) as ResultadoIA;
      const frontendDuration = Math.round(performance.now() - startedAt);
      const resultWithTiming = normalizeResultadoIA({
        ...data,
        duracion_ms: data.duracion_ms ?? frontendDuration,
      });

      if (resultWithTiming.estado === "error") {
        throw new Error(resultWithTiming.error_detalle || "La IA no pudo analizar esta imagen.");
      }

      return resultWithTiming;
    } finally {
      if (analysisTimerRef.current) {
        clearTimeout(analysisTimerRef.current);
        analysisTimerRef.current = null;
      }
      setAnalizando(false);
    }
  }

  async function revisarBajaContraUltimoConteo(resultado: ResultadoIA) {
    try {
      const avesRes = await fetchWithAuth("/aves");
      const aves = (await avesRes.json()) as Ave[];

      if (!Array.isArray(aves) || aves.length === 0) return;

      const pollitos = aves.filter((ave) => ave.tipo === "pollito");
      if (pollitos.length === 0) return;

      const ultimo = pollitos[pollitos.length - 1];
      const conteoActual = normalizeIACounts(resultado).pollitos;

      if (conteoActual < ultimo.cantidad) setMostrarCausaBaja(true);
    } catch {
      setMostrarCausaBaja(false);
    }
  }

  async function handleCompressAndUpload() {
    if (!selectedFile) return;

    try {
      setStage("compressing");
      setError("");
      setProgress(0);
      setResultadoIA(null);
      setConfirmado(false);
      setFeedbackEnviado(false);
      setCorrectionReason("");
      setValidatedCounts({ ...EMPTY_IA_COUNTS });

      const result = await compressImage(selectedFile, {
        maxWidth: 1600,
        maxHeight: 1600,
        quality: 0.72,
        mimeType: "image/jpeg",
      });

      setCompressedMeta(result.meta);
      setStage("uploading");
      setUploadStageDetail("subiendo");
      setProgress(25);

      const id = await subirImagenReal(result.file);

      setImagenId(id);
      setUploadStageDetail("procesando");
      setProgress(65);

      const resultado = await analizarConIA(id);
      const counts = normalizeIACounts(resultado);
      const total = totalIACounts(counts);

      setUploadStageDetail("finalizado");
      setProgress(100);
      setResultadoIA(resultado);
      setValidatedCounts(copyCounts(counts));
      setStage("success");

      await revisarBajaContraUltimoConteo(resultado);

      saveLastMetrics({
        imagenId: id,
        resultadoId: resultado.id,
        conteoIA: total,
        conteoCorregido: total,
        diferencia: 0,
        confianza: resultado.confianza ?? null,
        precisionEstimada: resultado.precision_estimada ?? confianzaComoPrecision(resultado.confianza),
        duracionMs: resultado.duracion_ms ?? null,
        estado: resultado.estado,
        feedbackEnviado: false,
        fecha: new Date().toISOString(),
        conteosIA: counts,
        conteosCorregidos: counts,
      });

      showToast({
        type: "success",
        title: "Análisis completado",
        description: `${total} elemento(s) detectados: ${formatIACounts(counts)}.`,
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : "No se pudo procesar la imagen.";

      setStage("error");
      setError(message);

      saveLastMetrics({
        imagenId,
        resultadoId: null,
        conteoIA: null,
        conteoCorregido: null,
        diferencia: null,
        confianza: null,
        precisionEstimada: null,
        duracionMs: null,
        estado: "error",
        feedbackEnviado: false,
        fecha: new Date().toISOString(),
      });

      showToast({ type: "error", title: "Error", description: message });
    }
  }

  function updateValidatedCount(key: IACategoryKey, amount: number) {
    setValidatedCounts((current) => ({
      ...current,
      [key]: Math.max(0, current[key] + amount),
    }));
  }

  async function handleEnviarFeedback(tipo: "correccion" | "fallida") {
    if (!imagenId) {
      showToast({
        type: "error",
        title: "Sin imagen",
        description: "Primero debes subir una imagen.",
      });
      return false;
    }

    if (tipo === "fallida" && correctionReason.trim().length < 4) {
      showToast({
        type: "error",
        title: "Agrega una observación",
        description: "Explica brevemente por qué esta foto falló.",
      });
      return false;
    }

    try {
      setEnviandoFeedback(true);

      const motivo = [
        correctionReason.trim(),
        buildCountsNote("IA", iaCounts),
        buildCountsNote("Validado", validatedCounts),
      ]
        .filter(Boolean)
        .join(" | ");

      await enviarFeedbackIA(imagenId, {
        conteo_corregido: totalValidated,
        tipo_feedback: tipo,
        motivo:
          motivo ||
          (tipo === "fallida"
            ? "Foto marcada como fallida por el trabajador."
            : "Conteo corregido manualmente por el trabajador."),
      });

      setFeedbackEnviado(true);

      updateLastMetrics({
        conteoCorregido: totalValidated,
        diferencia: totalDifference,
        feedbackEnviado: true,
        conteosCorregidos: validatedCounts,
      });

      showToast({
        type: "success",
        title: "Feedback enviado",
        description: "La foto quedó marcada para mejora futura del modelo.",
      });

      return true;
    } catch (err) {
      const message = err instanceof Error ? err.message : "No se pudo enviar el feedback.";

      showToast({
        type: "error",
        title: "Error al enviar feedback",
        description: message,
      });

      return false;
    } finally {
      setEnviandoFeedback(false);
    }
  }

  async function handleConfirmar() {
    if (!resultadoIA) return;

    try {
      if (hasCorrection && !feedbackEnviado) {
        const feedbackOk = await handleEnviarFeedback("correccion");
        if (!feedbackOk) return;
      }

      const notas = [
        "Conteo validado desde Cámara IA.",
        buildCountsNote("IA", iaCounts),
        buildCountsNote("Validado", validatedCounts),
        `Confianza=${resultadoIA.confianza ?? "sin dato"}.`,
        resultadoIA.duracion_ms ? `Tiempo IA=${resultadoIA.duracion_ms}ms.` : "",
        correctionReason ? `Corrección: ${correctionReason}.` : "",
        causaBaja ? `Causa de baja: ${causaBaja}.` : "",
      ]
        .filter(Boolean)
        .join(" ");

      let gallinaAveId: number | null = null;

      if (validatedCounts.pollitos > 0) {
        await fetchWithAuth("/aves", {
          method: "POST",
          body: JSON.stringify({
            tipo: "pollito",
            cantidad: validatedCounts.pollitos,
            notas,
          }),
        });
      }

      if (validatedCounts.gallinas > 0) {
        const res = await fetchWithAuth("/aves", {
          method: "POST",
          body: JSON.stringify({
            tipo: "gallina",
            cantidad: validatedCounts.gallinas,
            notas,
          }),
        });

        const created = await res.json().catch(() => null);
        gallinaAveId = created?.id ? Number(created.id) : null;
      }

      if (validatedCounts.huevos > 0 && gallinaAveId) {
        await fetchWithAuth("/produccion-huevos", {
          method: "POST",
          body: JSON.stringify({
            ave_id: gallinaAveId,
            cantidad_huevos: validatedCounts.huevos,
            notas,
          }),
        });
      }

      setConfirmado(true);

      updateLastMetrics({
        conteoCorregido: totalValidated,
        diferencia: totalDifference,
        conteosCorregidos: validatedCounts,
      });

      const eggsWithoutLot = validatedCounts.huevos > 0 && !gallinaAveId;

      showToast({
        type: "success",
        title: "Conteo guardado",
        description: eggsWithoutLot
          ? "Se validó el conteo. Los huevos se mostraron en el resultado, pero no se registraron en producción porque no hay gallina/lote asociado."
          : "El conteo validado se guardó correctamente.",
      });
    } catch {
      showToast({
        type: "error",
        title: "Error",
        description: "No se pudo guardar el conteo validado.",
      });
    }
  }

  return (
    <RouteGuard>
      <AppShell header={<AppHeader />} sidebar={<Sidebar />} tabBar={<TabBar />}>
        <PageContainer>
          <section className="grid gap-5 xl:grid-cols-[1.15fr_0.85fr]">
            <div className="min-w-0 space-y-5">
              <div className="glass-card rounded-[32px] p-5 shadow-[0_20px_50px_rgba(0,0,0,0.07)] sm:p-8">
                <span className="inline-flex items-center gap-2 rounded-full bg-[var(--egg)] px-3 py-1 text-xs font-semibold text-[var(--primary-strong)]">
                  <Camera className="h-3.5 w-3.5" />
                  Cámara IA multicategoría
                </span>

                <h2 className="mt-4 text-3xl font-semibold leading-tight tracking-tight sm:text-4xl">
                  Escanea una foto y valida pollos, gallinas y huevos
                </h2>

                <p className="mt-4 text-sm leading-7 text-[var(--muted)] sm:text-base">
                  La pantalla ahora separa los resultados por categoría. Si la imagen tiene una mezcla de huevos,
                  pollos y gallinas, podrás ver y ajustar cada conteo sin tocar el entrenamiento del modelo.
                </p>

                <div className="mt-6">
                  <CameraInput
                    key={cameraNonce}
                    onCapture={handleCapture}
                    disabled={stage === "compressing" || stage === "uploading" || analizando}
                  />
                </div>
              </div>

              {analizando ? (
                <div className="glass-card rounded-[32px] p-8 text-center">
                  <div className="relative mx-auto mb-4 h-20 w-20">
                    <div className="absolute inset-0 animate-ping rounded-full border-4 border-[var(--egg)] opacity-30" />
                    <div className="absolute inset-2 animate-ping rounded-full border-4 border-[var(--egg)] opacity-50" />
                    <div className="flex h-20 w-20 items-center justify-center">
                      <Scan className="h-8 w-8 animate-pulse text-[var(--primary-strong)]" />
                    </div>
                  </div>

                  <p className="text-sm font-semibold">Analizando imagen con IA...</p>
                  <p className="mt-1 text-xs text-[var(--muted)]">
                    Buscando pollos/pollitos, gallinas y huevos.
                  </p>

                  {timerExcedido ? (
                    <p className="mt-2 text-xs font-semibold text-orange-500">
                      ⚠️ La IA está tardando más de 5 segundos. Espera un momento o vuelve a intentar.
                    </p>
                  ) : null}
                </div>
              ) : null}

              {stage === "compressing" ? <Spinner label="Optimizando imagen antes de enviarla..." /> : null}

              {hasImage && originalMeta && !resultadoIA ? (
                <PhotoPreview
                  previewUrl={previewUrl}
                  originalMeta={originalMeta}
                  compressedMeta={compressedMeta}
                  onRemove={resetCapture}
                />
              ) : null}

              {hasImage && resultadoIA ? (
                <VisualComparator
                  imageUrl={previewUrl}
                  detections={resultadoIA.detecciones || []}
                  iaCounts={iaCounts}
                  correctedCounts={validatedCounts}
                />
              ) : null}

              {!hasImage && !analizando ? (
                <div className="glass-card rounded-[32px] p-8 text-center">
                  <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-[24px] bg-[var(--egg)]">
                    <ImagePlus className="h-7 w-7 text-[var(--primary-strong)]" />
                  </div>

                  <h3 className="mt-5 text-xl font-semibold tracking-tight">
                    Aún no hay fotografía
                  </h3>

                  <p className="mt-2 text-sm text-[var(--muted)]">
                    Abre la cámara o selecciona una imagen para continuar.
                  </p>
                </div>
              ) : null}

              {(stage === "uploading" || stage === "success") && hasImage ? (
                <div className="rounded-[24px] bg-[var(--card-strong)] p-4 ring-1 ring-black/5 dark:ring-white/10">
                  <div className="mb-3 flex items-center justify-between gap-3">
                    <p className="text-sm font-medium">{progressLabel}</p>
                    <span className="text-sm font-semibold text-[var(--primary-strong)]">
                      {progress}%
                    </span>
                  </div>

                  <div className="h-3 w-full overflow-hidden rounded-full bg-black/5 dark:bg-white/10">
                    <div
                      className="h-full rounded-full bg-[var(--primary)] transition-all duration-500"
                      style={{ width: `${progress}%` }}
                    />
                  </div>
                </div>
              ) : null}

              {stage === "error" && error ? (
                <div className="space-y-4">
                  <ErrorAlert title="Error al procesar" message={error} />

                  {imagenId ? (
                    <div className="glass-card rounded-[32px] p-5">
                      <h3 className="text-lg font-semibold">Marcar esta foto como fallida</h3>
                      <p className="mt-2 text-sm leading-6 text-[var(--muted)]">
                        Si la foto llegó al servidor pero la IA falló, puedes enviarla como ejemplo fallido
                        para revisión futura.
                      </p>

                      <textarea
                        value={correctionReason}
                        onChange={(event) => setCorrectionReason(event.target.value)}
                        placeholder="Ej: imagen borrosa, animales amontonados, poca luz..."
                        rows={3}
                        className="mt-4 w-full resize-none rounded-2xl border border-black/10 bg-[var(--card-strong)] px-4 py-3 text-sm outline-none dark:border-white/10"
                      />

                      <div className="mt-4 flex flex-col gap-3 sm:flex-row">
                        <button
                          onClick={() => handleEnviarFeedback("fallida")}
                          disabled={enviandoFeedback}
                          className="primary-button inline-flex min-h-[44px] items-center justify-center gap-2 rounded-2xl px-4 py-3 text-sm font-semibold disabled:opacity-60"
                        >
                          <Send className="h-4 w-4" />
                          Enviar foto fallida
                        </button>

                        <button
                          onClick={handleSmartRetry}
                          className="secondary-button inline-flex min-h-[44px] items-center justify-center gap-2 rounded-2xl px-4 py-3 text-sm font-medium"
                        >
                          <RotateCcw className="h-4 w-4" />
                          Volver a intentar
                        </button>
                      </div>
                    </div>
                  ) : null}
                </div>
              ) : null}

              {resultadoIA && stage === "success" ? (
                <div className="glass-card space-y-5 rounded-[32px] p-6">
                  <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
                    <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[var(--egg)]">
                      <Bird className="h-6 w-6 text-[var(--primary-strong)]" />
                    </div>

                    <div className="min-w-0 flex-1">
                      <p className="text-sm text-[var(--muted)]">Resultado de la IA</p>
                      <p className="text-2xl font-black">{iaLabel}</p>
                    </div>

                    <span
                      className={`w-fit rounded-full px-3 py-1 text-xs font-bold ${
                        resultadoIA.confianza === "alta"
                          ? "bg-green-500/10 text-green-500"
                          : resultadoIA.confianza === "media"
                            ? "bg-yellow-500/10 text-yellow-500"
                            : "bg-red-500/10 text-red-500"
                      }`}
                    >
                      Confianza {resultadoIA.confianza || "sin dato"}
                    </span>
                  </div>

                  <div className="grid gap-3 md:grid-cols-3">
                    {IA_CATEGORIES.map((category) => {
                      const diff = countDifference[category.key];

                      return (
                        <div
                          key={category.key}
                          className="rounded-[28px] bg-[var(--card-strong)] p-4 ring-1 ring-black/5 dark:ring-white/10"
                        >
                          <p className="text-xs uppercase tracking-widest text-[var(--muted)]">
                            {category.title}
                          </p>
                          <p className="mt-1 text-3xl font-black">
                            {iaCounts[category.key]}
                          </p>
                          <p className="mt-1 text-xs leading-5 text-[var(--muted)]">
                            {category.description}
                          </p>

                          <div className="mt-4 flex items-center justify-between gap-2 rounded-2xl bg-[var(--background)] p-2 ring-1 ring-black/5 dark:ring-white/10">
                            <button
                              onClick={() => updateValidatedCount(category.key, -1)}
                              className="secondary-button flex h-10 w-10 items-center justify-center rounded-xl"
                              aria-label={`Restar ${category.title}`}
                            >
                              <Minus className="h-4 w-4" />
                            </button>

                            <div className="text-center">
                              <p className="text-[11px] text-[var(--muted)]">Validado</p>
                              <p className="text-2xl font-black">
                                {validatedCounts[category.key]}
                              </p>
                            </div>

                            <button
                              onClick={() => updateValidatedCount(category.key, 1)}
                              className="secondary-button flex h-10 w-10 items-center justify-center rounded-xl"
                              aria-label={`Sumar ${category.title}`}
                            >
                              <Plus className="h-4 w-4" />
                            </button>
                          </div>

                          {diff !== 0 ? (
                            <p className="mt-3 rounded-xl bg-orange-500/10 px-3 py-2 text-xs font-semibold text-orange-500">
                              Corrección {diff > 0 ? "+" : ""}{diff}
                            </p>
                          ) : null}
                        </div>
                      );
                    })}
                  </div>

                  {hasCorrection ? (
                    <div className="rounded-2xl bg-orange-500/10 p-4">
                      <p className="text-sm font-semibold text-orange-500">
                        Se detectó una corrección manual total de {totalDifference > 0 ? `+${totalDifference}` : totalDifference}.
                      </p>

                      <textarea
                        value={correctionReason}
                        onChange={(event) => setCorrectionReason(event.target.value)}
                        placeholder="Explica la corrección. Ej: había huevos ocultos, una gallina quedó fuera del cuadro, etc."
                        rows={3}
                        className="mt-3 w-full resize-none rounded-2xl border border-black/10 bg-[var(--card-strong)] px-4 py-3 text-sm outline-none dark:border-white/10"
                      />

                      <button
                        onClick={() => handleEnviarFeedback("correccion")}
                        disabled={feedbackEnviado || enviandoFeedback}
                        className="mt-3 inline-flex min-h-[44px] items-center justify-center gap-2 rounded-2xl bg-orange-500 px-4 py-3 text-sm font-semibold text-white disabled:opacity-60"
                      >
                        <Send className="h-4 w-4" />
                        {feedbackEnviado ? "Feedback enviado" : "Enviar corrección"}
                      </button>
                    </div>
                  ) : (
                    <div className="flex items-center gap-2 rounded-2xl bg-green-500/10 px-4 py-3 text-sm font-semibold text-green-500">
                      <ShieldCheck className="h-4 w-4" />
                      El trabajador no corrigió el conteo de la IA.
                    </div>
                  )}

                  {mostrarCausaBaja && !confirmado ? (
                    <div className="rounded-2xl border border-orange-500/20 bg-orange-500/10 p-4">
                      <div className="mb-3 flex items-center gap-2">
                        <AlertTriangle className="h-4 w-4 text-orange-500" />
                        <p className="text-sm font-semibold text-orange-500">
                          El conteo de pollos/pollitos bajó respecto al registro anterior
                        </p>
                      </div>

                      <label className="text-xs uppercase tracking-widest text-[var(--muted)]">
                        Causa de la baja
                      </label>

                      <textarea
                        value={causaBaja}
                        onChange={(event) => setCausaBaja(event.target.value)}
                        placeholder="Ej: enfermedad, traslado, venta, mortalidad..."
                        rows={2}
                        className="mt-2 w-full resize-none rounded-xl border border-black/10 bg-[var(--card-strong)] px-3 py-2 text-sm outline-none dark:border-white/10"
                      />
                    </div>
                  ) : null}

                  {!confirmado ? (
                    <div className="flex flex-col gap-3 sm:flex-row">
                      <button
                        onClick={handleConfirmar}
                        className="primary-button flex min-h-[44px] flex-1 items-center justify-center gap-2 rounded-2xl py-3 text-sm font-semibold"
                      >
                        <CheckCircle2 className="h-4 w-4" />
                        Confirmar conteo validado
                      </button>

                      <button
                        onClick={handleSmartRetry}
                        className="secondary-button flex min-h-[44px] flex-1 items-center justify-center gap-2 rounded-2xl py-3 text-sm font-medium"
                      >
                        <RotateCcw className="h-4 w-4" />
                        Nueva captura
                      </button>
                    </div>
                  ) : (
                    <div className="flex items-center gap-3 rounded-2xl border border-green-500/20 bg-green-500/10 p-4">
                      <CheckCircle2 className="h-5 w-5 text-green-500" />
                      <p className="text-sm font-semibold text-green-500">
                        ¡Conteo guardado correctamente!
                      </p>
                    </div>
                  )}
                </div>
              ) : null}

              {hasImage && stage !== "success" ? (
                <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap">
                  <button
                    onClick={handleCompressAndUpload}
                    disabled={!selectedFile || stage === "compressing" || stage === "uploading" || analizando}
                    className="primary-button inline-flex min-h-[44px] w-full items-center justify-center gap-2 rounded-2xl px-4 py-3 text-sm font-semibold transition duration-300 hover:-translate-y-0.5 disabled:opacity-60 sm:w-auto"
                  >
                    <UploadCloud className="h-4 w-4" />
                    Analizar con IA
                  </button>

                  <button
                    onClick={handleSmartRetry}
                    className="secondary-button inline-flex min-h-[44px] w-full items-center justify-center gap-2 rounded-2xl px-4 py-3 text-sm font-medium transition duration-300 hover:-translate-y-0.5 sm:w-auto"
                  >
                    <RefreshCw className="h-4 w-4" />
                    Limpiar captura
                  </button>
                </div>
              ) : null}
            </div>

            <div className="min-w-0 space-y-5">
              <div className="glass-card rounded-[32px] p-6">
                <p className="text-sm font-medium text-[var(--muted)]">Estado actual</p>
                <h3 className="mt-1 text-2xl font-semibold tracking-tight">{stageLabel}</h3>

                <div className="mt-6 space-y-3">
                  <div className="rounded-[24px] bg-[var(--card-strong)] p-4 ring-1 ring-black/5 dark:ring-white/10">
                    <p className="text-sm text-[var(--muted)]">Flujo optimizado</p>
                    <p className="mt-2 text-sm font-semibold">
                      Captura → IA multicategoría → validación por tipo → guardado
                    </p>
                  </div>

                  <div className="rounded-[24px] bg-[var(--card-strong)] p-4 ring-1 ring-black/5 dark:ring-white/10">
                    <p className="text-sm text-[var(--muted)]">Categorías activas</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {IA_CATEGORIES.map((category) => (
                        <span
                          key={category.key}
                          className="inline-flex items-center gap-2 rounded-full bg-[var(--egg)] px-3 py-1 text-xs font-semibold text-[var(--primary-strong)]"
                        >
                          <CircleDot className="h-3.5 w-3.5" />
                          {category.title}
                        </span>
                      ))}
                    </div>
                  </div>

                  {resultadoIA ? (
                    <div className="rounded-[24px] bg-[var(--card-strong)] p-4 ring-1 ring-black/5 dark:ring-white/10">
                      <p className="text-sm text-[var(--muted)]">Tiempo de IA</p>
                      <p className="mt-2 text-2xl font-black">
                        {resultadoIA.duracion_ms ? `${resultadoIA.duracion_ms} ms` : "Sin dato"}
                      </p>
                    </div>
                  ) : null}
                </div>
              </div>

              <div className="glass-card rounded-[32px] p-6">
                <p className="text-sm font-medium text-[var(--muted)]">Resumen rápido</p>
                <h3 className="mt-1 text-2xl font-semibold tracking-tight">Detalles</h3>

                <div className="mt-6 grid gap-3">
                  <div className="rounded-[24px] bg-[var(--card-strong)] p-4 ring-1 ring-black/5 dark:ring-white/10">
                    <p className="text-sm text-[var(--muted)]">Archivo original</p>
                    <p className="mt-2 text-sm font-semibold">
                      {originalMeta ? formatBytes(originalMeta.size) : "Sin datos"}
                    </p>
                  </div>

                  <div className="rounded-[24px] bg-[var(--card-strong)] p-4 ring-1 ring-black/5 dark:ring-white/10">
                    <p className="text-sm text-[var(--muted)]">Archivo optimizado</p>
                    <p className="mt-2 text-sm font-semibold">
                      {compressedMeta ? formatBytes(compressedMeta.size) : "Aún no comprimido"}
                    </p>
                  </div>

                  {resultadoIA ? (
                    <>
                      <div className="rounded-[24px] bg-[var(--egg)] p-4 ring-1 ring-black/5 dark:ring-white/10">
                        <p className="text-sm font-medium text-[var(--primary-strong)]">Conteo IA total</p>
                        <p className="mt-2 text-4xl font-black text-[var(--primary-strong)]">{totalIA}</p>
                        <p className="mt-2 text-xs leading-5 text-[var(--muted)]">{countSummaryLines(iaCounts)}</p>
                      </div>

                      <div className="rounded-[24px] bg-[var(--card-strong)] p-4 ring-1 ring-black/5 dark:ring-white/10">
                        <p className="text-sm text-[var(--muted)]">Conteo validado</p>
                        <p className="mt-2 text-4xl font-black">{totalValidated}</p>
                        <p className="mt-2 text-xs leading-5 text-[var(--muted)]">
                          {countSummaryLines(validatedCounts)}
                        </p>
                      </div>
                    </>
                  ) : null}
                </div>
              </div>
            </div>
          </section>
        </PageContainer>
      </AppShell>
    </RouteGuard>
  );
}
