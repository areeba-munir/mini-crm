"use client";

import Link from "next/link";
import type { FormEvent } from "react";
import { useState } from "react";

import { ApiError } from "@/lib/api";
import type { Company } from "@/types/company";
import type { Contact } from "@/types/contact";
import type { Lead } from "@/types/lead";
import type { NoteCreateInput } from "@/types/note";

type RelationshipType =
  | "company"
  | "contact"
  | "lead";

type NoteFormValues = {
  body: string;
  relationshipType: RelationshipType;
  relationshipId: string;
};

type NoteFormProps = {
  companies: Company[];
  contacts: Contact[];
  leads: Lead[];
  initialValues?: Partial<NoteCreateInput>;
  submitLabel: string;
  cancelHref: string;
  onSubmit: (
    input: NoteCreateInput,
  ) => Promise<void>;
};

const inputClassName =
  "w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white outline-none transition placeholder:text-slate-600 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 disabled:cursor-not-allowed disabled:opacity-60";

function getInitialRelationship(
  initialValues?: Partial<NoteCreateInput>,
): {
  type: RelationshipType;
  id: string;
} {
  if (initialValues?.company_id != null) {
    return {
      type: "company",
      id: String(initialValues.company_id),
    };
  }

  if (initialValues?.contact_id != null) {
    return {
      type: "contact",
      id: String(initialValues.contact_id),
    };
  }

  if (initialValues?.lead_id != null) {
    return {
      type: "lead",
      id: String(initialValues.lead_id),
    };
  }

  return {
    type: "company",
    id: "",
  };
}

export function NoteForm({
  companies,
  contacts,
  leads,
  initialValues,
  submitLabel,
  cancelHref,
  onSubmit,
}: NoteFormProps) {
  const initialRelationship =
    getInitialRelationship(initialValues);

  const [values, setValues] =
    useState<NoteFormValues>({
      body: initialValues?.body ?? "",
      relationshipType:
        initialRelationship.type,
      relationshipId:
        initialRelationship.id,
    });

  const [isSubmitting, setIsSubmitting] =
    useState(false);
  const [errorMessage, setErrorMessage] =
    useState("");

  function updateRelationshipType(
    relationshipType: RelationshipType,
  ) {
    setValues((currentValues) => ({
      ...currentValues,
      relationshipType,
      relationshipId: "",
    }));
  }

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();
    setErrorMessage("");

    const body = values.body.trim();

    if (!body) {
      setErrorMessage(
        "Note body cannot be blank.",
      );
      return;
    }

    if (!values.relationshipId) {
      setErrorMessage(
        "Please select a related record.",
      );
      return;
    }

    const relationshipId = Number(
      values.relationshipId,
    );

    setIsSubmitting(true);

    try {
      await onSubmit({
        body,
        company_id:
          values.relationshipType === "company"
            ? relationshipId
            : null,
        contact_id:
          values.relationshipType === "contact"
            ? relationshipId
            : null,
        lead_id:
          values.relationshipType === "lead"
            ? relationshipId
            : null,
      });
    } catch (error) {
      setErrorMessage(
        error instanceof ApiError
          ? error.message
          : "Unable to save the note.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form
      className="space-y-6"
      onSubmit={handleSubmit}
    >
      <div className="grid gap-6 md:grid-cols-2">
        <div>
          <label
            className="mb-2 block text-sm font-medium text-slate-200"
            htmlFor="note-related-type"
          >
            Related record type
          </label>

          <select
            className={inputClassName}
            disabled={isSubmitting}
            id="note-related-type"
            onChange={(event) =>
              updateRelationshipType(
                event.target
                  .value as RelationshipType,
              )
            }
            value={values.relationshipType}
          >
            <option value="company">Company</option>
            <option value="contact">Contact</option>
            <option value="lead">Lead</option>
          </select>
        </div>

        <div>
          <label
            className="mb-2 block text-sm font-medium text-slate-200"
            htmlFor="note-related-record"
          >
            Related record
          </label>

          <select
            className={inputClassName}
            disabled={isSubmitting}
            id="note-related-record"
            onChange={(event) =>
              setValues((currentValues) => ({
                ...currentValues,
                relationshipId:
                  event.target.value,
              }))
            }
            required
            value={values.relationshipId}
          >
            <option value="">
              Select a record
            </option>

            {values.relationshipType ===
              "company" &&
              companies.map((company) => (
                <option
                  key={company.id}
                  value={company.id}
                >
                  {company.name}
                </option>
              ))}

            {values.relationshipType ===
              "contact" &&
              contacts.map((contact) => (
                <option
                  key={contact.id}
                  value={contact.id}
                >
                  {[
                    contact.first_name,
                    contact.last_name,
                  ]
                    .filter(Boolean)
                    .join(" ")}
                </option>
              ))}

            {values.relationshipType === "lead" &&
              leads.map((lead) => (
                <option
                  key={lead.id}
                  value={lead.id}
                >
                  {lead.title}
                </option>
              ))}
          </select>
        </div>

        <div className="md:col-span-2">
          <label
            className="mb-2 block text-sm font-medium text-slate-200"
            htmlFor="note-body"
          >
            Note
          </label>

          <textarea
            autoFocus
            className={inputClassName}
            disabled={isSubmitting}
            id="note-body"
            onChange={(event) =>
              setValues((currentValues) => ({
                ...currentValues,
                body: event.target.value,
              }))
            }
            placeholder="Write your note here..."
            required
            rows={10}
            value={values.body}
          />
        </div>
      </div>

      {errorMessage && (
        <div
          className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300"
          role="alert"
        >
          {errorMessage}
        </div>
      )}

      <div className="flex flex-col-reverse gap-3 border-t border-slate-800 pt-6 sm:flex-row sm:justify-end">
        <Link
          className="rounded-lg border border-slate-700 px-5 py-3 text-center text-sm font-semibold text-slate-200 transition hover:bg-slate-800"
          href={cancelHref}
        >
          Cancel
        </Link>

        <button
          className="rounded-lg bg-blue-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:bg-slate-700"
          disabled={isSubmitting}
          type="submit"
        >
          {isSubmitting
            ? "Saving..."
            : submitLabel}
        </button>
      </div>
    </form>
  );
}