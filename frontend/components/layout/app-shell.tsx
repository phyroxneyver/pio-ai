import { ReactNode } from "react";

type AppShellProps = {
  children: ReactNode;
  header?: ReactNode;
  mobileNav?: ReactNode;
};

export function AppShell({ children, header, mobileNav }: AppShellProps) {
  return (
    <div className="min-h-screen text-[var(--foreground)]">
      <div className="mx-auto flex min-h-screen w-full max-w-7xl flex-col px-3 pb-24 pt-3 sm:px-5 lg:px-6">
        {header}

        <main className="flex-1 py-5">
          {children}
        </main>

        {mobileNav}
      </div>
    </div>
  );
}