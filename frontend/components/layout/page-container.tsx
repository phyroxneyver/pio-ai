import { ReactNode } from "react";
import { Sidebar } from "./Sidebar";
import { MobileNav } from "./mobile-nav";

type PageContainerProps = {
  children: ReactNode;
};

export function PageContainer({ children }: PageContainerProps) {
  return (
    <div className="min-h-screen bg-[#0a0a0a]">
      {/* Sidebar solo en escritorio */}
      <Sidebar />

      {/* Contenido principal */}
      <div className="lg:ml-64 flex flex-col min-h-screen">
        <main className="flex-1 px-4 py-6 sm:px-6">
          {children}
        </main>
      </div>

      {/* Nav inferior solo en móvil */}
      <MobileNav />
    </div>
  );
}