"use client";

import type { Note } from "@/types/note";

type DeleteNoteDialogProps = {
  note: Note;
  isDeleting: boolean;
  errorMessage: string;
  onCancel: () => void;
  onConfirm: () => void | Promise<void>;
};

export function DeleteNoteDialog({
  note,
  isDeleting,
  errorMessage,
  onCancel,
  onConfirm,
}: DeleteNoteDialogProps) {
  function handleBackdropClick() {
    if (!isDeleting) {
      onCancel();
    }
  }

  return (
    <div
      aria-labelledby="delete-note-title"
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 px-4 backdrop-blur-sm"
      onClick={handleBackdropClick}
      role="dialog"
    >
      <section
        className="w-full max-w-md rounded-2xl border border-slate-700 bg-slate-900 p-6 shadow-2xl"
        onClick={(event) => event.stopPropagation()}
      >
        <p className="text-sm font-medium text-red-400">Delete note</p>

        <h2
          className="mt-2 text-xl font-bold text-white"
          id="delete-note-title"
        >
          Delete this note?
        </h2>

        <p className="mt-3 text-sm leading-6 text-slate-400">
          This action permanently removes the note from the CRM and cannot be
          undone.
        </p>

        <blockquote className="mt-4 max-h-32 overflow-y-auto rounded-lg border border-slate-800 bg-slate-950 px-4 py-3 text-sm leading-6 text-slate-300">
          {note.body}
        </blockquote>

        {errorMessage && (
          <div
            className="mt-4 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300"
            role="alert"
          >
            {errorMessage}
          </div>
        )}

        <div className="mt-6 flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
          <button
            className="rounded-lg border border-slate-700 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
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
            {isDeleting ? "Deleting..." : "Delete note"}
          </button>
        </div>
      </section>
    </div>
  );
}
