import { ReactNode } from "react";

export function PageContainer({
    children,
    className = "",
}: {
    children: ReactNode;
    className?: string;
}) {
    return (
        <div className={`w-full max-w-full overflow-x-hidden ${className}`}>
            {children}
        </div>
    );
}