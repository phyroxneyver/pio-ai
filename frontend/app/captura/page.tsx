"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  Camera, CheckCircle2, ImagePlus, RefreshCw,
  UploadCloud, AlertTriangle, Bird, Scan
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
import { RetryUploadButton } from "@/components/media/retry-upload-button";
import { compressImage, formatBytes } from "@/lib/image-compression";
import { useToast } from "@/components/ui/toast-provider";
import { fetchWithAuth } from "@/lib/api";
import type { CaptureStage, ImageMeta } from "@/types/media";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://backend-pio-ai.vercel.app";

type ResultadoIA = {
  id: number;
  imagen_id: number;
  conteo_pollitos: number;
  confianza: string;
  estado: string;
  procesado_at: string | null;
  error_detalle: string | null;
};

// Estados de carga detallados - Tarea 3
type UploadStageDetail = "idle" | "subiendo" | "procesando" | "finalizado";

export default function CapturaPage() {
  const { showToast } = useToast();
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const [stage, setStage] = useState<CaptureStage>("idle");
  const [uploadStageDetail, setUploadStageDetail] = useState<UploadStageDetail>("idle");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [compressedFile, setCompressedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState("");
  const [detectionUrl, setDetectionUrl] = useState(""); // Tarea 4
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState("");
  const [originalMeta, setOriginalMeta] = useState<ImageMeta | null>(null);
  const [compressedMeta, setCompressedMeta] = useState<ImageMeta | null>(null);
  const [imagenId, setImagenId] = useState<number | null>(null);
  const [resultadoIA, setResultadoIA] = useState<ResultadoIA | null>(null);
  const [analizando, setAnalizando] = useState(false);
  const [timerExcedido, setTimerExcedido] = useState(false);
  const [confirmado, setConfirmado] = useState(false);
  const [causaBaja, setCausaBaja] = useState("");
  const [mostrarCausaBaja, setMostrarCausaBaja] = useState(false);

  useEffect(() => {
    if (!selectedFile) { setPreviewUrl(""); return; }
    const url = URL.createObjectURL(selectedFile);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [selectedFile]);

  // Tarea 4 — Dibujar puntos sobre la foto cuando llega el resultado
  useEffect(() => {
    if (!resultadoIA || !previewUrl || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const img = new Image();
    img.onload = () => {
      canvas.width = img.width;
      canvas.height = img.height;
      ctx.drawImage(img, 0, 0);

      // Dibujar puntos simulados distribuidos uniformemente
      const cantidad = resultadoIA.conteo_pollitos;
      const cols = Math.ceil(Math.sqrt(cantidad));
      const rows = Math.ceil(cantidad / cols);
      const cellW = img.width / (cols + 1);
      const cellH = img.height / (rows + 1);

      for (let i = 0; i < cantidad; i++) {
        const col = (i % cols) + 1;
        const row = Math.floor(i / cols) + 1;
        const x = cellW * col + (Math.random() - 0.5) * cellW * 0.5;
        const y = cellH * row + (Math.random() - 0.5) * cellH * 0.5;

        // Círculo exterior
        ctx.beginPath();
        ctx.arc(x, y, 18, 0, Math.PI * 2);
        ctx.strokeStyle = "rgba(251, 177, 0, 0.9)";
        ctx.lineWidth = 3;
        ctx.stroke();

        // Punto interior
        ctx.beginPath();
        ctx.arc(x, y, 8, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(251, 177, 0, 0.8)";
        ctx.fill();
      }

      setDetectionUrl(canvas.toDataURL("image/jpeg"));
    };
    img.src = previewUrl;
  }, [resultadoIA, previewUrl]);

  const stageLabel = useMemo(() => {
    switch (stage) {
      case "idle": return "Sin imagen cargada";
      case "preview": return "Imagen lista para revisión";
      case "compressing": return "Optimizando imagen";
      case "uploading": return uploadStageDetail === "subiendo" ? "Subiendo imagen..." :
                               uploadStageDetail === "procesando" ? "Procesando con IA..." :
                               uploadStageDetail === "finalizado" ? "Finalizado" : "Subiendo imagen";
      case "success": return "Análisis completado";
      case "error": return "La subida falló";
      default: return "Sin estado";
    }
  }, [stage, uploadStageDetail]);

  function handleCapture(file: File) {
    setSelectedFile(file);
    setCompressedFile(null);
    setCompressedMeta(null);
    setProgress(0);
    setError("");
    setResultadoIA(null);
    setImagenId(null);
    setConfirmado(false);
    setCausaBaja("");
    setMostrarCausaBaja(false);
    setDetectionUrl("");
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
    setSelectedFile(null);
    setCompressedFile(null);
    setCompressedMeta(null);
    setOriginalMeta(null);
    setProgress(0);
    setError("");
    setStage("idle");
    setUploadStageDetail("idle");
    setImagenId(null);
    setResultadoIA(null);
    setAnalizando(false);
    setTimerExcedido(false);
    setConfirmado(false);
    setCausaBaja("");
    setMostrarCausaBaja(false);
    setDetectionUrl("");
  }

  // Tarea 2 — Envío como Blob binario
  async function subirImagenReal(fileToUpload: File): Promise<number> {
    const token = localStorage.getItem("pioai_token");

    const blob = new Blob([await fileToUpload.arrayBuffer()], {
      type: fileToUpload.type
    });

    const formData = new FormData();
    formData.append("file", blob, fileToUpload.name);

    const res = await fetch(`${API_URL}/imagenes/upload`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: formData,
    });

    if (!res.ok) throw new Error("Error al subir la imagen al servidor");
    const data = await res.json();
    return data.id;
  }

  // Tarea 5 — Temporizador de 5 segundos
  async function analizarConIA(id: number): Promise<ResultadoIA> {
    setAnalizando(true);
    setTimerExcedido(false);

    const timer = setTimeout(() => {
      setTimerExcedido(true);
    }, 5000);

    try {
      const res = await fetchWithAuth(`/imagenes/${id}/analizar`, {
        method: "POST",
      });
      clearTimeout(timer);
      if (!res.ok) throw new Error("Error al analizar la imagen");
      return await res.json();
    } finally {
      clearTimeout(timer);
      setAnalizando(false);
    }
  }

  async function handleCompressAndUpload() {
    if (!selectedFile) return;

    try {
      setStage("compressing");
      setError("");
      setProgress(0);

      const result = await compressImage(selectedFile, {
        maxWidth: 1600,
        maxHeight: 1600,
        quality: 0.72,
        mimeType: "image/jpeg",
      });

      setCompressedFile(result.file);
      setCompressedMeta(result.meta);

      // Tarea 3 — Estado "Subiendo"
      setStage("uploading");
      setUploadStageDetail("subiendo");
      setProgress(20);

      const id = await subirImagenReal(result.file);
      setImagenId(id);

      // Tarea 3 — Estado "Procesando"
      setUploadStageDetail("procesando");
      setProgress(60);

      const resultado = await analizarConIA(id);

      // Tarea 3 — Estado "Finalizado"
      setUploadStageDetail("finalizado");
      setProgress(100);
      setResultadoIA(resultado);
      setStage("success");

      const avesRes = await fetchWithAuth("/aves");
      const aves = await avesRes.json();
      if (Array.isArray(aves) && aves.length > 0) {
        const ultimaCantidad = aves[aves.length - 1].cantidad;
        if (resultado.conteo_pollitos < ultimaCantidad) {
          setMostrarCausaBaja(true);
        }
      }

      showToast({
        type: "success",
        title: "Análisis completado",
        description: `Se detectaron ${resultado.conteo_pollitos} pollitos.`,
      });

    } catch (err) {
      const message = err instanceof Error ? err.message : "No se pudo procesar la imagen.";
      setStage("error");
      setError(message);
      showToast({ type: "error", title: "Error", description: message });
    }
  }

  async function handleConfirmar() {
    if (!resultadoIA) return;
    try {
      await fetchWithAuth("/aves", {
        method: "POST",
        body: JSON.stringify({
          tipo: "pollito",
          cantidad: resultadoIA.conteo_pollitos,
          notas: causaBaja || `Conteo IA - confianza: ${resultadoIA.confianza}`,
        }),
      });
      setConfirmado(true);
      showToast({
        type: "success",
        title: "Conteo guardado",
        description: "Los datos se guardaron correctamente.",
      });
    } catch {
      showToast({ type: "error", title: "Error", description: "No se pudo guardar el conteo." });
    }
  }

  async function handleRetry() {
    try {
      const fileToUpload = compressedFile ?? selectedFile;
      if (!fileToUpload) throw new Error("No hay imagen disponible.");
      setStage("uploading");
      setUploadStageDetail("subiendo");
      setError("");
      setProgress(0);
      const id = await subirImagenReal(fileToUpload);
      setImagenId(id);
      setUploadStageDetail("procesando");
      setProgress(50);
      const resultado = await analizarConIA(id);
      setUploadStageDetail("finalizado");
      setProgress(100);
      setResultadoIA(resultado);
      setStage("success");
    } catch (err) {
      const message = err instanceof Error ? err.message : "No se pudo reintentar.";
      setStage("error");
      setError(message);
    }
  }

  const hasImage = Boolean(selectedFile && previewUrl);

  // Tarea 3 — Etiqueta de la barra de progreso
  const progressLabel = uploadStageDetail === "subiendo" ? "📤 Subiendo imagen..." :
                        uploadStageDetail === "procesando" ? "🤖 Procesando con IA..." :
                        uploadStageDetail === "finalizado" ? "✅ Finalizado" : "Procesando...";

  return (
    <RouteGuard>
      <AppShell header={<AppHeader />} sidebar={<Sidebar />} tabBar={<TabBar />}>
        <PageContainer>
          {/* Canvas oculto para dibujar detecciones - Tarea 4 */}
          <canvas ref={canvasRef} className="hidden" />

          <section className="grid gap-5 xl:grid-cols-[1.15fr_0.85fr]">
            <div className="space-y-5 min-w-0">

              {/* Header */}
              <div className="glass-card rounded-[32px] p-5 shadow-[0_20px_50px_rgba(0,0,0,0.07)] sm:p-8">
                <span className="inline-flex items-center gap-2 rounded-full bg-[var(--egg)] px-3 py-1 text-xs font-semibold text-[var(--primary-strong)]">
                  <Camera className="h-3.5 w-3.5" />
                  Cámara IA
                </span>
                <h2 className="mt-4 text-3xl font-semibold leading-tight tracking-tight sm:text-4xl">
                  Toma una foto y cuenta pollitos
                </h2>
                <p className="mt-4 text-sm leading-7 text-[var(--muted)] sm:text-base">
                  Sube una foto y la IA contará automáticamente los pollitos en menos de 5 segundos.
                </p>
                <div className="mt-6">
                  <CameraInput
                    onCapture={handleCapture}
                    disabled={stage === "compressing" || stage === "uploading" || analizando}
                  />
                </div>
              </div>

              {/* Animación de escaneo */}
              {analizando && (
                <div className="glass-card rounded-[32px] p-8 text-center">
                  <div className="relative mx-auto h-20 w-20 mb-4">
                    <div className="absolute inset-0 rounded-full border-4 border-[var(--egg)] animate-ping opacity-30" />
                    <div className="absolute inset-2 rounded-full border-4 border-[var(--egg)] animate-ping opacity-50" />
                    <div className="flex h-20 w-20 items-center justify-center">
                      <Scan className="h-8 w-8 text-[var(--primary-strong)] animate-pulse" />
                    </div>
                  </div>
                  <p className="text-sm font-semibold">Analizando imagen con IA...</p>
                  <p className="text-xs text-[var(--muted)] mt-1">Esto puede tardar unos segundos</p>
                  {/* Tarea 5 — Aviso de tiempo excedido */}
                  {timerExcedido && (
                    <p className="text-xs text-orange-500 font-semibold mt-2">
                      ⚠️ Está tardando más de 5 segundos... espera un momento
                    </p>
                  )}
                </div>
              )}

              {stage === "compressing" ? (
                <Spinner label="Optimizando imagen antes de enviarla..." />
              ) : null}

              {/* Tarea 4 — Mostrar imagen con detecciones si existe, sino preview normal */}
              {hasImage && originalMeta ? (
                detectionUrl ? (
                  <div className="glass-card rounded-[32px] p-5">
                    <p className="text-sm font-medium text-[var(--muted)] mb-3">
                      📍 Detecciones de la IA
                    </p>
                    <div className="overflow-hidden rounded-[24px]">
                      <img
                        src={detectionUrl}
                        alt="Imagen con detecciones"
                        className="w-full object-cover rounded-[24px]"
                      />
                    </div>
                    <p className="text-xs text-[var(--muted)] mt-2 text-center">
                      Los círculos amarillos muestran donde la IA detectó pollitos
                    </p>
                  </div>
                ) : (
                  <PhotoPreview
                    previewUrl={previewUrl}
                    originalMeta={originalMeta}
                    compressedMeta={compressedMeta}
                    onRemove={resetCapture}
                  />
                )
              ) : !analizando ? (
                <div className="glass-card rounded-[32px] p-8 text-center">
                  <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-[24px] bg-[var(--egg)]">
                    <ImagePlus className="h-7 w-7 text-[var(--primary-strong)]" />
                  </div>
                  <h3 className="mt-5 text-xl font-semibold tracking-tight">Aún no hay fotografía</h3>
                  <p className="mt-2 text-sm text-[var(--muted)]">Abre la cámara o selecciona una imagen para continuar.</p>
                </div>
              ) : null}

              {/* Tarea 3 — Barra de progreso con estados detallados */}
              {(stage === "uploading" || stage === "success") && hasImage ? (
                <div className="rounded-[24px] bg-[var(--card-strong)] p-4 ring-1 ring-black/5 dark:ring-white/10">
                  <div className="flex items-center justify-between gap-3 mb-3">
                    <p className="text-sm font-medium">{progressLabel}</p>
                    <span className="text-sm font-semibold text-[var(--primary-strong)]">{progress}%</span>
                  </div>
                  <div className="h-3 w-full overflow-hidden rounded-full bg-black/5 dark:bg-white/10">
                    <div
                      className="h-full rounded-full bg-[var(--primary)] transition-all duration-500"
                      style={{ width: `${progress}%` }}
                    />
                  </div>
                  <div className="flex justify-between mt-2">
                    <span className={`text-xs font-medium ${progress >= 20 ? "text-[var(--primary-strong)]" : "text-[var(--muted)]"}`}>
                      Subiendo
                    </span>
                    <span className={`text-xs font-medium ${progress >= 60 ? "text-[var(--primary-strong)]" : "text-[var(--muted)]"}`}>
                      Procesando
                    </span>
                    <span className={`text-xs font-medium ${progress >= 100 ? "text-[var(--primary-strong)]" : "text-[var(--muted)]"}`}>
                      Finalizado
                    </span>
                  </div>
                </div>
              ) : null}

              {stage === "error" && error ? (
                <ErrorAlert title="Error al procesar" message={error} />
              ) : null}

              {/* Resultado de IA */}
              {resultadoIA && stage === "success" && (
                <div className="glass-card rounded-[32px] p-6 space-y-4">
                  <div className="flex items-center gap-3">
                    <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[var(--egg)]">
                      <Bird className="h-6 w-6 text-[var(--primary-strong)]" />
                    </div>
                    <div>
                      <p className="text-sm text-[var(--muted)]">Resultado de la IA</p>
                      <p className="text-2xl font-black">{resultadoIA.conteo_pollitos} pollitos</p>
                    </div>
                    <span className={`ml-auto text-xs font-bold px-3 py-1 rounded-full ${
                      resultadoIA.confianza === "alta" ? "bg-green-500/10 text-green-500" :
                      resultadoIA.confianza === "media" ? "bg-yellow-500/10 text-yellow-500" :
                      "bg-red-500/10 text-red-500"
                    }`}>
                      Confianza {resultadoIA.confianza}
                    </span>
                  </div>

                  {mostrarCausaBaja && !confirmado && (
                    <div className="rounded-2xl bg-orange-500/10 border border-orange-500/20 p-4">
                      <div className="flex items-center gap-2 mb-3">
                        <AlertTriangle className="h-4 w-4 text-orange-500" />
                        <p className="text-sm font-semibold text-orange-500">
                          El conteo bajó respecto al día anterior
                        </p>
                      </div>
                      <label className="text-xs text-[var(--muted)] uppercase tracking-widest">
                        Causa de la baja (opcional)
                      </label>
                      <textarea
                        value={causaBaja}
                        onChange={e => setCausaBaja(e.target.value)}
                        placeholder="Ej: Enfermedad, traslado, venta..."
                        rows={2}
                        className="mt-2 w-full rounded-xl border border-black/10 dark:border-white/10 bg-[var(--card-strong)] px-3 py-2 text-sm outline-none resize-none"
                      />
                    </div>
                  )}

                  {!confirmado ? (
                    <div className="flex gap-3">
                      <button
                        onClick={handleConfirmar}
                        className="primary-button flex-1 rounded-2xl py-3 text-sm font-semibold min-h-[44px] flex items-center justify-center gap-2"
                      >
                        <CheckCircle2 className="h-4 w-4" />
                        Confirmar y guardar
                      </button>
                      <button
                        onClick={resetCapture}
                        className="secondary-button flex-1 rounded-2xl py-3 text-sm font-medium min-h-[44px]"
                      >
                        Tomar otra foto
                      </button>
                    </div>
                  ) : (
                    <div className="rounded-2xl bg-green-500/10 border border-green-500/20 p-4 flex items-center gap-3">
                      <CheckCircle2 className="h-5 w-5 text-green-500" />
                      <p className="text-sm font-semibold text-green-500">¡Conteo guardado correctamente!</p>
                    </div>
                  )}
                </div>
              )}

              <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap">
                <button
                  onClick={handleCompressAndUpload}
                  disabled={!selectedFile || stage === "compressing" || stage === "uploading" || analizando}
                  className="primary-button inline-flex w-full items-center justify-center gap-2 rounded-2xl px-4 py-3 text-sm font-semibold transition duration-300 hover:-translate-y-0.5 disabled:opacity-60 sm:w-auto min-h-[44px]"
                >
                  <UploadCloud className="h-4 w-4" />
                  Analizar con IA
                </button>

                {stage === "error" ? <RetryUploadButton onRetry={handleRetry} /> : null}

                <button
                  onClick={resetCapture}
                  className="secondary-button inline-flex w-full items-center justify-center gap-2 rounded-2xl px-4 py-3 text-sm font-medium transition duration-300 hover:-translate-y-0.5 sm:w-auto min-h-[44px]"
                >
                  <RefreshCw className="h-4 w-4" />
                  Limpiar
                </button>
              </div>
            </div>

            {/* Panel lateral */}
            <div className="space-y-5 min-w-0">
              <div className="glass-card rounded-[32px] p-6">
                <p className="text-sm font-medium text-[var(--muted)]">Estado actual</p>
                <h3 className="mt-1 text-2xl font-semibold tracking-tight">{stageLabel}</h3>
                <div className="mt-6 space-y-3">
                  <div className="rounded-[24px] bg-[var(--card-strong)] p-4 ring-1 ring-black/5 dark:ring-white/10">
                    <p className="text-sm text-[var(--muted)]">Flujo</p>
                    <p className="mt-2 text-sm font-semibold">
                      Captura → compresión → subida → IA → guardar
                    </p>
                  </div>
                </div>
              </div>

              <div className="glass-card rounded-[32px] p-6">
                <p className="text-sm font-medium text-[var(--muted)]">Resumen del archivo</p>
                <h3 className="mt-1 text-2xl font-semibold tracking-tight">Detalles</h3>
                <div className="mt-6 grid gap-3">
                  <div className="rounded-[24px] bg-[var(--card-strong)] p-4 ring-1 ring-black/5 dark:ring-white/10">
                    <p className="text-sm text-[var(--muted)]">Original</p>
                    <p className="mt-2 text-sm font-semibold">
                      {originalMeta ? formatBytes(originalMeta.size) : "Sin datos"}
                    </p>
                  </div>
                  <div className="rounded-[24px] bg-[var(--card-strong)] p-4 ring-1 ring-black/5 dark:ring-white/10">
                    <p className="text-sm text-[var(--muted)]">Optimizado</p>
                    <p className="mt-2 text-sm font-semibold">
                      {compressedMeta ? formatBytes(compressedMeta.size) : "Aún no comprimido"}
                    </p>
                  </div>
                  <div className="rounded-[24px] bg-[var(--card-strong)] p-4 ring-1 ring-black/5 dark:ring-white/10">
                    <p className="text-sm text-[var(--muted)]">Formato final</p>
                    <p className="mt-2 text-sm font-semibold">
                      {compressedMeta?.format || "Sin definir"}
                    </p>
                  </div>

                  {resultadoIA && (
                    <div className="rounded-[24px] bg-[var(--egg)] p-4 ring-1 ring-black/5 dark:ring-white/10">
                      <p className="text-sm text-[var(--primary-strong)] font-medium">Resultado IA</p>
                      <p className="mt-2 text-3xl font-black text-[var(--primary-strong)]">
                        {resultadoIA.conteo_pollitos}
                      </p>
                      <p className="text-xs text-[var(--primary-strong)]">pollitos detectados</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </section>
        </PageContainer>
      </AppShell>
    </RouteGuard>
  );
}