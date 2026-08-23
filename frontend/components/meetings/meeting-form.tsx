"use client";

import Link from "next/link";
import type { FormEvent } from "react";
import { useState } from "react";

import { ApiError } from "@/lib/api";
import type { Company } from "@/types/company";
import type { Contact } from "@/types/contact";
import type {
  MeetingCreateInput,
  MeetingStatus,
} from "@/types/meeting";

const meetingStatuses: MeetingStatus[] = [
  "Scheduled",
  "Completed",
  "Cancelled",
];

type MeetingFormValues = {
  title: string;
  description: string;
  startsAt: string;
  endsAt: string;
  location: string;
  meetingLink: string;
  notes: string;
  status: MeetingStatus;
  companyId: string;
  userParticipantIds: number[];
  contactParticipantIds: number[];
};

type MeetingFormProps = {
  companies: Company[];
  contacts: Contact[];
  currentUserId: number;
  initialValues?: Partial<MeetingCreateInput>;
  submitLabel: string;
  cancelHref: string;
  onSubmit: (
    input: MeetingCreateInput,
  ) => Promise<void>;
};

const inputClassName =
  "w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white outline-none transition placeholder:text-slate-600 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 disabled:cursor-not-allowed disabled:opacity-60";

function optionalValue(
  value: string,
): string | null {
  const trimmedValue = value.trim();
  return trimmedValue || null;
}

function toDateTimeLocal(
  value?: string | null,
): string {
  if (!value) {
    return "";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "";
  }

  const timezoneOffset =
    date.getTimezoneOffset() * 60_000;

  return new Date(
    date.getTime() - timezoneOffset,
  )
    .toISOString()
    .slice(0, 16);
}

