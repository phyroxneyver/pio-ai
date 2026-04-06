type SpinnerProps = {
    label?: string;
};

export function Spinner({
    label = "Cargando información...",
}: SpinnerProps) {
    return (
        <div className="flex min-h-[240px] items-center justify-center px-4">
            <div className="glass-card w-full max-w-sm rounded-[28px] p-8 text-center shadow-[0_18px_40px_rgba(0,0,0,0.08)]">
                <div className="mx-auto h-14 w-14 animate-spin rounded-full border-[5px] border-[var(--egg)] border-t-[var(--primary-strong)]" />
                <p className="mt-5 text-sm font-medium text-[var(--muted)]">{label}</p>
            </div>
        </div>
    );
}