"use client";

import Link from "next/link";
import type { FormEvent } from "react";
import { useState } from "react";

import { ApiError } from "@/lib/api";
import type { Company } from "@/types/company";
import type { Contact } from "@/types/contact";
import type {
  LeadCreateInput,
  LeadStage,
} from "@/types/lead";

const leadStages: LeadStage[] = [
  "New",
  "Contacted",
  "Qualified",
  "Won",
  "Lost",
];

type LeadFormValues = {
  title: string;
  companyId: string;
  contactId: string;
  stage: LeadStage;
  estimatedValue: string;
  source: string;
  expectedCloseDate: string;
  description: string;
};

type LeadFormProps = {
  companies: Company[];
  contacts: Contact[];
  initialValues?: Partial<LeadCreateInput>;
  submitLabel: string;
  cancelHref: string;
  onSubmit: (
    input: LeadCreateInput,
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

export function LeadForm({
  companies,
  contacts,
  initialValues,
  submitLabel,
  cancelHref,
  onSubmit,
}: LeadFormProps) {
  const [values, setValues] = useState<LeadFormValues>({
    title: initialValues?.title ?? "",
    companyId:
      initialValues?.company_id == null
        ? ""
        : String(initialValues.company_id),
    contactId:
      initialValues?.contact_id == null
        ? ""
        : String(initialValues.contact_id),
    stage: initialValues?.stage ?? "New",
    estimatedValue:
      initialValues?.estimated_value ?? "",
    source: initialValues?.source ?? "",
    expectedCloseDate:
      initialValues?.expected_close_date ?? "",
    description: initialValues?.description ?? "",
  });

  const [isSubmitting, setIsSubmitting] =
    useState(false);
  const [errorMessage, setErrorMessage] =
    useState("");

  const selectedCompanyId = values.companyId
    ? Number(values.companyId)
    : null;

  const availableContacts =
    selectedCompanyId === null
      ? []
      : contacts.filter(
          (contact) =>
            contact.company_id === selectedCompanyId,
        );

  function updateValue(
    field: keyof LeadFormValues,
    value: string,
  ) {
    setValues((currentValues) => ({
      ...currentValues,
      [field]: value,
    }));
  }

  function updateCompany(companyId: string) {
    setValues((currentValues) => {
      const selectedContact = contacts.find(
        (contact) =>
          String(contact.id) ===
          currentValues.contactId,
      );

      const shouldKeepContact =
        selectedContact &&
        String(selectedContact.company_id) ===
          companyId;

      return {
        ...currentValues,
        companyId,
        contactId: shouldKeepContact
          ? currentValues.contactId
          : "",
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
        "Lead title cannot be blank.",
      );
      return;
    }

    if (!values.companyId) {
      setErrorMessage(
        "Please select a company.",
      );
      return;
    }

    setIsSubmitting(true);

    try {
      await onSubmit({
        title,
        company_id: Number(values.companyId),
        contact_id: values.contactId
          ? Number(values.contactId)
          : null,
        stage: values.stage,
        estimated_value: optionalValue(
          values.estimatedValue,
        ),
        source: optionalValue(values.source),
        expected_close_date: optionalValue(
          values.expectedCloseDate,
        ),
        description: optionalValue(
          values.description,
        ),
      });
    } catch (error) {
      setErrorMessage(
        error instanceof ApiError
          ? error.message
          : "Unable to save the lead.",
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
            htmlFor="lead-title"
          >
            Lead title
          </label>

          <input
            autoFocus
            className={inputClassName}
            disabled={isSubmitting}
            id="lead-title"
            maxLength={200}
            onChange={(event) =>
              updateValue(
                "title",
                event.target.value,
              )
            }
            placeholder="New website project"
            required
            type="text"
            value={values.title}
          />
        </div>

        <div>
          <label
            className="mb-2 block text-sm font-medium text-slate-200"
            htmlFor="lead-company"
          >
            Company
          </label>

          <select
            className={inputClassName}
            disabled={isSubmitting}
            id="lead-company"
            onChange={(event) =>
              updateCompany(event.target.value)
            }
            required
            value={values.companyId}
          >
            <option value="">
              Select a company
            </option>

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
            htmlFor="lead-contact"
          >
            Primary contact
          </label>

          <select
            className={inputClassName}
            disabled={
              isSubmitting ||
              selectedCompanyId === null
            }
            id="lead-contact"
            onChange={(event) =>
              updateValue(
                "contactId",
                event.target.value,
              )
            }
            value={values.contactId}
          >
            <option value="">
              No primary contact
            </option>

            {availableContacts.map((contact) => (
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
          </select>
        </div>

        <div>
          <label
            className="mb-2 block text-sm font-medium text-slate-200"
            htmlFor="lead-stage"
          >
            Stage
          </label>

          <select
            className={inputClassName}
            disabled={isSubmitting}
            id="lead-stage"
            onChange={(event) =>
              updateValue(
                "stage",
                event.target.value,
              )
            }
            value={values.stage}
          >
            {leadStages.map((stage) => (
              <option key={stage} value={stage}>
                {stage}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label
            className="mb-2 block text-sm font-medium text-slate-200"
            htmlFor="lead-estimated-value"
          >
            Estimated value
          </label>

          <input
            className={inputClassName}
            disabled={isSubmitting}
            id="lead-estimated-value"
            min="0"
            onChange={(event) =>
              updateValue(
                "estimatedValue",
                event.target.value,
              )
            }
            placeholder="5000.00"
            step="0.01"
            type="number"
            value={values.estimatedValue}
          />
        </div>

        <div>
          <label
            className="mb-2 block text-sm font-medium text-slate-200"
            htmlFor="lead-source"
          >
            Source
          </label>

          <input
            className={inputClassName}
            disabled={isSubmitting}
            id="lead-source"
            maxLength={100}
            onChange={(event) =>
              updateValue(
                "source",
                event.target.value,
              )
            }
            placeholder="Website"
            type="text"
            value={values.source}
          />
        </div>

        <div>
          <label
            className="mb-2 block text-sm font-medium text-slate-200"
            htmlFor="lead-close-date"
          >
            Expected close date
          </label>

          <input
            className={inputClassName}
            disabled={isSubmitting}
            id="lead-close-date"
            onChange={(event) =>
              updateValue(
                "expectedCloseDate",
                event.target.value,
              )
            }
            type="date"
            value={values.expectedCloseDate}
          />
        </div>

        <div className="md:col-span-2">
          <label
            className="mb-2 block text-sm font-medium text-slate-200"
            htmlFor="lead-description"
          >
            Description
          </label>

          <textarea
            className={inputClassName}
            disabled={isSubmitting}
            id="lead-description"
            onChange={(event) =>
              updateValue(
                "description",
                event.target.value,
              )
            }
            placeholder="Additional information about this opportunity"
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