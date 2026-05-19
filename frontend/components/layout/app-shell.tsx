import { ReactNode } from "react";

type AppShellProps = {
  children: ReactNode;
  header?: ReactNode;
  sidebar?: ReactNode;
  tabBar?: ReactNode;
};

export function AppShell({
  children,
  header,
  sidebar,
  tabBar,
}: AppShellProps) {
  return (
    <div className="min-h-screen bg-[var(--background)] text-[var(--foreground)]">
      <div className="mx-auto flex min-h-screen w-full max-w-[1600px] flex-col px-2 pb-24 pt-2 sm:px-4 sm:pb-28 sm:pt-3 lg:px-5 xl:px-6">
        {header}

        <div className="mt-4 flex w-full flex-1 gap-4 sm:mt-5 xl:gap-5">
          {sidebar ? (
            <aside className="hidden w-[270px] shrink-0 lg:block xl:w-[290px]">
              {sidebar}
            </aside>
          ) : null}

          <main className="min-w-0 flex-1">{children}</main>
        </div>

        {tabBar}
      </div>
    </div>
  );
}
