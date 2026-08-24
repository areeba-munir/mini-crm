"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { ContactForm } from "@/components/contacts/contact-form";
import { AppShell } from "@/components/layout/app-shell";
import { useToast } from "@/components/ui/toast-provider";
import { useAuthenticatedUser } from "@/hooks/use-authenticated-user";
import { ApiError } from "@/lib/api";
import { removeAccessToken } from "@/lib/auth-storage";
import { listCompanies } from "@/lib/companies-api";
import { createContact } from "@/lib/contacts-api";
import type { Company } from "@/types/company";
import type { ContactCreateInput } from "@/types/contact";

export default function NewContactPage() {
  const router = useRouter();
  const { showToast } = useToast();

  const {
    user,
    token,
    isLoading: isAuthenticationLoading,
    errorMessage: authenticationError,
  } = useAuthenticatedUser();

  const [companies, setCompanies] = useState<Company[]>([]);
  const [isCompaniesLoading, setIsCompaniesLoading] = useState(true);
  const [companiesError, setCompaniesError] = useState("");

  useEffect(() => {
    if (!token) {
      return;
    }

    let cancelled = false;

    async function loadCompanies(accessToken: string) {
      try {
        const companyRecords = await listCompanies(accessToken);

        if (!cancelled) {
          setCompanies(companyRecords);
          setIsCompaniesLoading(false);
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

        setCompaniesError(
          error instanceof ApiError
            ? error.message
            : "Unable to load companies.",
        );
        setIsCompaniesLoading(false);
      }
    }

    void loadCompanies(token);

    return () => {
      cancelled = true;
    };
  }, [router, token]);

  if (isAuthenticationLoading || !user || !token) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-950 px-4">
        <p
          className={`text-sm ${
            authenticationError ? "text-red-300" : "text-slate-400"
          }`}
        >
          {authenticationError || "Loading contact form..."}
        </p>
      </main>
    );
  }

  if (isCompaniesLoading) {
    return (
      <AppShell user={user}>
        <p className="text-sm text-slate-400">Loading companies...</p>
      </AppShell>
    );
  }

  if (companiesError) {
    return (
      <AppShell user={user}>
        <section className="rounded-2xl border border-red-500/30 bg-red-500/10 p-6">
          <h1 className="text-lg font-semibold text-red-300">
            Contact form unavailable
          </h1>

          <p className="mt-2 text-sm text-red-200">{companiesError}</p>
        </section>
      </AppShell>
    );
  }

  async function handleCreateContact(input: ContactCreateInput) {
    if (!token) {
      throw new Error("Authentication token is unavailable.");
    }

    await createContact(input, token);

    showToast("Contact created successfully.", "success");

    router.push("/contacts");
  }

  return (
    <AppShell user={user}>
      <section className="mx-auto max-w-3xl">
        <div>
          <p className="text-sm font-medium text-blue-400">Contacts</p>

          <h1 className="mt-1 text-3xl font-bold">Add contact</h1>

          <p className="mt-2 text-sm text-slate-400">
            Add a person and optionally connect them to an existing company.
          </p>
        </div>

        <div className="mt-8 rounded-2xl border border-slate-800 bg-slate-900 p-6 sm:p-8">
          <ContactForm
            cancelHref="/contacts"
            companies={companies}
            onSubmit={handleCreateContact}
            submitLabel="Create contact"
          />
        </div>
      </section>
    </AppShell>
  );
}
