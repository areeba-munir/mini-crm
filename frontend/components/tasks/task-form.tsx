"use client";

import Link from "next/link";
import type { FormEvent } from "react";
import { useState } from "react";

import { ApiError } from "@/lib/api";
import type { Company } from "@/types/company";
import type { Contact } from "@/types/contact";
import type { Lead } from "@/types/lead";
import type {
  TaskCreateInput,
  TaskPriority,
  TaskStatus,
} from "@/types/task";

const taskStatuses: TaskStatus[] = [
  "Pending",
  "In Progress",
  "Completed",
];

const taskPriorities: TaskPriority[] = [
  "Low",
  "Medium",
  "High",
];

type RelationshipType =
  | ""
  | "company"
  | "contact"
  | "lead";

type TaskFormValues = {
  title: string;
  description: string;
  status: TaskStatus;
  priority: TaskPriority;
  dueAt: string;
  relationshipType: RelationshipType;
  relationshipId: string;
};

type TaskFormProps = {
  companies: Company[];
  contacts: Contact[];
  leads: Lead[];
  currentUserId: number;
  initialValues?: Partial<TaskCreateInput>;
  submitLabel: string;
  cancelHref: string;
  onSubmit: (
    input: TaskCreateInput,
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

function getInitialRelationship(
  initialValues?: Partial<TaskCreateInput>,
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
    type: "",
    id: "",
  };
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

export function TaskForm({
  companies,
  contacts,
  leads,
  currentUserId,
  initialValues,
  submitLabel,
  cancelHref,
  onSubmit,
}: TaskFormProps) {
  const initialRelationship =
    getInitialRelationship(initialValues);

  const assignedUserId =
    initialValues?.assigned_to_id ??
    currentUserId;

  const [values, setValues] =
    useState<TaskFormValues>({
      title: initialValues?.title ?? "",
      description:
        initialValues?.description ?? "",
      status:
        initialValues?.status ?? "Pending",
      priority:
        initialValues?.priority ?? "Medium",
      dueAt: toDateTimeLocal(
        initialValues?.due_at,
      ),
      relationshipType:
        initialRelationship.type,
      relationshipId:
        initialRelationship.id,
    });

  const [isSubmitting, setIsSubmitting] =
    useState(false);
  const [errorMessage, setErrorMessage] =
    useState("");

  function updateValue<
    Key extends keyof TaskFormValues,
  >(
    field: Key,
    value: TaskFormValues[Key],
  ) {
    setValues((currentValues) => ({
      ...currentValues,
      [field]: value,
    }));
  }

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

    const title = values.title.trim();

    if (!title) {
      setErrorMessage(
        "Task title cannot be blank.",
      );
      return;
    }

    if (
      values.relationshipType &&
      !values.relationshipId
    ) {
      setErrorMessage(
        "Please select a related record.",
      );
      return;
    }

    const relationshipId = values.relationshipId
      ? Number(values.relationshipId)
      : null;

    setIsSubmitting(true);

    try {
      await onSubmit({
        title,
        description: optionalValue(
          values.description,
        ),
        status: values.status,
        priority: values.priority,
        due_at: values.dueAt
          ? new Date(values.dueAt).toISOString()
          : null,
        assigned_to_id: assignedUserId,
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
          : "Unable to save the task.",
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
            htmlFor="task-title"
          >
            Task title
          </label>

          <input
            autoFocus
            className={inputClassName}
            disabled={isSubmitting}
            id="task-title"
            maxLength={200}
            onChange={(event) =>
              updateValue(
                "title",
                event.target.value,
              )
            }
            placeholder="Follow up with the client"
            required
            type="text"
            value={values.title}
          />
        </div>

        <div>
          <label
            className="mb-2 block text-sm font-medium text-slate-200"
            htmlFor="task-status"
          >
            Status
          </label>

          <select
            className={inputClassName}
            disabled={isSubmitting}
            id="task-status"
            onChange={(event) =>
              updateValue(
                "status",
                event.target.value as TaskStatus,
              )
            }
            value={values.status}
          >
            {taskStatuses.map((status) => (
              <option key={status} value={status}>
                {status}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label
            className="mb-2 block text-sm font-medium text-slate-200"
            htmlFor="task-priority"
          >
            Priority
          </label>

          <select
            className={inputClassName}
            disabled={isSubmitting}
            id="task-priority"
            onChange={(event) =>
              updateValue(
                "priority",
                event.target.value as TaskPriority,
              )
            }
            value={values.priority}
          >
            {taskPriorities.map((priority) => (
              <option
                key={priority}
                value={priority}
              >
                {priority}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label
            className="mb-2 block text-sm font-medium text-slate-200"
            htmlFor="task-due-at"
          >
            Due date and time
          </label>

          <input
            className={inputClassName}
            disabled={isSubmitting}
            id="task-due-at"
            onChange={(event) =>
              updateValue(
                "dueAt",
                event.target.value,
              )
            }
            type="datetime-local"
            value={values.dueAt}
          />
        </div>

        <div>
          <p className="mb-2 text-sm font-medium text-slate-200">
            Assigned to
          </p>

          <div className="rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-slate-300">
            {assignedUserId === currentUserId
              ? "You"
              : `User #${assignedUserId}`}
          </div>
        </div>

        <div>
          <label
            className="mb-2 block text-sm font-medium text-slate-200"
            htmlFor="task-related-type"
          >
            Related record type
          </label>

          <select
            className={inputClassName}
            disabled={isSubmitting}
            id="task-related-type"
            onChange={(event) =>
              updateRelationshipType(
                event.target
                  .value as RelationshipType,
              )
            }
            value={values.relationshipType}
          >
            <option value="">General task</option>
            <option value="company">Company</option>
            <option value="contact">Contact</option>
            <option value="lead">Lead</option>
          </select>
        </div>

        <div>
          <label
            className="mb-2 block text-sm font-medium text-slate-200"
            htmlFor="task-related-record"
          >
            Related record
          </label>

          <select
            className={inputClassName}
            disabled={
              isSubmitting ||
              !values.relationshipType
            }
            id="task-related-record"
            onChange={(event) =>
              updateValue(
                "relationshipId",
                event.target.value,
              )
            }
            value={values.relationshipId}
          >
            <option value="">
              {values.relationshipType
                ? "Select a record"
                : "No related record"}
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
            htmlFor="task-description"
          >
            Description
          </label>

          <textarea
            className={inputClassName}
            disabled={isSubmitting}
            id="task-description"
            onChange={(event) =>
              updateValue(
                "description",
                event.target.value,
              )
            }
            placeholder="Additional instructions"
            rows={5}
            value={values.description}
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