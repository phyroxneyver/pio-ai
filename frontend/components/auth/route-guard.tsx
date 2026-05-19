"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { getToken } from "@/lib/session";

export function RouteGuard({
    children,
}: {
    children: React.ReactNode;
}) {
    const router = useRouter();
    const pathname = usePathname();
    const [checking, setChecking] = useState(true);

    useEffect(() => {
        const timer = window.setTimeout(() => {
            const token = getToken();

            if (!token) {
                router.replace(`/login?redirect=${encodeURIComponent(pathname || "/")}`);
                return;
            }

            setChecking(false);
        }, 0);

        return () => window.clearTimeout(timer);
    }, [pathname, router]);

    if (checking) {
        return (
            <div className="flex min-h-screen items-center justify-center px-4">
                <div className="glass-card w-full max-w-sm rounded-[32px] p-8 text-center">
                    <div className="mx-auto h-14 w-14 animate-spin rounded-full border-[5px] border-[var(--egg)] border-t-[var(--primary-strong)]" />
                    <h2 className="mt-5 text-xl font-semibold">Verificando sesión</h2>
                    <p className="mt-2 text-sm text-[var(--muted)]">
                        Espera un momento...
                    </p>
                </div>
            </div>
        );
    }

    return <>{children}</>;
}