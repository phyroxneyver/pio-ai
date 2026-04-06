export default function Loading() {
  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <div className="glass-card flex w-full max-w-sm flex-col items-center rounded-[32px] p-8 text-center shadow-[0_18px_40px_rgba(0,0,0,0.08)]">
        <div className="h-14 w-14 animate-spin rounded-full border-[5px] border-[var(--egg)] border-t-[var(--primary-strong)]" />
        <h2 className="mt-5 text-xl font-semibold">Cargando datos</h2>
        <p className="mt-2 text-sm text-[var(--muted)]">
          Estamos obteniendo la información del sistema.
        </p>
      </div>
    </div>
  );
}