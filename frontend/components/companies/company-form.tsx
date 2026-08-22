"use client";

import Link from "next/link";
import type { FormEvent } from "react";
import { useState } from "react";

import { ApiError } from "@/lib/api";
import type { CompanyCreateInput } from "@/types/company";

type CompanyFormValues = {
  name: string;
  industry: string;
  website: string;
  email: string;
  phone: string;
  address: string;
};

type CompanyFormProps = {
  initialValues?: Partial<CompanyFormValues>;
  submitLabel: string;
  cancelHref: string;
  onSubmit: (
    input: CompanyCreateInput,
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

export function CompanyForm({
  initialValues,
  submitLabel,
  cancelHref,
  onSubmit,
}: CompanyFormProps) {
  const [values, setValues] =
    useState<CompanyFormValues>({
      name: initialValues?.name ?? "",
      industry: initialValues?.industry ?? "",
      website: initialValues?.website ?? "",
      email: initialValues?.email ?? "",
      phone: initialValues?.phone ?? "",
      address: initialValues?.address ?? "",
    });

  const [isSubmitting, setIsSubmitting] =
    useState(false);
  const [errorMessage, setErrorMessage] =
    useState("");

  function updateValue(
    field: keyof CompanyFormValues,
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

    const companyName = values.name.trim();

    if (!companyName) {
      setErrorMessage(
        "Company name cannot be blank.",
      );
      return;
    }

    setIsSubmitting(true);

    try {
      await onSubmit({
        name: companyName,
        industry: optionalValue(values.industry),
        website: optionalValue(values.website),
        email: optionalValue(values.email),
        phone: optionalValue(values.phone),
        address: optionalValue(values.address),
      });
    } catch (error) {
      setErrorMessage(
        error instanceof ApiError
          ? error.message
          : "Unable to save the company.",
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
      <div>
        <label
          className="mb-2 block text-sm font-medium text-slate-200"
          htmlFor="company-name"
        >
          Company name
        </label>

        <input
          autoFocus
          className={inputClassName}
          disabled={isSubmitting}
          id="company-name"
          maxLength={200}
          onChange={(event) =>
            updateValue("name", event.target.value)
          }
          placeholder="Northstar Labs"
          required
          type="text"
          value={values.name}
        />
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <div>
          <label
            className="mb-2 block text-sm font-medium text-slate-200"
            htmlFor="company-industry"
          >
            Industry
          </label>

          <input
            className={inputClassName}
            disabled={isSubmitting}
            id="company-industry"
            maxLength={100}
            onChange={(event) =>
              updateValue(
                "industry",
                event.target.value,
              )
            }
            placeholder="Software"
            type="text"
            value={values.industry}
          />
        </div>

        <div>
          <label
            className="mb-2 block text-sm font-medium text-slate-200"
            htmlFor="company-website"
          >
            Website
          </label>

          <input
            className={inputClassName}
            disabled={isSubmitting}
            id="company-website"
            maxLength={500}
            onChange={(event) =>
              updateValue(
                "website",
                event.target.value,
              )
            }
            placeholder="https://example.com"
            type="url"
            value={values.website}
          />
        </div>

        <div>
          <label
            className="mb-2 block text-sm font-medium text-slate-200"
            htmlFor="company-email"
          >
            Email
          </label>

          <input
            autoComplete="email"
            className={inputClassName}
            disabled={isSubmitting}
            id="company-email"
            maxLength={255}
            onChange={(event) =>
              updateValue("email", event.target.value)
            }
            placeholder="hello@example.com"
            type="email"
            value={values.email}
          />
        </div>

        <div>
          <label
            className="mb-2 block text-sm font-medium text-slate-200"
            htmlFor="company-phone"
          >
            Phone
          </label>

          <input
            autoComplete="tel"
            className={inputClassName}
            disabled={isSubmitting}
            id="company-phone"
            maxLength={50}
            onChange={(event) =>
              updateValue("phone", event.target.value)
            }
            placeholder="+1 555 0100"
            type="tel"
            value={values.phone}
          />
        </div>
      </div>

      <div>
        <label
          className="mb-2 block text-sm font-medium text-slate-200"
          htmlFor="company-address"
        >
          Address
        </label>

        <textarea
          className={inputClassName}
          disabled={isSubmitting}
          id="company-address"
          onChange={(event) =>
            updateValue("address", event.target.value)
          }
          placeholder="100 Market Street"
          rows={4}
          value={values.address}
        />
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