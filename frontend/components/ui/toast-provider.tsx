"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";

export type ToastType = "success" | "error" | "info";

type Toast = {
  id: number;
  message: string;
  type: ToastType;
};

type ToastContextValue = {
  showToast: (message: string, type?: ToastType) => void;
};

type ToastProviderProps = {
  children: ReactNode;
};

const ToastContext = createContext<ToastContextValue | null>(null);

let nextToastId = 1;

export function ToastProvider({ children }: ToastProviderProps) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const removeToast = useCallback((toastId: number) => {
    setToasts((currentToasts) =>
      currentToasts.filter((toast) => toast.id !== toastId),
    );
  }, []);

  const showToast = useCallback(
    (message: string, type: ToastType = "success") => {
      const toastId = nextToastId;
      nextToastId += 1;

      const newToast: Toast = {
        id: toastId,
        message,
        type,
      };

      setToasts((currentToasts) => [...currentToasts.slice(-3), newToast]);

      window.setTimeout(() => {
        removeToast(toastId);
      }, 4000);
    },
    [removeToast],
  );

  const contextValue = useMemo(
    () => ({
      showToast,
    }),
    [showToast],
  );

  return (
    <ToastContext.Provider value={contextValue}>
      {children}

      <div
        aria-label="Notifications"
        className="pointer-events-none fixed right-4 top-4 z-[100] flex w-[calc(100%-2rem)] max-w-sm flex-col gap-3"
      >
        {toasts.map((toast) => {
          const colorClasses =
            toast.type === "success"
              ? "border-emerald-500/40 bg-emerald-950 text-emerald-100"
              : toast.type === "error"
                ? "border-red-500/40 bg-red-950 text-red-100"
                : "border-blue-500/40 bg-blue-950 text-blue-100";

          return (
            <div
              className={`pointer-events-auto flex items-start justify-between gap-4 rounded-xl border px-4 py-3 shadow-2xl ${colorClasses}`}
              key={toast.id}
              role={toast.type === "error" ? "alert" : "status"}
            >
              <p className="text-sm leading-6">{toast.message}</p>

              <button
                aria-label="Dismiss notification"
                className="shrink-0 rounded p-1 opacity-70 transition hover:bg-white/10 hover:opacity-100"
                onClick={() => removeToast(toast.id)}
                type="button"
              >
                <svg
                  aria-hidden="true"
                  className="h-4 w-4"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  viewBox="0 0 24 24"
                >
                  <path d="M6 6l12 12M18 6 6 18" strokeLinecap="round" />
                </svg>
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast(): ToastContextValue {
  const context = useContext(ToastContext);

  if (!context) {
    throw new Error("useToast must be used inside ToastProvider.");
  }

  return context;
}
