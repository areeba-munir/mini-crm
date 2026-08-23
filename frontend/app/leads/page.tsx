"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/layout/app-shell";
import { DeleteLeadDialog } from "@/components/leads/delete-lead-dialog";
import { useAuthenticatedUser } from "@/hooks/use-authenticated-user";
import { ApiError } from "@/lib/api";
import { removeAccessToken } from "@/lib/auth-storage";
import { listCompanies } from "@/lib/companies-api";
import { listContacts } from "@/lib/contacts-api";
import { deleteLead, listLeads } from "@/lib/leads-api";
import type { Company } from "@/types/company";
import type { Contact } from "@/types/contact";
import type { Lead, LeadStage } from "@/types/lead";

const leadStages: LeadStage[] = [
  "New",
  "Contacted",
  "Qualified",
  "Won",
  "Lost",
];

const emptyValue = "\u2014";

function getStageClassName(stage: LeadStage) {
  switch (stage) {
    case "Won":
      return "bg-emerald-500/10 text-emerald-300";
    case "Lost":
      return "bg-red-500/10 text-red-300";
    case "Qualified":
      return "bg-purple-500/10 text-purple-300";
    case "Contacted":
      return "bg-amber-500/10 text-amber-300";
    default:
      return "bg-blue-500/10 text-blue-300";
  }
}

