"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { type FormEvent, useEffect, useState } from "react";

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
import type { Lead, LeadListFilters, LeadSort, LeadStage } from "@/types/lead";

const leadStages: LeadStage[] = [
  "New",
  "Contacted",
  "Qualified",
  "Won",
  "Lost",
];

type LeadFilterForm = {
  query: string;
  stage: LeadStage | "";
  companyId: string;
  contactId: string;
  minEstimatedValue: string;
  maxEstimatedValue: string;
  expectedCloseFrom: string;
  expectedCloseTo: string;
  sortBy: LeadSort;
};

const emptyLeadFilterForm: LeadFilterForm = {
  query: "",
  stage: "",
  companyId: "",
  contactId: "",
  minEstimatedValue: "",
  maxEstimatedValue: "",
  expectedCloseFrom: "",
  expectedCloseTo: "",
  sortBy: "newest",
};

const emptyValue = "\u2014";

function buildLeadFilters(filterForm: LeadFilterForm): LeadListFilters {
  return {
    q: filterForm.query.trim() || undefined,
    stage: filterForm.stage || undefined,
    company_id: filterForm.companyId ? Number(filterForm.companyId) : undefined,
    contact_id: filterForm.contactId ? Number(filterForm.contactId) : undefined,
    min_estimated_value: filterForm.minEstimatedValue || undefined,
    max_estimated_value: filterForm.maxEstimatedValue || undefined,
    expected_close_from: filterForm.expectedCloseFrom || undefined,
    expected_close_to: filterForm.expectedCloseTo || undefined,
    sort_by: filterForm.sortBy,
  };
}

