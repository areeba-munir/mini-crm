"use client";

type DeleteTaskDialogProps = {
  taskTitle: string;
  errorMessage: string;
  isDeleting: boolean;
  onCancel: () => void;
  onConfirm: () => Promise<void>;
};

export function DeleteTaskDialog({
  taskTitle,
  errorMessage,
  isDeleting,
  onCancel,
  onConfirm,
}: DeleteTaskDialogProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 px-4 backdrop-blur-sm">
      <section
        aria-labelledby="delete-task-title"
        aria-modal="true"
        className="w-full max-w-md rounded-2xl border border-slate-700 bg-slate-900 p-6 shadow-2xl"
        role="dialog"
      >
        <p className="text-sm font-medium text-red-400">
          Delete task
        </p>

        <h2
          className="mt-2 text-xl font-bold text-white"
          id="delete-task-title"
        >
          Delete {taskTitle}?
        </h2>

        <p className="mt-3 text-sm leading-6 text-slate-400">
          This action permanently removes the task
          from the CRM. It cannot be undone.
        </p>

        {errorMessage && (
          <div
            className="mt-5 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300"
            role="alert"
          >
            {errorMessage}
          </div>
        )}

        <div className="mt-6 flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
          <button
            className="rounded-lg border border-slate-700 px-5 py-3 text-sm font-semibold text-slate-200 transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
            disabled={isDeleting}
            onClick={onCancel}
            type="button"
          >
            Cancel
          </button>

          <button
            className="rounded-lg bg-red-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-red-500 disabled:cursor-not-allowed disabled:bg-slate-700"
            disabled={isDeleting}
            onClick={() => void onConfirm()}
            type="button"
          >
            {isDeleting
              ? "Deleting..."
              : "Delete task"}
          </button>
        </div>
      </section>
    </div>
  );
}