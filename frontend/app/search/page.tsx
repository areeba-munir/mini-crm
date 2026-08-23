"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import type { FormEvent } from "react";
import { useState } from "react";

import { AppShell } from "@/components/layout/app-shell";
import { useAuthenticatedUser } from "@/hooks/use-authenticated-user";
import { ApiError } from "@/lib/api";
import { removeAccessToken } from "@/lib/auth-storage";
import { searchCrm } from "@/lib/search-api";
import type { SearchResults } from "@/types/search";

export default function SearchPage() {
  const router = useRouter();

  const {
    user,
    token,
    isLoading: isAuthenticationLoading,
    errorMessage: authenticationError,
  } = useAuthenticatedUser();

  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResults | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [searchError, setSearchError] = useState("");

  async function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!token) {
      return;
    }

    const normalizedQuery = query.trim();

    if (normalizedQuery.length < 2) {
      setSearchError("Enter at least 2 characters to search.");
      setResults(null);
      return;
    }

    setSearchError("");
    setIsSearching(true);

    try {
      const searchResults = await searchCrm(normalizedQuery, token);

      setResults(searchResults);
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        removeAccessToken();
        router.replace("/login");
        return;
      }

      setSearchError(
        error instanceof ApiError ? error.message : "Unable to search the CRM.",
      );
      setResults(null);
    } finally {
      setIsSearching(false);
    }
  }

  if (isAuthenticationLoading || !user || !token) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-950 px-4">
        <p
          className={`text-sm ${
            authenticationError ? "text-red-300" : "text-slate-400"
          }`}
        >
          {authenticationError || "Loading CRM search..."}
        </p>
      </main>
    );
  }

  const totalResults = results
    ? results.companies.length + results.contacts.length + results.leads.length
    : 0;

  return (
    <AppShell user={user}>
      <section>
        <p className="text-sm font-medium text-blue-400">CRM</p>

        <h1 className="mt-1 text-3xl font-bold">Search</h1>

        <p className="mt-2 text-sm text-slate-400">
          Find companies, contacts, and leads across your CRM.
        </p>
      </section>

      <form
        className="mt-8 flex flex-col gap-3 sm:flex-row"
        onSubmit={handleSearch}
      >
        <label className="sr-only" htmlFor="crm-search">
          Search the CRM
        </label>

        <input
          autoComplete="off"
          className="min-w-0 flex-1 rounded-lg border border-slate-700 bg-slate-900 px-4 py-3 text-white outline-none transition placeholder:text-slate-600 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 disabled:cursor-not-allowed disabled:opacity-60"
          disabled={isSearching}
          id="crm-search"
          maxLength={100}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search by company, contact, or lead..."
          type="search"
          value={query}
        />

        <button
          className="rounded-lg bg-blue-600 px-6 py-3 text-sm font-semibold text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:bg-slate-700"
          disabled={isSearching}
          type="submit"
        >
          {isSearching ? "Searching..." : "Search"}
        </button>
      </form>

      {searchError && (
        <section
          className="mt-5 rounded-xl border border-red-500/30 bg-red-500/10 px-5 py-4 text-sm text-red-300"
          role="alert"
        >
          {searchError}
        </section>
      )}

      {!searchError && results && (
        <p className="mt-5 text-sm text-slate-400">
          Found <span className="font-semibold text-white">{totalResults}</span>{" "}
          result{totalResults === 1 ? "" : "s"}.
        </p>
      )}

      {!searchError && results && totalResults === 0 && (
        <section className="mt-8 rounded-2xl border border-dashed border-slate-700 bg-slate-900 p-10 text-center">
          <h2 className="text-lg font-semibold">No matching records</h2>

          <p className="mt-2 text-sm text-slate-400">
            Try another name, email address, title, or keyword.
          </p>
        </section>
      )}

      {results && results.companies.length > 0 && (
        <section className="mt-8">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">Companies</h2>

            <span className="text-sm text-slate-500">
              {results.companies.length}
            </span>
          </div>

          <div className="mt-4 grid gap-4 lg:grid-cols-2">
            {results.companies.map((company) => (
              <article
                className="rounded-2xl border border-slate-800 bg-slate-900 p-5"
                key={company.id}
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <h3 className="font-semibold text-white">{company.name}</h3>

                    <p className="mt-1 text-sm text-slate-400">
                      {company.industry ?? "Industry not provided"}
                    </p>
                  </div>

                  <Link
                    className="text-sm font-semibold text-blue-400 hover:text-blue-300"
                    href={`/companies/${company.id}/edit`}
                  >
                    View
                  </Link>
                </div>

                <p className="mt-4 text-sm text-slate-400">
                  {company.email ??
                    company.phone ??
                    company.website ??
                    "No contact details"}
                </p>
              </article>
            ))}
          </div>
        </section>
      )}

      {results && results.contacts.length > 0 && (
        <section className="mt-8">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">Contacts</h2>

            <span className="text-sm text-slate-500">
              {results.contacts.length}
            </span>
          </div>

          <div className="mt-4 grid gap-4 lg:grid-cols-2">
            {results.contacts.map((contact) => {
              const contactName = [contact.first_name, contact.last_name]
                .filter(Boolean)
                .join(" ");

              return (
                <article
                  className="rounded-2xl border border-slate-800 bg-slate-900 p-5"
                  key={contact.id}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <h3 className="font-semibold text-white">
                        {contactName}
                      </h3>

                      <p className="mt-1 text-sm text-slate-400">
                        {contact.job_title ?? "Job title not provided"}
                      </p>
                    </div>

                    <Link
                      className="text-sm font-semibold text-blue-400 hover:text-blue-300"
                      href={`/contacts/${contact.id}/edit`}
                    >
                      View
                    </Link>
                  </div>

                  <p className="mt-4 text-sm text-slate-400">
                    {contact.email ?? contact.phone ?? "No contact details"}
                  </p>
                </article>
              );
            })}
          </div>
        </section>
      )}

      {results && results.leads.length > 0 && (
        <section className="mt-8">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">Leads</h2>

            <span className="text-sm text-slate-500">
              {results.leads.length}
            </span>
          </div>

          <div className="mt-4 grid gap-4 lg:grid-cols-2">
            {results.leads.map((lead) => (
              <article
                className="rounded-2xl border border-slate-800 bg-slate-900 p-5"
                key={lead.id}
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <h3 className="font-semibold text-white">{lead.title}</h3>

                    <p className="mt-1 text-sm text-slate-400">
                      Stage: {lead.stage}
                    </p>
                  </div>

                  <Link
                    className="text-sm font-semibold text-blue-400 hover:text-blue-300"
                    href={`/leads/${lead.id}/edit`}
                  >
                    View
                  </Link>
                </div>

                <p className="mt-4 text-sm text-slate-400">
                  {lead.source
                    ? `Source: ${lead.source}`
                    : "Source not provided"}
                </p>
              </article>
            ))}
          </div>
        </section>
      )}
    </AppShell>
  );
}
