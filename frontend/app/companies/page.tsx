"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { DeleteCompanyDialog } from "@/components/companies/delete-company-dialog";
import { AppShell } from "@/components/layout/app-shell";
import { useAuthenticatedUser } from "@/hooks/use-authenticated-user";
import { ApiError } from "@/lib/api";
import { removeAccessToken } from "@/lib/auth-storage";
import {
  deleteCompany as deleteCompanyRecord,
  listCompanies,
} from "@/lib/companies-api";
import type { Company } from "@/types/company";

export default function CompaniesPage() {
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
  const [isCompaniesLoading, setIsCompaniesLoading] =
    useState(true);
  const [companiesError, setCompaniesError] =
    useState("");

  const [companyToDelete, setCompanyToDelete] =
    useState<Company | null>(null);
  const [isDeleting, setIsDeleting] =
    useState(false);
  const [deleteError, setDeleteError] =
    useState("");

  useEffect(() => {
    if (!token) {
      return;
    }

    let cancelled = false;

    async function loadCompanies(
      accessToken: string,
    ) {
      try {
        const companyRecords = await listCompanies(
          accessToken,
        );

        if (!cancelled) {
          setCompanies(companyRecords);
          setIsCompaniesLoading(false);
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

  function openDeleteDialog(company: Company) {
    setDeleteError("");
    setCompanyToDelete(company);
  }

  function closeDeleteDialog() {
    if (isDeleting) {
      return;
    }

    setDeleteError("");
    setCompanyToDelete(null);
  }

  async function handleDeleteCompany() {
    const company = companyToDelete;
    const accessToken = token;

    if (!company || !accessToken) {
      return;
    }

    setDeleteError("");
    setIsDeleting(true);

    try {
      await deleteCompanyRecord(
        company.id,
        accessToken,
      );

      setCompanies((currentCompanies) =>
        currentCompanies.filter(
          (currentCompany) =>
            currentCompany.id !== company.id,
        ),
      );

      setCompanyToDelete(null);
    } catch (error) {
      if (
        error instanceof ApiError &&
        error.status === 401
      ) {
        removeAccessToken();
        router.replace("/login");
        return;
      }

      setDeleteError(
        error instanceof ApiError
          ? error.message
          : "Unable to delete the company.",
      );
    } finally {
      setIsDeleting(false);
    }
  }

  if (isAuthenticationLoading || !user || !token) {
    if (authenticationError) {
      return (
        <main className="flex min-h-screen items-center justify-center bg-slate-950 px-4">
          <p className="text-sm text-red-300">
            {authenticationError}
          </p>
        </main>
      );
    }

    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-950">
        <p className="text-sm text-slate-400">
          Loading companies...
        </p>
      </main>
    );
  }

  return (
    <AppShell user={user}>
      <section className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm font-medium text-blue-400">
            Clients
          </p>

          <h1 className="mt-1 text-3xl font-bold">
            Companies
          </h1>

          <p className="mt-2 text-sm text-slate-400">
            View and manage organizations in your CRM.
          </p>
        </div>

        <div className="flex flex-col gap-3 sm:items-end">
          <Link
            className="rounded-lg bg-blue-600 px-5 py-3 text-center text-sm font-semibold text-white transition hover:bg-blue-500"
            href="/companies/new"
          >
            Add company
          </Link>

          <div className="rounded-lg border border-slate-800 bg-slate-900 px-4 py-3 text-sm">
            <span className="text-slate-400">
              Total companies:
            </span>{" "}
            <span className="font-semibold text-white">
              {companies.length}
            </span>
          </div>
        </div>
      </section>

      {isCompaniesLoading && (
        <section className="mt-8 rounded-2xl border border-slate-800 bg-slate-900 p-8 text-center">
          <p className="text-sm text-slate-400">
            Loading company records...
          </p>
        </section>
      )}

      {!isCompaniesLoading && companiesError && (
        <section className="mt-8 rounded-2xl border border-red-500/30 bg-red-500/10 p-6">
          <h2 className="font-semibold text-red-300">
            Companies unavailable
          </h2>

          <p className="mt-2 text-sm text-red-200">
            {companiesError}
          </p>
        </section>
      )}

      {!isCompaniesLoading &&
        !companiesError &&
        companies.length === 0 && (
          <section className="mt-8 rounded-2xl border border-dashed border-slate-700 bg-slate-900 p-10 text-center">
            <h2 className="text-lg font-semibold">
              No companies yet
            </h2>

            <p className="mt-2 text-sm text-slate-400">
              Create your first company to start
              organizing contacts and leads.
            </p>
          </section>
        )}

      {!isCompaniesLoading &&
        !companiesError &&
        companies.length > 0 && (
          <section className="mt-8 overflow-hidden rounded-2xl border border-slate-800 bg-slate-900">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[900px] text-left">
                <thead className="border-b border-slate-800 bg-slate-900">
                  <tr className="text-xs uppercase tracking-wider text-slate-500">
                    <th className="px-6 py-4 font-medium">
                      Company
                    </th>

                    <th className="px-6 py-4 font-medium">
                      Industry
                    </th>

                    <th className="px-6 py-4 font-medium">
                      Email
                    </th>

                    <th className="px-6 py-4 font-medium">
                      Phone
                    </th>

                    <th className="px-6 py-4 font-medium">
                      Website
                    </th>

                    <th className="px-6 py-4 text-right font-medium">
                      Actions
                    </th>
                  </tr>
                </thead>

                <tbody className="divide-y divide-slate-800">
                  {companies.map((company) => (
                    <tr
                      className="transition hover:bg-slate-800/50"
                      key={company.id}
                    >
                      <td className="px-6 py-4">
                        <p className="font-medium text-white">
                          {company.name}
                        </p>

                        <p className="mt-1 text-xs text-slate-500">
                          Company #{company.id}
                        </p>
                      </td>

                      <td className="px-6 py-4 text-sm text-slate-300">
                        {company.industry ?? "—"}
                      </td>

                      <td className="px-6 py-4 text-sm text-slate-300">
                        {company.email ?? "—"}
                      </td>

                      <td className="px-6 py-4 text-sm text-slate-300">
                        {company.phone ?? "—"}
                      </td>

                      <td className="max-w-xs truncate px-6 py-4 text-sm text-slate-300">
                        {company.website ?? "—"}
                      </td>

                      <td className="px-6 py-4">
                        <div className="flex items-center justify-end gap-4">
                          <Link
                            className="text-sm font-semibold text-blue-400 transition hover:text-blue-300"
                            href={`/companies/${company.id}/edit`}
                          >
                            Edit
                          </Link>

                          <button
                            className="text-sm font-semibold text-red-400 transition hover:text-red-300"
                            onClick={() =>
                              openDeleteDialog(company)
                            }
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

      <DeleteCompanyDialog
        company={companyToDelete}
        errorMessage={deleteError}
        isDeleting={isDeleting}
        onCancel={closeDeleteDialog}
        onConfirm={handleDeleteCompany}
      />
    </AppShell>
  );
}