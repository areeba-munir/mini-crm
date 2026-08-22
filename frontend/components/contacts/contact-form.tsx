"use client";

import Link from "next/link";
import type { FormEvent } from "react";
import { useState } from "react";

import { ApiError } from "@/lib/api";
import type { Company } from "@/types/company";
import type { ContactCreateInput } from "@/types/contact";

type ContactFormValues = {
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  jobTitle: string;
  companyId: string;
};

type ContactFormProps = {
  companies: Company[];
  initialValues?: Partial<ContactCreateInput>;
  submitLabel: string;
  cancelHref: string;
  onSubmit: (
    input: ContactCreateInput,
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

export function ContactForm({
  companies,
  initialValues,
  submitLabel,
  cancelHref,
  onSubmit,
}: ContactFormProps) {
  const [values, setValues] =
    useState<ContactFormValues>({
      firstName: initialValues?.first_name ?? "",
      lastName: initialValues?.last_name ?? "",
      email: initialValues?.email ?? "",
      phone: initialValues?.phone ?? "",
      jobTitle: initialValues?.job_title ?? "",
      companyId:
        initialValues?.company_id == null
          ? ""
          : String(initialValues.company_id),
    });

  const [isSubmitting, setIsSubmitting] =
    useState(false);
  const [errorMessage, setErrorMessage] =
    useState("");

  function updateValue(
    field: keyof ContactFormValues,
    value: string,
  ) {
    setValues((currentValues) => ({
      ...currentValues,
      [field]: value,
    }));
  }

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();
    setErrorMessage("");

    const firstName = values.firstName.trim();

    if (!firstName) {
      setErrorMessage(
        "First name cannot be blank.",
      );
      return;
    }

    setIsSubmitting(true);

    try {
      await onSubmit({
        first_name: firstName,
        last_name: optionalValue(values.lastName),
        email: optionalValue(
          values.email.toLowerCase(),
        ),
        phone: optionalValue(values.phone),
        job_title: optionalValue(values.jobTitle),
        company_id: values.companyId
          ? Number(values.companyId)
          : null,
      });
    } catch (error) {
      setErrorMessage(
        error instanceof ApiError
          ? error.message
          : "Unable to save the contact.",
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
            htmlFor="contact-first-name"
          >
            First name
          </label>

          <input
            autoFocus
            className={inputClassName}
            disabled={isSubmitting}
            id="contact-first-name"
            maxLength={100}
            onChange={(event) =>
              updateValue(
                "firstName",
                event.target.value,
              )
            }
            placeholder="Areeb"
            required
            type="text"
            value={values.firstName}
          />
        </div>

        <div>
          <label
            className="mb-2 block text-sm font-medium text-slate-200"
            htmlFor="contact-last-name"
          >
            Last name
          </label>

          <input
            className={inputClassName}
            disabled={isSubmitting}
            id="contact-last-name"
            maxLength={100}
            onChange={(event) =>
              updateValue(
                "lastName",
                event.target.value,
              )
            }
            placeholder="Ahmed"
            type="text"
            value={values.lastName}
          />
        </div>

        <div>
          <label
            className="mb-2 block text-sm font-medium text-slate-200"
            htmlFor="contact-email"
          >
            Email
          </label>

          <input
            autoComplete="email"
            className={inputClassName}
            disabled={isSubmitting}
            id="contact-email"
            onChange={(event) =>
              updateValue(
                "email",
                event.target.value,
              )
            }
            placeholder="areeb@example.com"
            type="email"
            value={values.email}
          />
        </div>

        <div>
          <label
            className="mb-2 block text-sm font-medium text-slate-200"
            htmlFor="contact-phone"
          >
            Phone
          </label>

          <input
            autoComplete="tel"
            className={inputClassName}
            disabled={isSubmitting}
            id="contact-phone"
            maxLength={50}
            onChange={(event) =>
              updateValue(
                "phone",
                event.target.value,
              )
            }
            placeholder="+1 555 0100"
            type="tel"
            value={values.phone}
          />
        </div>

        <div>
          <label
            className="mb-2 block text-sm font-medium text-slate-200"
            htmlFor="contact-job-title"
          >
            Job title
          </label>

          <input
            className={inputClassName}
            disabled={isSubmitting}
            id="contact-job-title"
            maxLength={150}
            onChange={(event) =>
              updateValue(
                "jobTitle",
                event.target.value,
              )
            }
            placeholder="Software Developer"
            type="text"
            value={values.jobTitle}
          />
        </div>

        <div>
          <label
            className="mb-2 block text-sm font-medium text-slate-200"
            htmlFor="contact-company"
          >
            Company
          </label>

          <select
            className={inputClassName}
            disabled={isSubmitting}
            id="contact-company"
            onChange={(event) =>
              updateValue(
                "companyId",
                event.target.value,
              )
            }
            value={values.companyId}
          >
            <option value="">
              No company
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