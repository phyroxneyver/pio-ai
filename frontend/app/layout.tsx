import type { Metadata } from "next";
import "./globals.css";
import { AppThemeProvider } from "@/components/theme/theme-provider";
import { ToastProvider } from "@/components/ui/toast-provider";

export const metadata: Metadata = {
  title: "PIO AI",
  description: "Plataforma de monitoreo y control avícola con IA",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es" suppressHydrationWarning data-scroll-behavior="smooth">
      <body className="antialiased">
        <AppThemeProvider>
          <ToastProvider>{children}</ToastProvider>
        </AppThemeProvider>
      </body>
    </html>
  );
}
