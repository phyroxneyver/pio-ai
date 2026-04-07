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
            <div className="mx-auto flex min-h-screen w-full max-w-[1600px] flex-col px-3 pb-24 pt-3 sm:px-5 lg:px-6">
                {header}

                <div className="mt-5 flex flex-1 gap-5">
                    {sidebar ? (
                        <aside className="hidden xl:block xl:w-[290px] xl:shrink-0">
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