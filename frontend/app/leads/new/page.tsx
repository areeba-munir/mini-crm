"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/layout/app-shell";
import { LeadForm } from "@/components/leads/lead-form";
import { useAuthenticatedUser } from "@/hooks/use-authenticated-user";
import { ApiError } from "@/lib/api";
import { removeAccessToken } from "@/lib/auth-storage";
import { listCompanies } from "@/lib/companies-api";
import { listContacts } from "@/lib/contacts-api";
import { createLead } from "@/lib/leads-api";
import type { Company } from "@/types/company";
import type { Contact } from "@/types/contact";
import type { LeadCreateInput } from "@/types/lead";

export default function NewLeadPage() {
  const router = useRouter();

  const {
    user,
    token,
    isLoading: isAuthenticationLoading,
    errorMessage: authenticationError,
  } = useAuthenticatedUser();

  const [companies, setCompanies] = useState<Company[]>(
    [],
  );
  const [contacts, setContacts] = useState<Contact[]>(
    [],
  );
  const [isDataLoading, setIsDataLoading] =
    useState(true);
  const [dataError, setDataError] = useState("");

  useEffect(() => {
    if (!token) {
      return;
    }

    let cancelled = false;

    async function loadFormData(
      accessToken: string,
    ) {
      try {
        const [
          companyRecords,
          contactRecords,
        ] = await Promise.all([
          listCompanies(accessToken),
          listContacts(accessToken),
        ]);

        if (!cancelled) {
          setCompanies(companyRecords);
          setContacts(contactRecords);
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
            : "Unable to load the lead form.",
        );
        setIsDataLoading(false);
      }
    }

    void loadFormData(token);

    return () => {
      cancelled = true;
    };
  }, [router, token]);

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
            "Loading lead form..."}
        </p>
      </main>
    );
  }

  if (isDataLoading) {
    return (
      <AppShell user={user}>
        <p className="text-sm text-slate-400">
          Loading companies and contacts...
        </p>
      </AppShell>
    );
  }

  if (dataError) {
    return (
      <AppShell user={user}>
        <section className="rounded-2xl border border-red-500/30 bg-red-500/10 p-6">
          <h1 className="text-lg font-semibold text-red-300">
            Lead form unavailable
          </h1>

          <p className="mt-2 text-sm text-red-200">
            {dataError}
          </p>
        </section>
      </AppShell>
    );
  }

  async function handleCreateLead(
    input: LeadCreateInput,
  ) {
    if (!token) {
      throw new Error(
        "Authentication token is unavailable.",
      );
    }

    await createLead(input, token);
    router.push("/leads");
  }

  return (
    <AppShell user={user}>
      <section className="mx-auto max-w-3xl">
        <div>
          <p className="text-sm font-medium text-blue-400">
            Leads
          </p>

          <h1 className="mt-1 text-3xl font-bold">
            Add lead
          </h1>

          <p className="mt-2 text-sm text-slate-400">
            Create a sales opportunity and connect it
            to a company.
          </p>
        </div>

        <div className="mt-8 rounded-2xl border border-slate-800 bg-slate-900 p-6 sm:p-8">
          <LeadForm
            cancelHref="/leads"
            companies={companies}
            contacts={contacts}
            onSubmit={handleCreateLead}
            submitLabel="Create lead"
          />
        </div>
      </section>
    </AppShell>
  );
}