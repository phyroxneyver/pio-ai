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