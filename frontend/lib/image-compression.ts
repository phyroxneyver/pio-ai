import type { ImageMeta } from "@/types/media";

type CompressOptions = {
  maxWidth?: number;
  maxHeight?: number;
  quality?: number;
  mimeType?: "image/jpeg" | "image/webp";
};

export type CompressResult = {
  file: File;
  meta: ImageMeta;
};

function loadImage(file: File): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const image = new Image();

    image.onload = () => {
      URL.revokeObjectURL(url);
      resolve(image);
    };

    image.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error("No se pudo leer la imagen seleccionada."));
    };

    image.src = url;
  });
}

export function formatBytes(bytes: number) {
  if (bytes === 0) return "0 B";

  const units = ["B", "KB", "MB", "GB"];
  const index = Math.min(
    Math.floor(Math.log(bytes) / Math.log(1024)),
    units.length - 1,
  );

  const value = bytes / 1024 ** index;
  return `${value.toFixed(value >= 10 || index === 0 ? 0 : 1)} ${units[index]}`;
}

export async function compressImage(
  file: File,
  options: CompressOptions = {},
): Promise<CompressResult> {
  const {
    maxWidth = 1600,
    maxHeight = 1600,
    quality = 0.72,
    mimeType = "image/jpeg",
  } = options;

  const image = await loadImage(file);

  let width = image.width;
  let height = image.height;

  const ratio = Math.min(maxWidth / width, maxHeight / height, 1);

  width = Math.round(width * ratio);
  height = Math.round(height * ratio);

  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;

  const context = canvas.getContext("2d");

  if (!context) {
    throw new Error("No se pudo crear el contexto de compresión.");
  }

  context.imageSmoothingEnabled = true;
  context.imageSmoothingQuality = "high";
  context.drawImage(image, 0, 0, width, height);

  const blob = await new Promise<Blob | null>((resolve) => {
    canvas.toBlob(resolve, mimeType, quality);
  });

  if (!blob) {
    throw new Error("No se pudo generar la imagen optimizada.");
  }

  const extension = mimeType === "image/webp" ? "webp" : "jpg";
  const nameWithoutExtension = file.name.replace(/\.[^.]+$/, "");
  const compressedFile = new File(
    [blob],
    `${nameWithoutExtension}-optimizado.${extension}`,
    {
      type: mimeType,
      lastModified: Date.now(),
    },
  );

  return {
    file: compressedFile,
    meta: {
      name: compressedFile.name,
      size: compressedFile.size,
      format: compressedFile.type || mimeType,
      width,
      height,
    },
  };
}