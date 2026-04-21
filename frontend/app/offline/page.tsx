export default function OfflinePage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-[#0a0a0a] px-4 text-center">
      <div className="flex h-20 w-20 items-center justify-center rounded-[2rem] bg-[var(--egg)] mb-6">
        <span className="text-4xl">🐣</span>
      </div>
      <h1 className="text-2xl font-black text-white">Sin conexión</h1>
      <p className="mt-3 text-sm text-zinc-400 max-w-xs">
        No hay internet disponible. Puedes seguir viendo los datos que ya cargaste,
        pero no podrás guardar nuevos registros hasta recuperar la conexión.
      </p>
      <button
        onClick={() => window.location.reload()}
        className="mt-8 primary-button rounded-2xl px-6 py-3 text-sm font-semibold min-h-[44px]"
      >
        Reintentar conexión
      </button>
    </div>
  );
}