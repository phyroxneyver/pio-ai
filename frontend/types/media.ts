export type CaptureStage =
  | "idle"
  | "preview"
  | "compressing"
  | "uploading"
  | "success"
  | "error";

export type ImageMeta = {
  name: string;
  size: number;
  format: string;
  width?: number;
  height?: number;
};

export type IAVisualDetection = {
  x: number;
  y: number;
  label?: string;
  confidence?: number | null;
};

export type LastAIMetrics = {
  imagenId: number | null;
  resultadoId: number | null;
  conteoIA: number | null;
  conteoCorregido: number | null;
  diferencia: number | null;
  confianza: string | null;
  precisionEstimada: number | null;
  duracionMs: number | null;
  estado: string;
  feedbackEnviado: boolean;
  fecha: string;
};