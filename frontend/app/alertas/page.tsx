"use client";

import { AppShell } from "@/components/layout/app-shell";
import { AppHeader } from "@/components/header/app-header";
import { Sidebar } from "@/components/layout/sidebar";
import { TabBar } from "@/components/layout/tab-bar";
import { PageContainer } from "@/components/layout/page-container";
import { RouteGuard } from "@/components/auth/route-guard";
import { Bell, AlertTriangle } from "lucide-react";

export default function AlertasPage() {
  return (
    <RouteGuard>
      <AppShell header={<AppHeader />} sidebar={<Sidebar />} tabBar={<TabBar />}>
        <PageContainer>
          <div className="mx-auto max-w-3xl space-y-8">
            <div>
              <span className="inline-flex items-center gap-2 rounded-full bg-[var(--egg)] px-3 py-1 text-xs font-semibold text-[var(--primary-strong)]">
                <Bell className="h-3.5 w-3.5" />
                Alertas
              </span>
              <h1 className="mt-3 text-3xl font-semibold tracking-tight">Centro de alertas</h1>
              <p className="mt-2 text-sm text-[var(--muted)]">
                Aquí aparecerán las alertas cuando el conteo baje repentinamente.
              </p>
            </div>

            <div className="glass-card rounded-[32px] p-6">
              <div className="flex flex-col items-center gap-4 py-8 text-center">
                <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-[var(--egg)]">
                  <AlertTriangle className="h-8 w-8 text-[var(--primary-strong)]" />
                </div>
                <div>
                  <p className="font-semibold">Sin alertas activas</p>
                  <p className="mt-1 text-sm text-[var(--muted)]">
                    El sistema está operando normalmente.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </PageContainer>
      </AppShell>
    </RouteGuard>
  );
}