function hasActiveLeadFilters(filters: LeadListFilters): boolean {
  return Boolean(
    filters.q ||
    filters.stage ||
    filters.company_id ||
    filters.contact_id ||
    filters.min_estimated_value ||
    filters.max_estimated_value ||
    filters.expected_close_from ||
    filters.expected_close_to ||
    (filters.sort_by && filters.sort_by !== "newest"),
  );
}

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

  const [draftFilters, setDraftFilters] = useState<LeadFilterForm>({
    ...emptyLeadFilterForm,
  });
  const [appliedFilters, setAppliedFilters] = useState<LeadListFilters>({
    sort_by: "newest",
  });

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
            listLeads(accessToken, appliedFilters),
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
  }, [appliedFilters, router, token]);

  const companyNamesById = new Map(
    companies.map((company) => [company.id, company.name]),
  );

  const contactNamesById = new Map(
    contacts.map((contact) => [
      contact.id,
      [contact.first_name, contact.last_name].filter(Boolean).join(" "),
    ]),
  );

  const hasActiveFilters = hasActiveLeadFilters(appliedFilters);

  function getCompanyName(lead: Lead) {
    return companyNamesById.get(lead.company_id) ?? "Unknown company";
  }

  function getContactName(lead: Lead) {
    if (lead.contact_id === null) {
      return emptyValue;
    }

    return contactNamesById.get(lead.contact_id) ?? "Unknown contact";
  }

  function handleApplyFilters(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setDataError("");
    setIsDataLoading(true);
    setAppliedFilters(buildLeadFilters(draftFilters));
  }

  function handleClearFilters() {
    const clearedFilters = {
      ...emptyLeadFilterForm,
    };

    setDraftFilters(clearedFilters);
    setDataError("");
    setIsDataLoading(true);
    setAppliedFilters(buildLeadFilters(clearedFilters));
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
      <section className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm font-medium text-blue-400">Sales</p>

          <h1 className="mt-1 text-3xl font-bold">Leads</h1>

          <p className="mt-2 text-sm text-slate-400">
            Track sales opportunities through your CRM pipeline.
          </p>
        </div>

        <Link
          className="rounded-lg bg-blue-600 px-5 py-3 text-center text-sm font-semibold text-white transition hover:bg-blue-500"
          href="/leads/new"
        >
          Add lead
        </Link>
      </section>

      <section className="mt-6 rounded-2xl border border-slate-800 bg-slate-900 p-5 sm:p-6">
        <div>
          <p className="text-sm font-medium text-blue-400">
            Advanced filtering
          </p>

          <h2 className="mt-1 text-xl font-semibold">Find opportunities</h2>

          <p className="mt-2 text-sm text-slate-400">
            Combine text, relationship, value, date, stage, and sorting
            criteria.
          </p>
        </div>

        <form className="mt-6" onSubmit={handleApplyFilters}>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <label className="text-sm text-slate-300 sm:col-span-2">
              <span className="mb-2 block">Search</span>

              <input
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white outline-none placeholder:text-slate-600 focus:border-blue-500"
                maxLength={200}
                onChange={(event) =>
                  setDraftFilters((currentFilters) => ({
                    ...currentFilters,
                    query: event.target.value,
                  }))
                }
                placeholder="Title, source, or description"
                type="search"
                value={draftFilters.query}
              />
            </label>

            <label className="text-sm text-slate-300">
              <span className="mb-2 block">Pipeline stage</span>

              <select
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white outline-none focus:border-blue-500"
                onChange={(event) =>
                  setDraftFilters((currentFilters) => ({
                    ...currentFilters,
                    stage: event.target.value as LeadStage | "",
                  }))
                }
                value={draftFilters.stage}
              >
                <option value="">All stages</option>

                {leadStages.map((stage) => (
                  <option key={stage} value={stage}>
                    {stage}
                  </option>
                ))}
              </select>
            </label>

            <label className="text-sm text-slate-300">
              <span className="mb-2 block">Sort by</span>

              <select
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white outline-none focus:border-blue-500"
                onChange={(event) =>
                  setDraftFilters((currentFilters) => ({
                    ...currentFilters,
                    sortBy: event.target.value as LeadSort,
                  }))
                }
                value={draftFilters.sortBy}
              >
                <option value="newest">Newest first</option>
                <option value="oldest">Oldest first</option>
                <option value="value_high">Value: high to low</option>
                <option value="value_low">Value: low to high</option>
                <option value="close_soon">Expected close: soonest</option>
              </select>
            </label>

            <label className="text-sm text-slate-300">
              <span className="mb-2 block">Company</span>

              <select
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white outline-none focus:border-blue-500"
                onChange={(event) =>
                  setDraftFilters((currentFilters) => ({
                    ...currentFilters,
                    companyId: event.target.value,
                  }))
                }
                value={draftFilters.companyId}
              >
                <option value="">All companies</option>

                {companies.map((company) => (
                  <option key={company.id} value={company.id}>
                    {company.name}
                  </option>
                ))}
              </select>
            </label>

            <label className="text-sm text-slate-300">
              <span className="mb-2 block">Contact</span>

              <select
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white outline-none focus:border-blue-500"
                onChange={(event) =>
                  setDraftFilters((currentFilters) => ({
                    ...currentFilters,
                    contactId: event.target.value,
                  }))
                }
                value={draftFilters.contactId}
              >
                <option value="">All contacts</option>

                {contacts.map((contact) => {
                  const contactName = [contact.first_name, contact.last_name]
                    .filter(Boolean)
                    .join(" ");

                  return (
                    <option key={contact.id} value={contact.id}>
                      {contactName}
                    </option>
                  );
                })}
              </select>
            </label>

            <label className="text-sm text-slate-300">
              <span className="mb-2 block">Minimum value</span>

              <input
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white outline-none placeholder:text-slate-600 focus:border-blue-500"
                min="0"
                onChange={(event) =>
                  setDraftFilters((currentFilters) => ({
                    ...currentFilters,
                    minEstimatedValue: event.target.value,
                  }))
                }
                placeholder="0.00"
                step="0.01"
                type="number"
                value={draftFilters.minEstimatedValue}
              />
            </label>

            <label className="text-sm text-slate-300">
              <span className="mb-2 block">Maximum value</span>

              <input
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white outline-none placeholder:text-slate-600 focus:border-blue-500"
                min="0"
                onChange={(event) =>
                  setDraftFilters((currentFilters) => ({
                    ...currentFilters,
                    maxEstimatedValue: event.target.value,
                  }))
                }
                placeholder="0.00"
                step="0.01"
                type="number"
                value={draftFilters.maxEstimatedValue}
              />
            </label>

            <label className="text-sm text-slate-300">
              <span className="mb-2 block">Expected close from</span>

              <input
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white outline-none focus:border-blue-500"
                onChange={(event) =>
                  setDraftFilters((currentFilters) => ({
                    ...currentFilters,
                    expectedCloseFrom: event.target.value,
                  }))
                }
                type="date"
                value={draftFilters.expectedCloseFrom}
              />
            </label>

            <label className="text-sm text-slate-300">
              <span className="mb-2 block">Expected close to</span>

              <input
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white outline-none focus:border-blue-500"
                onChange={(event) =>
                  setDraftFilters((currentFilters) => ({
                    ...currentFilters,
                    expectedCloseTo: event.target.value,
                  }))
                }
                type="date"
                value={draftFilters.expectedCloseTo}
              />
            </label>
          </div>

          <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:justify-end">
            <button
              className="rounded-lg border border-slate-700 px-5 py-3 text-sm font-semibold text-slate-300 transition hover:border-slate-600 hover:text-white disabled:cursor-not-allowed disabled:opacity-60"
              disabled={isDataLoading}
              onClick={handleClearFilters}
              type="button"
            >
              Clear filters
            </button>

            <button
              className="rounded-lg bg-blue-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-60"
              disabled={isDataLoading}
              type="submit"
            >
              {isDataLoading ? "Loading..." : "Apply filters"}
            </button>
          </div>
        </form>
      </section>

      <p className="mt-5 text-sm text-slate-400">
        Matching leads:{" "}
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
          <h2 className="text-lg font-semibold">
            {hasActiveFilters
              ? "No leads match these filters"
              : "No leads found"}
          </h2>

          <p className="mt-2 text-sm text-slate-400">
            {hasActiveFilters
              ? "Adjust or clear the filters to broaden your results."
              : "Create your first sales opportunity."}
          </p>

          {hasActiveFilters ? (
            <button
              className="mt-5 inline-flex rounded-lg border border-slate-700 px-5 py-3 text-sm font-semibold text-slate-200 transition hover:border-slate-600 hover:text-white"
              onClick={handleClearFilters}
              type="button"
            >
              Clear filters
            </button>
          ) : (
            <Link
              className="mt-5 inline-flex rounded-lg bg-blue-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-blue-500"
              href="/leads/new"
            >
              Add your first lead
            </Link>
          )}
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
