type UploadProgressProps = {
  progress: number;
  label?: string;
};

export function UploadProgress({
  progress,
  label = "Subiendo imagen...",
}: UploadProgressProps) {
  const safeProgress = Math.max(0, Math.min(progress, 100));

  return (
    <div className="rounded-[24px] bg-[var(--card-strong)] p-4 ring-1 ring-black/5 dark:ring-white/10">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm font-medium text-[var(--foreground)]">{label}</p>
        <span className="text-sm font-semibold text-[var(--primary-strong)]">
          {safeProgress}%
        </span>
      </div>

      <div className="mt-3 h-3 w-full overflow-hidden rounded-full bg-black/5 dark:bg-white/10">
        <div
          className="h-full rounded-full bg-[var(--primary)] transition-all duration-300"
          style={{ width: `${safeProgress}%` }}
        />
      </div>
    </div>
  );
}