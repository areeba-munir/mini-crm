"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/layout/app-shell";
import { useAuthenticatedUser } from "@/hooks/use-authenticated-user";
import { ApiError } from "@/lib/api";
import { removeAccessToken } from "@/lib/auth-storage";
import { listCompanies } from "@/lib/companies-api";
import { listContacts } from "@/lib/contacts-api";
import type { Company } from "@/types/company";
import type { Contact } from "@/types/contact";

export default function ContactsPage() {
  const router = useRouter();

  const {
    user,
    token,
    isLoading: isAuthenticationLoading,
    errorMessage: authenticationError,
  } = useAuthenticatedUser();

  const [contacts, setContacts] = useState<Contact[]>(
    [],
  );
  const [companies, setCompanies] = useState<Company[]>(
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

    async function loadContactData(
      accessToken: string,
    ) {
      try {
        const [
          contactRecords,
          companyRecords,
        ] = await Promise.all([
          listContacts(accessToken),
          listCompanies(accessToken),
        ]);

        if (!cancelled) {
          setContacts(contactRecords);
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
            : "Unable to load contacts.",
        );
        setIsDataLoading(false);
      }
    }

    void loadContactData(token);

    return () => {
      cancelled = true;
    };
  }, [router, token]);

  const companyNamesById = new Map(
    companies.map((company) => [
      company.id,
      company.name,
    ]),
  );

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
          Loading contacts...
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
            Contacts
          </h1>

          <p className="mt-2 text-sm text-slate-400">
            View people and their related companies.
          </p>
        </div>

        <div className="rounded-lg border border-slate-800 bg-slate-900 px-4 py-3 text-sm">
          <span className="text-slate-400">
            Total contacts:
          </span>{" "}
          <span className="font-semibold text-white">
            {contacts.length}
          </span>
        </div>
      </section>

      {isDataLoading && (
        <section className="mt-8 rounded-2xl border border-slate-800 bg-slate-900 p-8 text-center">
          <p className="text-sm text-slate-400">
            Loading contact records...
          </p>
        </section>
      )}

      {!isDataLoading && dataError && (
        <section className="mt-8 rounded-2xl border border-red-500/30 bg-red-500/10 p-6">
          <h2 className="font-semibold text-red-300">
            Contacts unavailable
          </h2>

          <p className="mt-2 text-sm text-red-200">
            {dataError}
          </p>
        </section>
      )}

      {!isDataLoading &&
        !dataError &&
        contacts.length === 0 && (
          <section className="mt-8 rounded-2xl border border-dashed border-slate-700 bg-slate-900 p-10 text-center">
            <h2 className="text-lg font-semibold">
              No contacts yet
            </h2>

            <p className="mt-2 text-sm text-slate-400">
              Add your first contact and optionally
              connect them to a company.
            </p>
          </section>
        )}

      {!isDataLoading &&
        !dataError &&
        contacts.length > 0 && (
          <section className="mt-8 overflow-hidden rounded-2xl border border-slate-800 bg-slate-900">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[850px] text-left">
                <thead className="border-b border-slate-800">
                  <tr className="text-xs uppercase tracking-wider text-slate-500">
                    <th className="px-6 py-4 font-medium">
                      Contact
                    </th>

                    <th className="px-6 py-4 font-medium">
                      Job title
                    </th>

                    <th className="px-6 py-4 font-medium">
                      Company
                    </th>

                    <th className="px-6 py-4 font-medium">
                      Email
                    </th>

                    <th className="px-6 py-4 font-medium">
                      Phone
                    </th>
                  </tr>
                </thead>

                <tbody className="divide-y divide-slate-800">
                  {contacts.map((contact) => {
                    const fullName = [
                      contact.first_name,
                      contact.last_name,
                    ]
                      .filter(Boolean)
                      .join(" ");

                    const companyName =
                      contact.company_id === null
                        ? "Unassigned"
                        : companyNamesById.get(
                            contact.company_id,
                          ) ?? "Unknown company";

                    return (
                      <tr
                        className="transition hover:bg-slate-800/50"
                        key={contact.id}
                      >
                        <td className="px-6 py-4">
                          <p className="font-medium text-white">
                            {fullName}
                          </p>

                          <p className="mt-1 text-xs text-slate-500">
                            Contact #{contact.id}
                          </p>
                        </td>

                        <td className="px-6 py-4 text-sm text-slate-300">
                          {contact.job_title ?? "—"}
                        </td>

                        <td className="px-6 py-4 text-sm text-slate-300">
                          {companyName}
                        </td>

                        <td className="px-6 py-4 text-sm text-slate-300">
                          {contact.email ?? "—"}
                        </td>

                        <td className="px-6 py-4 text-sm text-slate-300">
                          {contact.phone ?? "—"}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </section>
        )}
    </AppShell>
  );
}