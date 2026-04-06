import { Egg } from "lucide-react";

type LogoMarkProps = {
    showText?: boolean;
    iconOnly?: boolean;
    className?: string;
};

export function LogoMark({
    showText = true,
    iconOnly = false,
    className = "",
}: LogoMarkProps) {
    const onlyIcon = iconOnly || !showText;

    return (
        <div className={`flex min-w-0 items-center gap-3 ${className}`}>
            <div className="relative flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-white shadow-sm ring-1 ring-black/5 transition-transform duration-300 hover:scale-105 dark:bg-neutral-900 dark:ring-white/10">
                <div className="relative">
                    <Egg className="h-7 w-7 text-[var(--primary-strong)]" strokeWidth={2.2} />
                    <div className="absolute left-1/2 top-1/2 h-2.5 w-2.5 -translate-x-1/2 -translate-y-1/2 rounded-full bg-[var(--egg)]" />
                </div>
            </div>

            {!onlyIcon && (
                <div className="min-w-0 leading-tight">
                    <p className="truncate text-xs font-semibold uppercase tracking-[0.22em] text-[var(--muted-strong)]">
                        Sistema Avícola
                    </p>
                    <h1 className="truncate text-base font-semibold tracking-tight text-[var(--foreground)]">
                        PIO AI
                    </h1>
                </div>
            )}
        </div>
    );
}