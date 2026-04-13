"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Camera,
  CheckCircle2,
  ImagePlus,
  RefreshCw,
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
import { UploadProgress } from "@/components/media/upload-progress";
import { RetryUploadButton } from "@/components/media/retry-upload-button";
import { compressImage, formatBytes } from "@/lib/image-compression";
import { mockUploadImage } from "@/lib/mock-upload-image";
import { useToast } from "@/components/ui/toast-provider";
import type { CaptureStage, ImageMeta } from "@/types/media";

export default function CapturaPage() {
  const { showToast } = useToast();

  const [stage, setStage] = useState<CaptureStage>("idle");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [compressedFile, setCompressedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState("");
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState("");
  const [originalMeta, setOriginalMeta] = useState<ImageMeta | null>(null);
  const [compressedMeta, setCompressedMeta] = useState<ImageMeta | null>(null);
  const [simulateFailure, setSimulateFailure] = useState(false);

  useEffect(() => {
    if (!selectedFile) {
      setPreviewUrl("");
      return;
    }

    const url = URL.createObjectURL(selectedFile);
    setPreviewUrl(url);

    return () => {
      URL.revokeObjectURL(url);
    };
  }, [selectedFile]);

  const stageLabel = useMemo(() => {
    switch (stage) {
      case "idle":
        return "Sin imagen cargada";
      case "preview":
        return "Imagen lista para revisión";
      case "compressing":
        return "Optimizando imagen";
      case "uploading":
        return "Subiendo imagen";
      case "success":
        return "Subida completada";
      case "error":
        return "La subida falló";
      default:
        return "Sin estado";
    }
  }, [stage]);

  function handleCapture(file: File) {
    setSelectedFile(file);
    setCompressedFile(null);
    setCompressedMeta(null);
    setProgress(0);
    setError("");
    setStage("preview");

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
    setSimulateFailure(false);
  }

  async function uploadCompressedFile(fileToUpload: File) {
    setStage("uploading");
    setError("");
    setProgress(0);

    await mockUploadImage(fileToUpload, {
      onProgress: setProgress,
      forceError: simulateFailure,
    });

    setProgress(100);
    setStage("success");
    setSimulateFailure(false);

    showToast({
      type: "success",
      title: "Imagen subida",
      description: "La fotografía fue enviada correctamente.",
    });
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

      await uploadCompressedFile(result.file);
    } catch (err) {
      const message =
        err instanceof Error
          ? err.message
          : "No se pudo procesar la imagen seleccionada.";

      setStage("error");
      setError(message);

      showToast({
        type: "error",
        title: "Falló el procesamiento",
        description: message,
      });
    }
  }

  async function handleRetry() {
    try {
      const fileToUpload = compressedFile ?? selectedFile;

      if (!fileToUpload) {
        throw new Error("No hay imagen disponible para reintentar.");
      }

      await uploadCompressedFile(fileToUpload);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "No se pudo reintentar la subida.";

      setStage("error");
      setError(message);

      showToast({
        type: "error",
        title: "El reintento falló",
        description: message,
      });
    }
  }

  const hasImage = Boolean(selectedFile && previewUrl);

  return (
    <RouteGuard>
      <AppShell
        header={<AppHeader />}
        sidebar={<Sidebar />}
        tabBar={<TabBar />}
      >
        <PageContainer>
          <section className="grid gap-5 xl:grid-cols-[1.15fr_0.85fr]">
            <div className="space-y-5 min-w-0">
              <div className="glass-card rounded-[32px] p-5 shadow-[0_20px_50px_rgba(0,0,0,0.07)] sm:p-8">
                <span className="inline-flex items-center gap-2 rounded-full bg-[var(--egg)] px-3 py-1 text-xs font-semibold text-[var(--primary-strong)] dark:bg-white/5">
                  <Camera className="h-3.5 w-3.5" />
                  Captura multimedia
                </span>

                <h2 className="mt-4 text-3xl font-semibold leading-tight tracking-tight sm:text-4xl">
                  Toma, revisa y sube una fotografía
                </h2>

                <p className="mt-4 text-sm leading-7 text-[var(--muted)] sm:text-base">
                  Usa la cámara del dispositivo o del navegador, revisa la foto,
                  optimízala y súbela con control de progreso.
                </p>

                <div className="mt-6">
                  <CameraInput
                    onCapture={handleCapture}
                    disabled={stage === "compressing" || stage === "uploading"}
                  />
                </div>
              </div>

              {stage === "compressing" ? (
                <Spinner label="Optimizando imagen antes de enviarla..." />
              ) : null}

              {hasImage && originalMeta ? (
                <PhotoPreview
                  previewUrl={previewUrl}
                  originalMeta={originalMeta}
                  compressedMeta={compressedMeta}
                  onRemove={resetCapture}
                />
              ) : (
                <div className="glass-card rounded-[32px] p-8 text-center shadow-[0_18px_40px_rgba(0,0,0,0.06)]">
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
              )}

              {(stage === "uploading" || stage === "success") && hasImage ? (
                <UploadProgress
                  progress={progress}
                  label={
                    stage === "success"
                      ? "Carga completada"
                      : "Subiendo fotografía..."
                  }
                />
              ) : null}

              {stage === "error" && error ? (
                <ErrorAlert
                  title="Error al subir la fotografía"
                  message={error}
                />
              ) : null}

              <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap">
                <button
                  onClick={handleCompressAndUpload}
                  disabled={
                    !selectedFile ||
                    stage === "compressing" ||
                    stage === "uploading"
                  }
                  className="primary-button inline-flex w-full items-center justify-center gap-2 rounded-2xl px-4 py-3 text-sm font-semibold transition duration-300 hover:-translate-y-0.5 disabled:opacity-60 sm:w-auto"
                >
                  <UploadCloud className="h-4 w-4" />
                  Comprimir y subir
                </button>

                {stage === "error" ? (
                  <RetryUploadButton onRetry={handleRetry} />
                ) : null}

                <button
                  onClick={resetCapture}
                  className="secondary-button inline-flex w-full items-center justify-center gap-2 rounded-2xl px-4 py-3 text-sm font-medium transition duration-300 hover:-translate-y-0.5 sm:w-auto"
                >
                  <RefreshCw className="h-4 w-4" />
                  Limpiar
                </button>
              </div>
            </div>

            <div className="space-y-5 min-w-0">
              <div className="glass-card rounded-[32px] p-6 shadow-[0_20px_50px_rgba(0,0,0,0.07)]">
                <p className="text-sm font-medium text-[var(--muted)]">
                  Estado actual
                </p>
                <h3 className="mt-1 text-2xl font-semibold tracking-tight">
                  {stageLabel}
                </h3>

                <div className="mt-6 space-y-3">
                  <div className="rounded-[24px] bg-[var(--card-strong)] p-4 ring-1 ring-black/5 dark:ring-white/10">
                    <p className="text-sm text-[var(--muted)]">Flujo</p>
                    <p className="mt-2 text-sm font-semibold">
                      Captura → revisión → compresión → subida
                    </p>
                  </div>

                  <label className="flex items-center justify-between gap-3 rounded-[24px] bg-[var(--card-strong)] p-4 ring-1 ring-black/5 dark:ring-white/10">
                    <span className="text-sm font-medium">
                      Simular error de subida
                    </span>

                    <input
                      type="checkbox"
                      checked={simulateFailure}
                      onChange={(e) => setSimulateFailure(e.target.checked)}
                      className="h-4 w-4 accent-[var(--primary-strong)]"
                    />
                  </label>
                </div>
              </div>

              <div className="glass-card rounded-[32px] p-6 shadow-[0_20px_50px_rgba(0,0,0,0.07)]">
                <p className="text-sm font-medium text-[var(--muted)]">
                  Resumen del archivo
                </p>
                <h3 className="mt-1 text-2xl font-semibold tracking-tight">
                  Detalles de imagen
                </h3>

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
                      {compressedMeta
                        ? formatBytes(compressedMeta.size)
                        : "Aún no comprimido"}
                    </p>
                  </div>

                  <div className="rounded-[24px] bg-[var(--card-strong)] p-4 ring-1 ring-black/5 dark:ring-white/10">
                    <p className="text-sm text-[var(--muted)]">Formato final</p>
                    <p className="mt-2 text-sm font-semibold">
                      {compressedMeta?.format || "Sin definir"}
                    </p>
                  </div>
                </div>

                {stage === "success" ? (
                  <div className="mt-6 rounded-[24px] border border-emerald-500/15 bg-emerald-500/10 p-4 text-emerald-700 dark:text-emerald-300">
                    <div className="flex items-start gap-3">
                      <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0" />
                      <div>
                        <p className="text-sm font-semibold">
                          Fotografía cargada correctamente
                        </p>
                        <p className="mt-1 text-sm">
                          Ya puedes continuar con el siguiente registro.
                        </p>
                      </div>
                    </div>
                  </div>
                ) : null}
              </div>
            </div>
          </section>
        </PageContainer>
      </AppShell>
    </RouteGuard>
  );
}