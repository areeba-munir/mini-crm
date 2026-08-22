"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { ContactForm } from "@/components/contacts/contact-form";
import { AppShell } from "@/components/layout/app-shell";
import { useAuthenticatedUser } from "@/hooks/use-authenticated-user";
import { ApiError } from "@/lib/api";
import { removeAccessToken } from "@/lib/auth-storage";
import { listCompanies } from "@/lib/companies-api";
import {
  getContact,
  updateContact,
} from "@/lib/contacts-api";
import type { Company } from "@/types/company";
import type {
  Contact,
  ContactCreateInput,
} from "@/types/contact";

export default function EditContactPage() {
  const params = useParams<{
    contactId: string;
  }>();
  const router = useRouter();

  const contactId = Number(params.contactId);

  const isContactIdValid =
    Number.isInteger(contactId) && contactId >= 1;

  const {
    user,
    token,
    isLoading: isAuthenticationLoading,
    errorMessage: authenticationError,
  } = useAuthenticatedUser();

  const [contact, setContact] =
    useState<Contact | null>(null);
  const [companies, setCompanies] = useState<Company[]>(
    [],
  );
  const [isDataLoading, setIsDataLoading] =
    useState(true);
  const [dataError, setDataError] = useState("");

  useEffect(() => {
    if (!token || !isContactIdValid) {
      return;
    }

    let cancelled = false;

    async function loadContactData(
      accessToken: string,
    ) {
      try {
        const [
          contactRecord,
          companyRecords,
        ] = await Promise.all([
          getContact(contactId, accessToken),
          listCompanies(accessToken),
        ]);

        if (!cancelled) {
          setContact(contactRecord);
          setCompanies(companyRecords);
          setIsDataLoading(false);
        }
      } catch (error) {
        if (cancelled) {
          return;
        }

        if (
          error instanceof ApiError &&
          error.status === 401
        ) {
          removeAccessToken();
          router.replace("/login");
          return;
        }

        setDataError(
          error instanceof ApiError
            ? error.message
            : "Unable to load the contact.",
        );
        setIsDataLoading(false);
      }
    }

    void loadContactData(token);

    return () => {
      cancelled = true;
    };
  }, [
    contactId,
    isContactIdValid,
    router,
    token,
  ]);

  if (
    isAuthenticationLoading ||
    !user ||
    !token
  ) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-950 px-4">
        <p
          className={`text-sm ${
            authenticationError
              ? "text-red-300"
              : "text-slate-400"
          }`}
        >
          {authenticationError ||
            "Loading contact editor..."}
        </p>
      </main>
    );
  }

  if (!isContactIdValid) {
    return (
      <AppShell user={user}>
        <section className="rounded-2xl border border-red-500/30 bg-red-500/10 p-6">
          <h1 className="text-lg font-semibold text-red-300">
            Invalid contact
          </h1>

          <p className="mt-2 text-sm text-red-200">
            The contact ID must be a positive number.
          </p>
        </section>
      </AppShell>
    );
  }

  if (isDataLoading) {
    return (
      <AppShell user={user}>
        <p className="text-sm text-slate-400">
          Loading contact...
        </p>
      </AppShell>
    );
  }

  if (dataError || !contact) {
    return (
      <AppShell user={user}>
        <section className="rounded-2xl border border-red-500/30 bg-red-500/10 p-6">
          <h1 className="text-lg font-semibold text-red-300">
            Contact unavailable
          </h1>

          <p className="mt-2 text-sm text-red-200">
            {dataError ||
              "The contact could not be found."}
          </p>
        </section>
      </AppShell>
    );
  }

  async function handleUpdateContact(
    input: ContactCreateInput,
  ) {
    if (!token || !contact) {
      throw new Error(
        "Contact or authentication data is unavailable.",
      );
    }

    await updateContact(
      contact.id,
      input,
      token,
    );

    router.push("/contacts");
  }

  const contactName = [
    contact.first_name,
    contact.last_name,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <AppShell user={user}>
      <section className="mx-auto max-w-3xl">
        <div>
          <p className="text-sm font-medium text-blue-400">
            Contacts
          </p>

          <h1 className="mt-1 text-3xl font-bold">
            Edit contact
          </h1>

          <p className="mt-2 text-sm text-slate-400">
            Update the information stored for{" "}
            <span className="font-medium text-slate-200">
              {contactName}
            </span>
            .
          </p>
        </div>

        <div className="mt-8 rounded-2xl border border-slate-800 bg-slate-900 p-6 sm:p-8">
          <ContactForm
            cancelHref="/contacts"
            companies={companies}
            initialValues={{
              first_name: contact.first_name,
              last_name: contact.last_name,
              email: contact.email,
              phone: contact.phone,
              job_title: contact.job_title,
              company_id: contact.company_id,
            }}
            onSubmit={handleUpdateContact}
            submitLabel="Save changes"
          />
        </div>
      </section>
    </AppShell>
  );
}