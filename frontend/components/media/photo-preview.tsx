import { ImageIcon, Trash2 } from "lucide-react";
import { formatBytes } from "@/lib/image-compression";
import type { ImageMeta } from "@/types/media";

type PhotoPreviewProps = {
  previewUrl: string;
  originalMeta: ImageMeta;
  compressedMeta?: ImageMeta | null;
  onRemove?: () => void;
};

export function PhotoPreview({
  previewUrl,
  originalMeta,
  compressedMeta,
  onRemove,
}: PhotoPreviewProps) {
  return (
    <div className="glass-card rounded-[32px] p-5 shadow-[0_18px_40px_rgba(0,0,0,0.06)]">
      <div className="flex flex-col gap-5 lg:flex-row">
        <div className="w-full lg:max-w-[360px]">
          <div className="overflow-hidden rounded-[24px] bg-[var(--card-strong)] ring-1 ring-black/5 dark:ring-white/10">
            <img
              src={previewUrl}
              alt="Previsualización de la fotografía"
              className="h-[260px] w-full object-cover"
            />
          </div>
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-3">
            <div className="min-w-0">
              <p className="text-sm font-medium text-[var(--muted)]">
                Previsualización
              </p>
              <h3 className="mt-1 flex items-center gap-2 text-xl font-semibold tracking-tight">
                <ImageIcon className="h-5 w-5 text-[var(--primary-strong)]" />
                Foto lista para enviar
              </h3>
            </div>

            {onRemove ? (
              <button
                onClick={onRemove}
                className="secondary-button inline-flex shrink-0 items-center gap-2 rounded-2xl px-3 py-2 text-sm font-medium"
              >
                <Trash2 className="h-4 w-4" />
                Quitar
              </button>
            ) : null}
          </div>

          <div className="mt-5 grid gap-3 sm:grid-cols-2">
            <div className="rounded-[24px] bg-[var(--card-strong)] p-4 ring-1 ring-black/5 dark:ring-white/10">
              <p className="text-sm text-[var(--muted)]">Archivo original</p>
              <p className="mt-2 break-all text-sm font-semibold">
                {originalMeta.name}
              </p>
              <p className="mt-2 text-sm text-[var(--muted)]">
                {formatBytes(originalMeta.size)}
              </p>
              <p className="mt-1 text-sm text-[var(--muted)]">
                {originalMeta.format || "image/*"}
              </p>
            </div>

            <div className="rounded-[24px] bg-[var(--card-strong)] p-4 ring-1 ring-black/5 dark:ring-white/10">
              <p className="text-sm text-[var(--muted)]">Archivo optimizado</p>

              {compressedMeta ? (
                <>
                  <p className="mt-2 break-all text-sm font-semibold">
                    {compressedMeta.name}
                  </p>
                  <p className="mt-2 text-sm text-[var(--muted)]">
                    {formatBytes(compressedMeta.size)}
                  </p>
                  <p className="mt-1 text-sm text-[var(--muted)]">
                    {compressedMeta.format}
                  </p>
                </>
              ) : (
                <p className="mt-2 text-sm text-[var(--muted)]">
                  Aún no se ha comprimido la imagen.
                </p>
              )}
            </div>
          </div>

          {compressedMeta?.width && compressedMeta?.height ? (
            <div className="mt-3 rounded-[24px] bg-[var(--card-strong)] p-4 ring-1 ring-black/5 dark:ring-white/10">
              <p className="text-sm text-[var(--muted)]">Resolución final</p>
              <p className="mt-2 text-sm font-semibold">
                {compressedMeta.width} × {compressedMeta.height} px
              </p>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}