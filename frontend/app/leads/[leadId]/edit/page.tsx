"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/layout/app-shell";
import { LeadForm } from "@/components/leads/lead-form";
import { useAuthenticatedUser } from "@/hooks/use-authenticated-user";
import { ApiError } from "@/lib/api";
import { removeAccessToken } from "@/lib/auth-storage";
import { listCompanies } from "@/lib/companies-api";
import { listContacts } from "@/lib/contacts-api";
import {
  getLead,
  updateLead,
} from "@/lib/leads-api";
import type { Company } from "@/types/company";
import type { Contact } from "@/types/contact";
import type {
  Lead,
  LeadCreateInput,
} from "@/types/lead";

export default function EditLeadPage() {
  const params = useParams<{
    leadId: string;
  }>();
  const router = useRouter();

  const leadId = Number(params.leadId);

  const isLeadIdValid =
    Number.isInteger(leadId) && leadId >= 1;

  const {
    user,
    token,
    isLoading: isAuthenticationLoading,
    errorMessage: authenticationError,
  } = useAuthenticatedUser();

  const [lead, setLead] =
    useState<Lead | null>(null);
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
    if (!token || !isLeadIdValid) {
      return;
    }

    let cancelled = false;

    async function loadLeadData(
      accessToken: string,
    ) {
      try {
        const [
          leadRecord,
          companyRecords,
          contactRecords,
        ] = await Promise.all([
          getLead(leadId, accessToken),
          listCompanies(accessToken),
          listContacts(accessToken),
        ]);

        if (!cancelled) {
          setLead(leadRecord);
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
            : "Unable to load the lead.",
        );
        setIsDataLoading(false);
      }
    }

    void loadLeadData(token);

    return () => {
      cancelled = true;
    };
  }, [
    isLeadIdValid,
    leadId,
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
            "Loading lead editor..."}
        </p>
      </main>
    );
  }

  if (!isLeadIdValid) {
    return (
      <AppShell user={user}>
        <section className="rounded-2xl border border-red-500/30 bg-red-500/10 p-6">
          <h1 className="text-lg font-semibold text-red-300">
            Invalid lead
          </h1>

          <p className="mt-2 text-sm text-red-200">
            The lead ID must be a positive number.
          </p>
        </section>
      </AppShell>
    );
  }

  if (isDataLoading) {
    return (
      <AppShell user={user}>
        <p className="text-sm text-slate-400">
          Loading lead...
        </p>
      </AppShell>
    );
  }

  if (dataError || !lead) {
    return (
      <AppShell user={user}>
        <section className="rounded-2xl border border-red-500/30 bg-red-500/10 p-6">
          <h1 className="text-lg font-semibold text-red-300">
            Lead unavailable
          </h1>

          <p className="mt-2 text-sm text-red-200">
            {dataError ||
              "The lead could not be found."}
          </p>
        </section>
      </AppShell>
    );
  }

  async function handleUpdateLead(
    input: LeadCreateInput,
  ) {
    if (!token || !lead) {
      throw new Error(
        "Lead or authentication data is unavailable.",
      );
    }

    await updateLead(
      lead.id,
      input,
      token,
    );

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
            Edit lead
          </h1>

          <p className="mt-2 text-sm text-slate-400">
            Update the sales opportunity{" "}
            <span className="font-medium text-slate-200">
              {lead.title}
            </span>
            .
          </p>
        </div>

        <div className="mt-8 rounded-2xl border border-slate-800 bg-slate-900 p-6 sm:p-8">
          <LeadForm
            cancelHref="/leads"
            companies={companies}
            contacts={contacts}
            initialValues={{
              title: lead.title,
              company_id: lead.company_id,
              contact_id: lead.contact_id,
              stage: lead.stage,
              estimated_value:
                lead.estimated_value,
              source: lead.source,
              expected_close_date:
                lead.expected_close_date,
              description: lead.description,
            }}
            onSubmit={handleUpdateLead}
            submitLabel="Save changes"
          />
        </div>
      </section>
    </AppShell>
  );
}