function formatEstimatedValue(estimatedValue: string | null) {
  if (estimatedValue === null) {
    return emptyValue;
  }

  return Number(estimatedValue).toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function formatExpectedCloseDate(expectedCloseDate: string | null) {
  if (!expectedCloseDate) {
    return emptyValue;
  }

  return new Date(`${expectedCloseDate}T00:00:00`).toLocaleDateString();
}

export default function LeadsPage() {
  const router = useRouter();

  const {
    user,
    token,
    isLoading: isAuthenticationLoading,
    errorMessage: authenticationError,
  } = useAuthenticatedUser();

  const [leads, setLeads] = useState<Lead[]>([]);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [selectedStage, setSelectedStage] = useState<LeadStage | "">("");
  const [isDataLoading, setIsDataLoading] = useState(true);
  const [dataError, setDataError] = useState("");

  const [leadToDelete, setLeadToDelete] = useState<Lead | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState("");

  useEffect(() => {
    if (!token) {
      return;
    }

    let cancelled = false;

    async function loadLeadData(accessToken: string) {
      try {
        const [leadRecords, companyRecords, contactRecords] = await Promise.all(
          [
            listLeads(
              accessToken,
              selectedStage ? { stage: selectedStage } : {},
            ),
            listCompanies(accessToken),
            listContacts(accessToken),
          ],
        );

        if (!cancelled) {
          setLeads(leadRecords);
          setCompanies(companyRecords);
          setContacts(contactRecords);
          setIsDataLoading(false);
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

        setDataError(
          error instanceof ApiError ? error.message : "Unable to load leads.",
        );
        setIsDataLoading(false);
      }
    }

    void loadLeadData(token);

    return () => {
      cancelled = true;
    };
  }, [router, selectedStage, token]);

  const companyNamesById = new Map(
    companies.map((company) => [company.id, company.name]),
  );

  const contactNamesById = new Map(
    contacts.map((contact) => [
      contact.id,
      [contact.first_name, contact.last_name].filter(Boolean).join(" "),
    ]),
  );

  function getCompanyName(lead: Lead) {
    return companyNamesById.get(lead.company_id) ?? "Unknown company";
  }

  function getContactName(lead: Lead) {
    if (lead.contact_id === null) {
      return emptyValue;
    }

    return contactNamesById.get(lead.contact_id) ?? "Unknown contact";
  }

  function openDeleteDialog(lead: Lead) {
    setDeleteError("");
    setLeadToDelete(lead);
  }

  function closeDeleteDialog() {
    if (isDeleting) {
      return;
    }

    setDeleteError("");
    setLeadToDelete(null);
  }

  async function handleDeleteLead() {
    if (!token || !leadToDelete) {
      return;
    }

    setIsDeleting(true);
    setDeleteError("");

    try {
      await deleteLead(leadToDelete.id, token);

      setLeads((currentLeads) =>
        currentLeads.filter((lead) => lead.id !== leadToDelete.id),
      );

      setLeadToDelete(null);
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        removeAccessToken();
        router.replace("/login");
        return;
      }

      setDeleteError(
        error instanceof ApiError
          ? error.message
          : "Unable to delete the lead.",
      );
    } finally {
      setIsDeleting(false);
    }
  }

  if (isAuthenticationLoading || !user || !token) {
    if (authenticationError) {
      return (
        <main className="flex min-h-screen items-center justify-center bg-slate-950 px-4">
          <p className="text-sm text-red-300">{authenticationError}</p>
        </main>
      );
    }

    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-950">
        <p className="text-sm text-slate-400">Loading leads...</p>
      </main>
    );
  }

  return (
    <AppShell user={user}>
      <section className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-sm font-medium text-blue-400">Sales</p>

          <h1 className="mt-1 text-3xl font-bold">Leads</h1>

          <p className="mt-2 text-sm text-slate-400">
            Track sales opportunities through your CRM pipeline.
          </p>
        </div>

        <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
          <label className="text-sm text-slate-300">
            <span className="mb-2 block">Pipeline stage</span>

            <select
              className="min-w-44 rounded-lg border border-slate-700 bg-slate-900 px-4 py-3 text-sm text-white outline-none focus:border-blue-500"
              onChange={(event) => {
                setDataError("");
                setIsDataLoading(true);
                setSelectedStage(event.target.value as LeadStage | "");
              }}
              value={selectedStage}
            >
              <option value="">All stages</option>

              {leadStages.map((stage) => (
                <option key={stage} value={stage}>
                  {stage}
                </option>
              ))}
            </select>
          </label>

          <Link
            className="rounded-lg bg-blue-600 px-5 py-3 text-center text-sm font-semibold text-white transition hover:bg-blue-500"
            href="/leads/new"
          >
            Add lead
          </Link>
        </div>
      </section>

      <p className="mt-5 text-sm text-slate-400">
        Total leads:{" "}
        <span className="font-semibold text-white">{leads.length}</span>
      </p>

      {isDataLoading && (
        <section className="mt-8 rounded-2xl border border-slate-800 bg-slate-900 p-8 text-center">
          <p className="text-sm text-slate-400">Loading lead records...</p>
        </section>
      )}

      {!isDataLoading && dataError && (
        <section className="mt-8 rounded-2xl border border-red-500/30 bg-red-500/10 p-6">
          <h2 className="font-semibold text-red-300">Leads unavailable</h2>

          <p className="mt-2 text-sm text-red-200">{dataError}</p>
        </section>
      )}

      {!isDataLoading && !dataError && leads.length === 0 && (
        <section className="mt-8 rounded-2xl border border-dashed border-slate-700 bg-slate-900 p-10 text-center">
          <h2 className="text-lg font-semibold">No leads found</h2>

          <p className="mt-2 text-sm text-slate-400">
            Create a lead or select a different pipeline stage.
          </p>

          <Link
            className="mt-5 inline-flex rounded-lg bg-blue-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-blue-500"
            href="/leads/new"
          >
            Add your first lead
          </Link>
        </section>
      )}

      {!isDataLoading && !dataError && leads.length > 0 && (
        <section className="mt-8">
          <div className="grid gap-4 md:hidden">
            {leads.map((lead) => (
              <article
                className="rounded-2xl border border-slate-800 bg-slate-900 p-5"
                key={lead.id}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0">
                    <h2 className="truncate font-semibold text-white">
                      {lead.title}
                    </h2>

                    <p className="mt-1 text-xs text-slate-500">
                      Lead #{lead.id}
                    </p>
                  </div>

                  <span
                    className={`shrink-0 rounded-full px-3 py-1 text-xs font-medium ${getStageClassName(
                      lead.stage,
                    )}`}
                  >
                    {lead.stage}
                  </span>
                </div>

                <dl className="mt-5 grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <dt className="text-xs text-slate-500">Company</dt>

                    <dd className="mt-1 text-slate-300">
                      {getCompanyName(lead)}
                    </dd>
                  </div>

                  <div>
                    <dt className="text-xs text-slate-500">Contact</dt>

                    <dd className="mt-1 text-slate-300">
                      {getContactName(lead)}
                    </dd>
                  </div>

                  <div>
                    <dt className="text-xs text-slate-500">Estimated value</dt>

                    <dd className="mt-1 text-slate-300">
                      {formatEstimatedValue(lead.estimated_value)}
                    </dd>
                  </div>

                  <div>
                    <dt className="text-xs text-slate-500">Expected close</dt>

                    <dd className="mt-1 text-slate-300">
                      {formatExpectedCloseDate(lead.expected_close_date)}
                    </dd>
                  </div>
                </dl>

                <div className="mt-5 flex justify-end gap-4 border-t border-slate-800 pt-4">
                  <Link
                    className="text-sm font-semibold text-blue-400 transition hover:text-blue-300"
                    href={`/leads/${lead.id}/edit`}
                  >
                    Edit
                  </Link>

                  <button
                    className="text-sm font-semibold text-red-400 transition hover:text-red-300"
                    onClick={() => openDeleteDialog(lead)}
                    type="button"
                  >
                    Delete
                  </button>
                </div>
              </article>
            ))}
          </div>

          <div className="hidden overflow-hidden rounded-2xl border border-slate-800 bg-slate-900 md:block">
            <table className="w-full table-fixed text-left">
              <thead className="border-b border-slate-800">
                <tr className="text-xs uppercase tracking-wider text-slate-500">
                  <th className="w-[23%] px-4 py-4 font-medium">Lead</th>

                  <th className="w-[14%] px-4 py-4 font-medium">Stage</th>

                  <th className="w-[21%] px-4 py-4 font-medium">Company</th>

                  <th className="hidden px-4 py-4 font-medium 2xl:table-cell">
                    Contact
                  </th>

                  <th className="w-[17%] px-4 py-4 font-medium">Value</th>

                  <th className="hidden w-[15%] px-4 py-4 font-medium xl:table-cell">
                    Expected close
                  </th>

                  <th className="w-[25%] px-4 py-4 text-right font-medium xl:w-[14%]">
                    Actions
                  </th>
                </tr>
              </thead>

              <tbody className="divide-y divide-slate-800">
                {leads.map((lead) => (
                  <tr
                    className="transition hover:bg-slate-800/50"
                    key={lead.id}
                  >
                    <td className="px-4 py-4">
                      <p className="truncate font-medium text-white">
                        {lead.title}
                      </p>

                      <p className="mt-1 text-xs text-slate-500">
                        Lead #{lead.id}
                      </p>
                    </td>

                    <td className="px-4 py-4">
                      <span
                        className={`inline-flex rounded-full px-3 py-1 text-xs font-medium ${getStageClassName(
                          lead.stage,
                        )}`}
                      >
                        {lead.stage}
                      </span>
                    </td>

                    <td className="truncate px-4 py-4 text-sm text-slate-300">
                      {getCompanyName(lead)}
                    </td>

                    <td className="hidden truncate px-4 py-4 text-sm text-slate-300 2xl:table-cell">
                      {getContactName(lead)}
                    </td>

                    <td className="whitespace-nowrap px-4 py-4 text-sm text-slate-300">
                      {formatEstimatedValue(lead.estimated_value)}
                    </td>

                    <td className="hidden whitespace-nowrap px-4 py-4 text-sm text-slate-300 xl:table-cell">
                      {formatExpectedCloseDate(lead.expected_close_date)}
                    </td>

                    <td className="px-4 py-4">
                      <div className="flex justify-end gap-3">
                        <Link
                          className="text-sm font-semibold text-blue-400 transition hover:text-blue-300"
                          href={`/leads/${lead.id}/edit`}
                        >
                          Edit
                        </Link>

                        <button
                          className="text-sm font-semibold text-red-400 transition hover:text-red-300"
                          onClick={() => openDeleteDialog(lead)}
                          type="button"
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {leadToDelete && (
        <DeleteLeadDialog
          errorMessage={deleteError}
          isDeleting={isDeleting}
          leadTitle={leadToDelete.title}
          onCancel={closeDeleteDialog}
          onConfirm={handleDeleteLead}
        />
      )}
    </AppShell>
  );
}