export function MeetingForm({
  companies,
  contacts,
  currentUserId,
  initialValues,
  submitLabel,
  cancelHref,
  onSubmit,
}: MeetingFormProps) {
  const [values, setValues] =
    useState<MeetingFormValues>({
      title: initialValues?.title ?? "",
      description:
        initialValues?.description ?? "",
      startsAt: toDateTimeLocal(
        initialValues?.starts_at,
      ),
      endsAt: toDateTimeLocal(
        initialValues?.ends_at,
      ),
      location: initialValues?.location ?? "",
      meetingLink:
        initialValues?.meeting_link ?? "",
      notes: initialValues?.notes ?? "",
      status:
        initialValues?.status ?? "Scheduled",
      companyId:
        initialValues?.company_id == null
          ? ""
          : String(initialValues.company_id),
      userParticipantIds:
        initialValues?.user_participant_ids ??
        [],
      contactParticipantIds:
        initialValues?.contact_participant_ids ??
        [],
    });

  const [isSubmitting, setIsSubmitting] =
    useState(false);
  const [errorMessage, setErrorMessage] =
    useState("");

  function updateTextValue(
    field:
      | "title"
      | "description"
      | "startsAt"
      | "endsAt"
      | "location"
      | "meetingLink"
      | "notes"
      | "companyId",
    value: string,
  ) {
    setValues((currentValues) => ({
      ...currentValues,
      [field]: value,
    }));
  }

  function toggleCurrentUser() {
    setValues((currentValues) => {
      const isIncluded =
        currentValues.userParticipantIds.includes(
          currentUserId,
        );

      return {
        ...currentValues,
        userParticipantIds: isIncluded
          ? currentValues.userParticipantIds.filter(
              (userId) =>
                userId !== currentUserId,
            )
          : [
              ...currentValues.userParticipantIds,
              currentUserId,
            ],
      };
    });
  }

  function toggleContact(contactId: number) {
    setValues((currentValues) => {
      const isIncluded =
        currentValues.contactParticipantIds.includes(
          contactId,
        );

      return {
        ...currentValues,
        contactParticipantIds: isIncluded
          ? currentValues.contactParticipantIds.filter(
              (currentContactId) =>
                currentContactId !== contactId,
            )
          : [
              ...currentValues.contactParticipantIds,
              contactId,
            ],
      };
    });
  }

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();
    setErrorMessage("");

    const title = values.title.trim();

    if (!title) {
      setErrorMessage(
        "Meeting title cannot be blank.",
      );
      return;
    }

    if (!values.startsAt || !values.endsAt) {
      setErrorMessage(
        "Start and end times are required.",
      );
      return;
    }

    const startsAt = new Date(values.startsAt);
    const endsAt = new Date(values.endsAt);

    if (endsAt <= startsAt) {
      setErrorMessage(
        "Meeting end must be after start.",
      );
      return;
    }

    setIsSubmitting(true);

    try {
      await onSubmit({
        title,
        description: optionalValue(
          values.description,
        ),
        starts_at: startsAt.toISOString(),
        ends_at: endsAt.toISOString(),
        location: optionalValue(
          values.location,
        ),
        meeting_link: optionalValue(
          values.meetingLink,
        ),
        notes: optionalValue(values.notes),
        status: values.status,
        organizer_id: currentUserId,
        company_id: values.companyId
          ? Number(values.companyId)
          : null,
        user_participant_ids:
          values.userParticipantIds,
        contact_participant_ids:
          values.contactParticipantIds,
      });
    } catch (error) {
      setErrorMessage(
        error instanceof ApiError
          ? error.message
          : "Unable to save the meeting.",
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
        <div className="md:col-span-2">
          <label
            className="mb-2 block text-sm font-medium text-slate-200"
            htmlFor="meeting-title"
          >
            Meeting title
          </label>

          <input
            autoFocus
            className={inputClassName}
            disabled={isSubmitting}
            id="meeting-title"
            maxLength={200}
            onChange={(event) =>
              updateTextValue(
                "title",
                event.target.value,
              )
            }
            placeholder="Client discovery call"
            required
            type="text"
            value={values.title}
          />
        </div>

        <div>
          <label
            className="mb-2 block text-sm font-medium text-slate-200"
            htmlFor="meeting-start"
          >
            Starts at
          </label>

          <input
            className={inputClassName}
            disabled={isSubmitting}
            id="meeting-start"
            onChange={(event) =>
              updateTextValue(
                "startsAt",
                event.target.value,
              )
            }
            required
            type="datetime-local"
            value={values.startsAt}
          />
        </div>

        <div>
          <label
            className="mb-2 block text-sm font-medium text-slate-200"
            htmlFor="meeting-end"
          >
            Ends at
          </label>

          <input
            className={inputClassName}
            disabled={isSubmitting}
            id="meeting-end"
            onChange={(event) =>
              updateTextValue(
                "endsAt",
                event.target.value,
              )
            }
            required
            type="datetime-local"
            value={values.endsAt}
          />
        </div>

        <div>
          <label
            className="mb-2 block text-sm font-medium text-slate-200"
            htmlFor="meeting-status"
          >
            Status
          </label>

          <select
            className={inputClassName}
            disabled={isSubmitting}
            id="meeting-status"
            onChange={(event) =>
              setValues((currentValues) => ({
                ...currentValues,
                status:
                  event.target
                    .value as MeetingStatus,
              }))
            }
            value={values.status}
          >
            {meetingStatuses.map((status) => (
              <option key={status} value={status}>
                {status}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label
            className="mb-2 block text-sm font-medium text-slate-200"
            htmlFor="meeting-company"
          >
            Company
          </label>

          <select
            className={inputClassName}
            disabled={isSubmitting}
            id="meeting-company"
            onChange={(event) =>
              updateTextValue(
                "companyId",
                event.target.value,
              )
            }
            value={values.companyId}
          >
            <option value="">No company</option>

            {companies.map((company) => (
              <option
                key={company.id}
                value={company.id}
              >
                {company.name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label
            className="mb-2 block text-sm font-medium text-slate-200"
            htmlFor="meeting-location"
          >
            Location
          </label>

          <input
            className={inputClassName}
            disabled={isSubmitting}
            id="meeting-location"
            maxLength={500}
            onChange={(event) =>
              updateTextValue(
                "location",
                event.target.value,
              )
            }
            placeholder="Conference room"
            type="text"
            value={values.location}
          />
        </div>

        <div>
          <label
            className="mb-2 block text-sm font-medium text-slate-200"
            htmlFor="meeting-link"
          >
            Meeting link
          </label>

          <input
            className={inputClassName}
            disabled={isSubmitting}
            id="meeting-link"
            maxLength={500}
            onChange={(event) =>
              updateTextValue(
                "meetingLink",
                event.target.value,
              )
            }
            placeholder="https://meet.example.com/call"
            type="url"
            value={values.meetingLink}
          />
        </div>

        <div className="md:col-span-2">
          <label
            className="mb-2 block text-sm font-medium text-slate-200"
            htmlFor="meeting-description"
          >
            Description
          </label>

          <textarea
            className={inputClassName}
            disabled={isSubmitting}
            id="meeting-description"
            onChange={(event) =>
              updateTextValue(
                "description",
                event.target.value,
              )
            }
            placeholder="Meeting agenda and purpose"
            rows={4}
            value={values.description}
          />
        </div>

        <div className="md:col-span-2">
          <p className="mb-3 text-sm font-medium text-slate-200">
            CRM user participants
          </p>

          <label className="flex items-center gap-3 rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-slate-300">
            <input
              checked={values.userParticipantIds.includes(
                currentUserId,
              )}
              className="size-4 accent-blue-600"
              disabled={isSubmitting}
              onChange={toggleCurrentUser}
              type="checkbox"
            />

            Include me as a participant
          </label>
        </div>

        <div className="md:col-span-2">
          <p className="mb-3 text-sm font-medium text-slate-200">
            Contact participants
          </p>

          {contacts.length === 0 ? (
            <p className="rounded-lg border border-dashed border-slate-700 px-4 py-4 text-sm text-slate-400">
              No contacts are available.
            </p>
          ) : (
            <div className="grid gap-3 sm:grid-cols-2">
              {contacts.map((contact) => (
                <label
                  className="flex items-center gap-3 rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-slate-300"
                  key={contact.id}
                >
                  <input
                    checked={values.contactParticipantIds.includes(
                      contact.id,
                    )}
                    className="size-4 accent-blue-600"
                    disabled={isSubmitting}
                    onChange={() =>
                      toggleContact(contact.id)
                    }
                    type="checkbox"
                  />

                  {[
                    contact.first_name,
                    contact.last_name,
                  ]
                    .filter(Boolean)
                    .join(" ")}
                </label>
              ))}
            </div>
          )}
        </div>

        <div className="md:col-span-2">
          <label
            className="mb-2 block text-sm font-medium text-slate-200"
            htmlFor="meeting-notes"
          >
            Notes
          </label>

          <textarea
            className={inputClassName}
            disabled={isSubmitting}
            id="meeting-notes"
            onChange={(event) =>
              updateTextValue(
                "notes",
                event.target.value,
              )
            }
            placeholder="Private meeting notes"
            rows={4}
            value={values.notes}
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