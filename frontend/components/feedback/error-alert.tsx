import { AlertCircle } from "lucide-react";

type ErrorAlertProps = {
    title?: string;
    message: string;
};

export function ErrorAlert({
    title = "Ocurrió un problema",
    message,
}: ErrorAlertProps) {
    return (
        <div className="rounded-[24px] border border-red-500/15 bg-red-500/10 p-4 text-red-700 dark:text-red-300">
            <div className="flex items-start gap-3">
                <AlertCircle className="mt-0.5 h-5 w-5 shrink-0" />
                <div>
                    <p className="text-sm font-semibold">{title}</p>
                    <p className="mt-1 text-sm leading-6">{message}</p>
                </div>
            </div>
        </div>
    );
}