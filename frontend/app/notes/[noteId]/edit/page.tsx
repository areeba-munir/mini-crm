"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { NoteForm } from "@/components/notes/note-form";
import { AppShell } from "@/components/layout/app-shell";
import { useAuthenticatedUser } from "@/hooks/use-authenticated-user";
import { ApiError } from "@/lib/api";
import { removeAccessToken } from "@/lib/auth-storage";
import { listCompanies } from "@/lib/companies-api";
import { listContacts } from "@/lib/contacts-api";
import { listLeads } from "@/lib/leads-api";
import { getNote, updateNote } from "@/lib/notes-api";
import type { Company } from "@/types/company";
import type { Contact } from "@/types/contact";
import type { Lead } from "@/types/lead";
import type { Note, NoteCreateInput } from "@/types/note";

export default function EditNotePage() {
  const params = useParams<{
    noteId: string;
  }>();
  const router = useRouter();

  const noteId = Number(params.noteId);
  const isNoteIdValid = Number.isInteger(noteId) && noteId >= 1;

  const {
    user,
    token,
    isLoading: isAuthenticationLoading,
    errorMessage: authenticationError,
  } = useAuthenticatedUser();

  const [note, setNote] = useState<Note | null>(null);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [isDataLoading, setIsDataLoading] = useState(true);
  const [dataError, setDataError] = useState("");

  useEffect(() => {
    if (!token || !isNoteIdValid) {
      return;
    }

    let cancelled = false;

    async function loadNoteData(accessToken: string) {
      try {
        const [noteRecord, companyRecords, contactRecords, leadRecords] =
          await Promise.all([
            getNote(noteId, accessToken),
            listCompanies(accessToken),
            listContacts(accessToken),
            listLeads(accessToken),
          ]);

        if (!cancelled) {
          setNote(noteRecord);
          setCompanies(companyRecords);
          setContacts(contactRecords);
          setLeads(leadRecords);
          setIsDataLoading(false);
        }
      } catch (error) {
        if (cancelled) {
          return;
        }

        if (error instanceof ApiError && error.status === 401) {
          removeAccessToken();
          router.replace("/login");
          return;
        }

        setDataError(
          error instanceof ApiError
            ? error.message
            : "Unable to load the note.",
        );
        setIsDataLoading(false);
      }
    }

    void loadNoteData(token);

    return () => {
      cancelled = true;
    };
  }, [isNoteIdValid, noteId, router, token]);

  if (isAuthenticationLoading || !user || !token) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-950 px-4">
        <p
          className={`text-sm ${
            authenticationError ? "text-red-300" : "text-slate-400"
          }`}
        >
          {authenticationError || "Loading note editor..."}
        </p>
      </main>
    );
  }

  if (!isNoteIdValid) {
    return (
      <AppShell user={user}>
        <section className="rounded-2xl border border-red-500/30 bg-red-500/10 p-6">
          <h1 className="text-lg font-semibold text-red-300">Invalid note</h1>

          <p className="mt-2 text-sm text-red-200">
            The note ID must be a positive number.
          </p>
        </section>
      </AppShell>
    );
  }

  if (isDataLoading) {
    return (
      <AppShell user={user}>
        <p className="text-sm text-slate-400">Loading note...</p>
      </AppShell>
    );
  }

  if (dataError || !note) {
    return (
      <AppShell user={user}>
        <section className="rounded-2xl border border-red-500/30 bg-red-500/10 p-6">
          <h1 className="text-lg font-semibold text-red-300">
            Note unavailable
          </h1>

          <p className="mt-2 text-sm text-red-200">
            {dataError || "The note could not be found."}
          </p>
        </section>
      </AppShell>
    );
  }

  async function handleUpdateNote(input: NoteCreateInput) {
    if (!token || !note) {
      throw new Error("Note or authentication data is unavailable.");
    }

    await updateNote(note.id, input, token);
    router.push("/notes");
  }

  return (
    <AppShell user={user}>
      <section className="mx-auto max-w-3xl">
        <div>
          <p className="text-sm font-medium text-blue-400">Notes</p>

          <h1 className="mt-1 text-3xl font-bold">Edit note</h1>

          <p className="mt-2 text-sm text-slate-400">
            Update the note text or its related CRM record.
          </p>
        </div>

        <div className="mt-8 rounded-2xl border border-slate-800 bg-slate-900 p-6 sm:p-8">
          <NoteForm
            cancelHref="/notes"
            companies={companies}
            contacts={contacts}
            initialValues={{
              body: note.body,
              company_id: note.company_id,
              contact_id: note.contact_id,
              lead_id: note.lead_id,
            }}
            leads={leads}
            onSubmit={handleUpdateNote}
            submitLabel="Save changes"
          />
        </div>
      </section>
    </AppShell>
  );
}
