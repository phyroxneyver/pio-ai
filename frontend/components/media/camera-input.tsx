"use client";

import { useEffect, useRef, useState } from "react";
import { Aperture, Camera, FolderOpen, X } from "lucide-react";
import { ErrorAlert } from "@/components/feedback/error-alert";

type CameraInputProps = {
  onCapture: (file: File) => void;
  disabled?: boolean;
};

export function CameraInput({
  onCapture,
  disabled = false,
}: CameraInputProps) {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const [cameraOpen, setCameraOpen] = useState(false);
  const [startingCamera, setStartingCamera] = useState(false);
  const [cameraError, setCameraError] = useState("");

  function stopStream() {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
  }

  useEffect(() => {
    return () => { stopStream(); };
  }, []);

  async function openLiveCamera() {
    if (disabled) return;
    try {
      setCameraError("");
      setStartingCamera(true);
      stopStream();

      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: "environment" } },
        audio: false,
      });

      streamRef.current = stream;
      setCameraOpen(true);

      window.setTimeout(async () => {
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          try {
            await videoRef.current.play();
          } catch {
            setCameraError("No se pudo iniciar la previsualización de la cámara.");
          }
        }
      }, 50);
    } catch {
      setCameraError(
        "No se pudo acceder a la cámara. Revisa los permisos del navegador o usa la opción de seleccionar imagen.",
      );
      setCameraOpen(false);
    } finally {
      setStartingCamera(false);
    }
  }

  function openNativeInput() {
    if (disabled) return;
    fileInputRef.current?.click();
  }

  function handleFileChange(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (file) onCapture(file);
    event.currentTarget.value = "";
  }

  async function takePhoto() {
    if (!videoRef.current || !canvasRef.current) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const width = video.videoWidth || 1280;
    const height = video.videoHeight || 720;

    canvas.width = width;
    canvas.height = height;

    const context = canvas.getContext("2d");
    if (!context) {
      setCameraError("No se pudo procesar la fotografía capturada.");
      return;
    }

    context.drawImage(video, 0, 0, width, height);

    const blob = await new Promise<Blob | null>((resolve) => {
      canvas.toBlob(resolve, "image/jpeg", 0.92);
    });

    if (!blob) {
      setCameraError("No se pudo generar la foto capturada.");
      return;
    }

    const file = new File([blob], `captura-${Date.now()}.jpg`, {
      type: "image/jpeg",
      lastModified: Date.now(),
    });

    onCapture(file);
    closeLiveCamera();
  }

  function closeLiveCamera() {
    stopStream();
    setCameraOpen(false);
  }

  return (
    <div className="space-y-4">
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        capture="environment"
        className="hidden"
        onChange={handleFileChange}
      />

      <canvas ref={canvasRef} className="hidden" />

      <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap">
        <button
          onClick={openNativeInput}
          disabled={disabled}
          className="primary-button inline-flex w-full items-center justify-center gap-2 rounded-2xl px-4 py-3 text-sm font-semibold transition duration-300 hover:-translate-y-0.5 disabled:opacity-60 sm:w-auto"
        >
          <FolderOpen className="h-4 w-4" />
          Tomar o elegir foto
        </button>

        <button
          onClick={openLiveCamera}
          disabled={disabled || startingCamera}
          className="secondary-button inline-flex w-full items-center justify-center gap-2 rounded-2xl px-4 py-3 text-sm font-medium transition duration-300 hover:-translate-y-0.5 disabled:opacity-60 sm:w-auto"
        >
          <Aperture className="h-4 w-4" />
          {startingCamera ? "Abriendo..." : "Vista en vivo"}
        </button>
      </div>

      {cameraError ? (
        <ErrorAlert title="No se pudo abrir la cámara" message={cameraError} />
      ) : null}

      {cameraOpen ? (
        <div className="glass-card rounded-[32px] p-5 shadow-[0_18px_40px_rgba(0,0,0,0.06)]">

          {/* Visor con overlay guía */}
          <div className="relative overflow-hidden rounded-[24px] bg-black">
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className="h-[320px] w-full object-cover sm:h-[420px]"
            />

            {/* Overlay oscuro en los bordes */}
            <div className="absolute inset-0 pointer-events-none">
              {/* Bordes oscuros */}
              <div className="absolute inset-0 bg-black/40" />

              {/* Recuadro guía central transparente */}
              <div className="absolute inset-0 flex items-center justify-center">
                <div
                  className="relative border-2 border-[var(--egg)] rounded-2xl"
                  style={{ width: "75%", height: "65%" }}
                >
                  {/* Esquinas del recuadro */}
                  <div className="absolute -top-1 -left-1 w-5 h-5 border-t-4 border-l-4 border-[var(--egg)] rounded-tl-lg" />
                  <div className="absolute -top-1 -right-1 w-5 h-5 border-t-4 border-r-4 border-[var(--egg)] rounded-tr-lg" />
                  <div className="absolute -bottom-1 -left-1 w-5 h-5 border-b-4 border-l-4 border-[var(--egg)] rounded-bl-lg" />
                  <div className="absolute -bottom-1 -right-1 w-5 h-5 border-b-4 border-r-4 border-[var(--egg)] rounded-br-lg" />

                  {/* Texto guía dentro del recuadro */}
                  <div className="absolute bottom-3 left-0 right-0 flex justify-center">
                    <span className="bg-black/60 text-white text-xs font-semibold px-3 py-1 rounded-full">
                      Centra pollos, gallinas o huevos
                    </span>
                  </div>
                </div>
              </div>

              {/* Instrucción arriba */}
              <div className="absolute top-3 left-0 right-0 flex justify-center">
                <span className="bg-black/60 text-white text-xs px-3 py-1 rounded-full">
                  📏 Evita sombras y objetos cortados
                </span>
              </div>
            </div>
          </div>

          <div className="mt-4 flex flex-col gap-3 sm:flex-row">
            <button
              onClick={takePhoto}
              className="primary-button inline-flex w-full items-center justify-center gap-2 rounded-2xl px-4 py-3 text-sm font-semibold transition duration-300 hover:-translate-y-0.5 sm:w-auto"
            >
              <Camera className="h-4 w-4" />
              Tomar foto
            </button>

            <button
              onClick={closeLiveCamera}
              className="secondary-button inline-flex w-full items-center justify-center gap-2 rounded-2xl px-4 py-3 text-sm font-medium transition duration-300 hover:-translate-y-0.5 sm:w-auto"
            >
              <X className="h-4 w-4" />
              Cerrar cámara
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}