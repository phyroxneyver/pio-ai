"use client";

type ErrorProps = {
    error: Error & { digest?: string };
    reset: () => void;
};

export default function Error({ error, reset }: ErrorProps) {
    return (
        <div className="flex min-h-screen items-center justify-center px-4">
            <div className="glass-card w-full max-w-md rounded-[32px] p-8 shadow-[0_18px_40px_rgba(0,0,0,0.08)]">
                <span className="rounded-full bg-red-500/10 px-3 py-1 text-xs font-semibold text-red-600 ring-1 ring-red-500/15 dark:text-red-300">
                    Error del sistema
                </span>

                <h2 className="mt-4 text-2xl font-semibold tracking-tight">
                    Ocurrió un problema
                </h2>

                <p className="mt-3 text-sm leading-6 text-[var(--muted)]">
                    {error.message || "No se pudo completar la acción solicitada."}
                </p>

                <div className="mt-6 flex gap-3">
                    <button
                        onClick={() => reset()}
                        className="primary-button rounded-2xl px-4 py-2 text-sm font-semibold"
                    >
                        Reintentar
                    </button>

                    <button className="secondary-button rounded-2xl px-4 py-2 text-sm font-medium">
                        Volver
                    </button>
                </div>
            </div>
        </div>
    );
}