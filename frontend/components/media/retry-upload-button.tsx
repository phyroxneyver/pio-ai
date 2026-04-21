import { RefreshCw } from "lucide-react";

type RetryUploadButtonProps = {
  onRetry: () => void;
  disabled?: boolean;
};

export function RetryUploadButton({
  onRetry,
  disabled = false,
}: RetryUploadButtonProps) {
  return (
    <button
      onClick={onRetry}
      disabled={disabled}
      className="secondary-button inline-flex w-full items-center justify-center gap-2 rounded-2xl px-4 py-3 text-sm font-semibold transition duration-300 hover:-translate-y-0.5 disabled:opacity-60 sm:w-auto"
    >
      <RefreshCw className="h-4 w-4" />
      Reintentar
    </button>
  );
}