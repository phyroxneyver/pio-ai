"use client";

import {
  createContext,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { AlertCircle, CheckCircle2, Info, X } from "lucide-react";

type ToastType = "success" | "error" | "info";

type ToastItem = {
  id: number;
  title: string;
  description?: string;
  type: ToastType;
};

type ToastContextType = {
  showToast: (toast: {
    title: string;
    description?: string;
    type?: ToastType;
  }) => void;
};

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  function removeToast(id: number) {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  }

  function showToast(toast: {
    title: string;
    description?: string;
    type?: ToastType;
  }) {
    const id = Date.now() + Math.floor(Math.random() * 1000);

    const newToast: ToastItem = {
      id,
      title: toast.title,
      description: toast.description,
      type: toast.type || "info",
    };

    setToasts((prev) => [...prev, newToast]);

    window.setTimeout(() => {
      removeToast(id);
    }, 3200);
  }

  const value = useMemo(
    () => ({
      showToast,
    }),
    [],
  );

  return (
    <ToastContext.Provider value={value}>
      {children}

      <div className="pointer-events-none fixed right-4 top-4 z-[9999] flex w-[calc(100%-32px)] max-w-sm flex-col gap-3">
        {toasts.map((toast) => {
          const icon =
            toast.type === "success" ? (
              <CheckCircle2 className="h-5 w-5 text-emerald-500" />
            ) : toast.type === "error" ? (
              <AlertCircle className="h-5 w-5 text-red-500" />
            ) : (
              <Info className="h-5 w-5 text-sky-500" />
            );

          return (
            <div
              key={toast.id}
              className="toast-enter pointer-events-auto rounded-[24px] border border-white/20 bg-white/80 p-4 shadow-[0_18px_40px_rgba(0,0,0,0.12)] backdrop-blur-xl dark:border-white/10 dark:bg-neutral-900/85"
            >
              <div className="flex items-start gap-3">
                <div className="mt-0.5 shrink-0">{icon}</div>

                <div className="min-w-0 flex-1">
                  <p className="text-sm font-semibold text-[var(--foreground)]">
                    {toast.title}
                  </p>

                  {toast.description ? (
                    <p className="mt-1 text-sm leading-5 text-[var(--muted)]">
                      {toast.description}
                    </p>
                  ) : null}
                </div>

                <button
                  onClick={() => removeToast(toast.id)}
                  className="rounded-full p-1 text-[var(--muted)] transition hover:bg-black/5 hover:text-[var(--foreground)] dark:hover:bg-white/5"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);

  if (!context) {
    throw new Error("useToast debe usarse dentro de ToastProvider");
  }

  return context;
}