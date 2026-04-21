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
import { ClipboardList, CheckCircle, Baby, Bird, Egg } from "lucide-react";

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

    if (pollitos === 0 && gallinas === 0 && huevos === 0) {
      setError("Debes registrar al menos un valor antes de guardar.");
      return;
    }

    try {
      setLoading(true);

      if (pollitos > 0) {
        await fetchWithAuth("/aves", {
          method: "POST",
          body: JSON.stringify({ tipo: "pollito", cantidad: pollitos, notas }),
        });
      }

      if (gallinas > 0) {
        await fetchWithAuth("/aves", {
          method: "POST",
          body: JSON.stringify({ tipo: "gallina", cantidad: gallinas, notas }),
        });
      }

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

  const total = pollitos + gallinas + huevos;

  return (
    <RouteGuard>
      <AppShell header={<AppHeader />} sidebar={<Sidebar />} tabBar={<TabBar />}>
        <PageContainer>
          <div className="w-full space-y-6">

            {/* Título */}
            <div>
              <span className="inline-flex items-center gap-2 rounded-full bg-[var(--egg)] px-3 py-1 text-xs font-semibold text-[var(--primary-strong)]">
                <ClipboardList className="h-3.5 w-3.5" />
                Registro del día
              </span>
              <h1 className="mt-3 text-3xl font-semibold tracking-tight">¿Cuántos hay hoy?</h1>
              <p className="mt-1 text-sm text-[var(--muted)]">Registra el conteo manual de aves y huevos del día.</p>
            </div>

            {/* Mensajes */}
            {success && (
              <div className="flex items-center gap-3 rounded-2xl bg-green-500/10 border border-green-500/20 px-4 py-4">
                <CheckCircle className="h-5 w-5 text-green-500 shrink-0" />
                <p className="text-sm font-semibold text-green-500">¡Datos guardados correctamente!</p>
              </div>
            )}
            {error && (
              <div className="rounded-2xl bg-red-500/10 border border-red-500/20 px-4 py-4">
                <p className="text-sm font-semibold text-red-400">{error}</p>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">

              {/* Grid de contadores */}
              <div className="grid gap-4 sm:grid-cols-3">
                {/* Pollitos */}
                <div className="glass-card rounded-[28px] p-6 space-y-4">
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-yellow-500/10">
                      <Baby className="h-5 w-5 text-yellow-500" />
                    </div>
                    <div>
                      <p className="text-sm font-semibold">Pollitos</p>
                      <p className="text-xs text-[var(--muted)]">Crías recientes</p>
                    </div>
                  </div>
                  <CounterButton label="" value={pollitos} onChange={setPollitos} />
                </div>

                {/* Gallinas */}
                <div className="glass-card rounded-[28px] p-6 space-y-4">
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-orange-500/10">
                      <Bird className="h-5 w-5 text-orange-500" />
                    </div>
                    <div>
                      <p className="text-sm font-semibold">Gallinas</p>
                      <p className="text-xs text-[var(--muted)]">Aves adultas</p>
                    </div>
                  </div>
                  <CounterButton label="" value={gallinas} onChange={setGallinas} />
                </div>

                {/* Huevos */}
                <div className="glass-card rounded-[28px] p-6 space-y-4">
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--egg)]">
                      <Egg className="h-5 w-5 text-[var(--primary-strong)]" />
                    </div>
                    <div>
                      <p className="text-sm font-semibold">Huevos</p>
                      <p className="text-xs text-[var(--muted)]">Producción del día</p>
                    </div>
                  </div>
                  <CounterButton label="" value={huevos} onChange={setHuevos} />
                </div>
              </div>

              {/* Resumen total */}
              {total > 0 && (
                <div className="glass-card rounded-[24px] px-5 py-4 flex items-center justify-between">
                  <p className="text-sm font-medium text-[var(--muted)]">Total a registrar</p>
                  <span className="text-2xl font-black">{total}</span>
                </div>
              )}

              {/* Notas */}
              <div className="glass-card rounded-[28px] p-6 space-y-3">
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
                className="primary-button w-full rounded-2xl py-4 text-base font-semibold transition duration-300 hover:-translate-y-0.5 disabled:opacity-70 min-h-[56px]"
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