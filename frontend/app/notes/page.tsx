"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/layout/app-shell";
import { DeleteNoteDialog } from "@/components/notes/delete-note-dialog";
import { useAuthenticatedUser } from "@/hooks/use-authenticated-user";
import { ApiError } from "@/lib/api";
import { removeAccessToken } from "@/lib/auth-storage";
import { listCompanies } from "@/lib/companies-api";
import { listContacts } from "@/lib/contacts-api";
import { listLeads } from "@/lib/leads-api";
import { deleteNote as deleteNoteRecord, listNotes } from "@/lib/notes-api";
import type { Company } from "@/types/company";
import type { Contact } from "@/types/contact";
import type { Lead } from "@/types/lead";
import type { Note } from "@/types/note";

type RelationshipFilter = "" | "company" | "contact" | "lead";

export default function NotesPage() {
  const router = useRouter();

  const {
    user,
    token,
    isLoading: isAuthenticationLoading,
    errorMessage: authenticationError,
  } = useAuthenticatedUser();

  const [notes, setNotes] = useState<Note[]>([]);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [leads, setLeads] = useState<Lead[]>([]);

  const [relationshipFilter, setRelationshipFilter] =
    useState<RelationshipFilter>("");

  const [isDataLoading, setIsDataLoading] = useState(true);
  const [dataError, setDataError] = useState("");

  const [noteToDelete, setNoteToDelete] = useState<Note | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState("");

  useEffect(() => {
    if (!token) {
      return;
    }

    let cancelled = false;

    async function loadNoteData(accessToken: string) {
      try {
        const [noteRecords, companyRecords, contactRecords, leadRecords] =
          await Promise.all([
            listNotes(accessToken),
            listCompanies(accessToken),
            listContacts(accessToken),
            listLeads(accessToken),
          ]);

        if (!cancelled) {
          setNotes(noteRecords);
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
          error instanceof ApiError ? error.message : "Unable to load notes.",
        );
        setIsDataLoading(false);
      }
    }

    void loadNoteData(token);

    return () => {
      cancelled = true;
    };
  }, [router, token]);

  const companyNamesById = new Map(
    companies.map((company) => [company.id, company.name]),
  );

  const contactNamesById = new Map(
    contacts.map((contact) => [
      contact.id,
      [contact.first_name, contact.last_name].filter(Boolean).join(" "),
    ]),
  );

  const leadTitlesById = new Map(leads.map((lead) => [lead.id, lead.title]));

  const filteredNotes = notes.filter((note) => {
    if (!relationshipFilter) {
      return true;
    }

    if (relationshipFilter === "company") {
      return note.company_id !== null;
    }

    if (relationshipFilter === "contact") {
      return note.contact_id !== null;
    }

    return note.lead_id !== null;
  });

  function getRelatedRecord(note: Note) {
    if (note.company_id !== null) {
      return {
        type: "Company",
        name: companyNamesById.get(note.company_id) ?? "Unknown company",
      };
    }

    if (note.contact_id !== null) {
      return {
        type: "Contact",
        name: contactNamesById.get(note.contact_id) ?? "Unknown contact",
      };
    }

    if (note.lead_id !== null) {
      return {
        type: "Lead",
        name: leadTitlesById.get(note.lead_id) ?? "Unknown lead",
      };
    }

    return {
      type: "Record",
      name: "Unknown record",
    };
  }

  function openDeleteDialog(note: Note) {
    setDeleteError("");
    setNoteToDelete(note);
  }

  function closeDeleteDialog() {
    if (isDeleting) {
      return;
    }

    setDeleteError("");
    setNoteToDelete(null);
  }

  async function handleDeleteNote() {
    if (!token || !noteToDelete) {
      return;
    }

    setDeleteError("");
    setIsDeleting(true);

    try {
      await deleteNoteRecord(noteToDelete.id, token);

      setNotes((currentNotes) =>
        currentNotes.filter((note) => note.id !== noteToDelete.id),
      );

      setNoteToDelete(null);
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        removeAccessToken();
        router.replace("/login");
        return;
      }

      setDeleteError(
        error instanceof ApiError
          ? error.message
          : "Unable to delete the note.",
      );
    } finally {
      setIsDeleting(false);
    }
  }

  if (isAuthenticationLoading || !user || !token) {
    if (authenticationError) {
      return (
        <main className="flex min-h-screen items-center justify-center bg-slate-950 px-4">
          <p className="text-sm text-red-300">{authenticationError}</p>
        </main>
      );
    }

    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-950">
        <p className="text-sm text-slate-400">Loading notes...</p>
      </main>
    );
  }

  return (
    <AppShell user={user}>
      <section className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-sm font-medium text-blue-400">Activity</p>

          <h1 className="mt-1 text-3xl font-bold">Notes</h1>

          <p className="mt-2 text-sm text-slate-400">
            Record information about companies, contacts, and leads.
          </p>
        </div>

        <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
          <label className="text-sm text-slate-300">
            <span className="mb-2 block">Related record</span>

            <select
              className="min-w-44 rounded-lg border border-slate-700 bg-slate-900 px-4 py-3 text-sm text-white outline-none focus:border-blue-500"
              onChange={(event) =>
                setRelationshipFilter(event.target.value as RelationshipFilter)
              }
              value={relationshipFilter}
            >
              <option value="">All records</option>
              <option value="company">Companies</option>
              <option value="contact">Contacts</option>
              <option value="lead">Leads</option>
            </select>
          </label>

          <Link
            className="rounded-lg bg-blue-600 px-5 py-3 text-center text-sm font-semibold text-white transition hover:bg-blue-500"
            href="/notes/new"
          >
            Add note
          </Link>
        </div>
      </section>

      <p className="mt-5 text-sm text-slate-400">
        Total notes:{" "}
        <span className="font-semibold text-white">{filteredNotes.length}</span>
      </p>

      {isDataLoading && (
        <section className="mt-8 rounded-2xl border border-slate-800 bg-slate-900 p-8 text-center">
          <p className="text-sm text-slate-400">Loading note records...</p>
        </section>
      )}

      {!isDataLoading && dataError && (
        <section className="mt-8 rounded-2xl border border-red-500/30 bg-red-500/10 p-6">
          <h2 className="font-semibold text-red-300">Notes unavailable</h2>

          <p className="mt-2 text-sm text-red-200">{dataError}</p>
        </section>
      )}

      {!isDataLoading && !dataError && filteredNotes.length === 0 && (
        <section className="mt-8 rounded-2xl border border-dashed border-slate-700 bg-slate-900 p-10 text-center">
          <h2 className="text-lg font-semibold">No notes found</h2>

          <p className="mt-2 text-sm text-slate-400">
            Create a note or select a different relationship filter.
          </p>
        </section>
      )}

      {!isDataLoading && !dataError && filteredNotes.length > 0 && (
        <section className="mt-8 grid gap-5 lg:grid-cols-2">
          {filteredNotes.map((note) => {
            const relatedRecord = getRelatedRecord(note);
            const isOwnNote = note.author_id === user.id;

            return (
              <article
                className="rounded-2xl border border-slate-800 bg-slate-900 p-6"
                key={note.id}
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wider text-blue-400">
                      {relatedRecord.type}
                    </p>

                    <h2 className="mt-1 font-semibold text-white">
                      {relatedRecord.name}
                    </h2>
                  </div>

                  {isOwnNote ? (
                    <div className="flex items-center gap-4">
                      <Link
                        className="text-sm font-semibold text-blue-400 transition hover:text-blue-300"
                        href={`/notes/${note.id}/edit`}
                      >
                        Edit
                      </Link>

                      <button
                        className="text-sm font-semibold text-red-400 transition hover:text-red-300"
                        onClick={() => openDeleteDialog(note)}
                        type="button"
                      >
                        Delete
                      </button>
                    </div>
                  ) : (
                    <span className="text-xs font-medium text-slate-500">
                      Read only
                    </span>
                  )}
                </div>

                <p className="mt-5 whitespace-pre-wrap text-sm leading-6 text-slate-300">
                  {note.body}
                </p>

                <div className="mt-6 border-t border-slate-800 pt-4 text-xs text-slate-500">
                  <p>Author: {isOwnNote ? "You" : `User #${note.author_id}`}</p>

                  <p className="mt-1">
                    {new Date(note.created_at).toLocaleString()}
                  </p>
                </div>
              </article>
            );
          })}
        </section>
      )}

      {noteToDelete && (
        <DeleteNoteDialog
          errorMessage={deleteError}
          isDeleting={isDeleting}
          note={noteToDelete}
          onCancel={closeDeleteDialog}
          onConfirm={handleDeleteNote}
        />
      )}
    </AppShell>
  );
}
