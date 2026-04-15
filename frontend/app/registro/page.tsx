"use client";

import { useState } from "react";
import { fetchWithAuth } from "@/lib/api";
import { CounterButton } from "@/components/ui/CounterButton";
import { AppShell } from "@/components/layout/app-shell";
import { AppHeader } from "@/components/header/app-header";
import { Sidebar } from "@/components/layout/sidebar";
import { TabBar } from "@/components/layout/tab-bar";
import { PageContainer } from "@/components/layout/page-container";
import { RouteGuard } from "@/components/auth/route-guard";
import { ClipboardList, CheckCircle } from "lucide-react";

export default function RegistroPage() {
  const [pollitos, setPollitos] = useState(0);
  const [gallinas, setGallinas] = useState(0);
  const [huevos, setHuevos] = useState(0);
  const [notas, setNotas] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess(false);

    // Tarea 4: validar que al menos un campo tenga valor
    if (pollitos === 0 && gallinas === 0 && huevos === 0) {
      setError("Debes registrar al menos un valor antes de guardar.");
      return;
    }

    try {
  setLoading(true);

  // Registrar aves (pollitos)
  if (pollitos > 0) {
    await fetchWithAuth("/aves", {
      method: "POST",
      body: JSON.stringify({ tipo: "pollito", cantidad: pollitos, notas }),
    });
  }

  // Registrar aves (gallinas)
  if (gallinas > 0) {
    await fetchWithAuth("/aves", {
      method: "POST",
      body: JSON.stringify({ tipo: "gallina", cantidad: gallinas, notas }),
    });
  }

  // Registrar huevos - necesita ave_id, usamos 1 por defecto
  if (huevos > 0) {
    await fetchWithAuth("/produccion-huevos", {
      method: "POST",
      body: JSON.stringify({ ave_id: 1, cantidad_huevos: huevos, notas }),
    });
  }

  setSuccess(true);
  setPollitos(0);
  setGallinas(0);
  setHuevos(0);
  setNotas("");
  setTimeout(() => setSuccess(false), 4000);
} catch {
  setError("Error de conexión. Intenta de nuevo.");
} finally {
  setLoading(false);
}
  };

  return (
    <RouteGuard>
      <AppShell
        header={<AppHeader />}
        sidebar={<Sidebar />}
        tabBar={<TabBar />}
      >
        <PageContainer>
          <div className="mx-auto max-w-xl">

            {/* Título */}
            <div className="mb-8">
              <span className="inline-flex items-center gap-2 rounded-full bg-[var(--egg)] px-3 py-1 text-xs font-semibold text-[var(--primary-strong)]">
                <ClipboardList className="h-3.5 w-3.5" />
                Registro del día
              </span>
              <h1 className="mt-3 text-3xl font-semibold tracking-tight">
                ¿Cuántos hay hoy?
              </h1>
              <p className="mt-2 text-sm text-[var(--muted)]">
                Registra el conteo manual de aves y huevos del día.
              </p>
            </div>

            {/* Confirmación de éxito - Tarea 3 */}
            {success && (
              <div className="mb-6 flex items-center gap-3 rounded-2xl bg-green-500/10 border border-green-500/20 px-4 py-4">
                <CheckCircle className="h-5 w-5 text-green-500 shrink-0" />
                <p className="text-sm font-semibold text-green-500">
                  ¡Datos guardados correctamente!
                </p>
              </div>
            )}

            {/* Error */}
            {error && (
              <div className="mb-6 rounded-2xl bg-red-500/10 border border-red-500/20 px-4 py-4">
                <p className="text-sm font-semibold text-red-400">{error}</p>
              </div>
            )}

            {/* Formulario */}
            <form onSubmit={handleSubmit} className="glass-card rounded-[32px] p-6 sm:p-8 space-y-8">

              {/* Contadores - Tarea 1 */}
              <CounterButton
                label="Pollitos"
                value={pollitos}
                onChange={setPollitos}
              />

              <CounterButton
                label="Gallinas"
                value={gallinas}
                onChange={setGallinas}
              />

              <CounterButton
                label="Huevos"
                value={huevos}
                onChange={setHuevos}
              />

              {/* Notas */}
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium text-[var(--muted)] uppercase tracking-widest">
                  Notas (opcional)
                </label>
                <textarea
                  value={notas}
                  onChange={(e) => setNotas(e.target.value)}
                  placeholder="Ej: Se encontraron 2 aves enfermas..."
                  rows={3}
                  className="w-full rounded-2xl border border-black/10 dark:border-white/10 bg-[var(--card-strong)] px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-[var(--primary-strong)] resize-none"
                />
              </div>

              {/* Botón guardar */}
              <button
                type="submit"
                disabled={loading}
                className="primary-button w-full rounded-2xl py-4 text-sm font-semibold transition duration-300 hover:-translate-y-0.5 disabled:opacity-70"
              >
                {loading ? "Guardando..." : "Guardar registro"}
              </button>
            </form>
          </div>
        </PageContainer>
      </AppShell>
    </RouteGuard>
  );
}