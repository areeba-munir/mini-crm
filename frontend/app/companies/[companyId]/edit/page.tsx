"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { CompanyForm } from "@/components/companies/company-form";
import { AppShell } from "@/components/layout/app-shell";
import { useAuthenticatedUser } from "@/hooks/use-authenticated-user";
import { ApiError } from "@/lib/api";
import { removeAccessToken } from "@/lib/auth-storage";
import {
  getCompany,
  updateCompany,
} from "@/lib/companies-api";
import type {
  Company,
  CompanyCreateInput,
} from "@/types/company";

export default function EditCompanyPage() {
  const params = useParams<{
    companyId: string;
  }>();
  const router = useRouter();

  const companyId = Number(params.companyId);

  const isCompanyIdValid =
    Number.isInteger(companyId) && companyId >= 1;

  const {
    user,
    token,
    isLoading: isAuthenticationLoading,
    errorMessage: authenticationError,
  } = useAuthenticatedUser();

  const [company, setCompany] =
    useState<Company | null>(null);
  const [isCompanyLoading, setIsCompanyLoading] =
    useState(true);
  const [companyError, setCompanyError] =
    useState("");

  useEffect(() => {
    if (!token || !isCompanyIdValid) {
      return;
    }

    let cancelled = false;

    async function loadCompany(
      accessToken: string,
    ) {
      try {
        const companyRecord = await getCompany(
          companyId,
          accessToken,
        );

        if (!cancelled) {
          setCompany(companyRecord);
          setIsCompanyLoading(false);
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

        setCompanyError(
          error instanceof ApiError
            ? error.message
            : "Unable to load the company.",
        );
        setIsCompanyLoading(false);
      }
    }

    void loadCompany(token);

    return () => {
      cancelled = true;
    };
  }, [
    companyId,
    isCompanyIdValid,
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
            "Loading company editor..."}
        </p>
      </main>
    );
  }

  if (!isCompanyIdValid) {
    return (
      <AppShell user={user}>
        <section className="rounded-2xl border border-red-500/30 bg-red-500/10 p-6">
          <h1 className="text-lg font-semibold text-red-300">
            Invalid company
          </h1>

          <p className="mt-2 text-sm text-red-200">
            The company ID must be a positive number.
          </p>
        </section>
      </AppShell>
    );
  }

  if (isCompanyLoading) {
    return (
      <AppShell user={user}>
        <p className="text-sm text-slate-400">
          Loading company...
        </p>
      </AppShell>
    );
  }

  if (companyError || !company) {
    return (
      <AppShell user={user}>
        <section className="rounded-2xl border border-red-500/30 bg-red-500/10 p-6">
          <h1 className="text-lg font-semibold text-red-300">
            Company unavailable
          </h1>

          <p className="mt-2 text-sm text-red-200">
            {companyError ||
              "The company could not be found."}
          </p>
        </section>
      </AppShell>
    );
  }

  async function handleUpdateCompany(
    input: CompanyCreateInput,
  ) {
    if (!token || !company) {
      throw new Error(
        "Company or authentication data is unavailable.",
      );
    }

    await updateCompany(
      company.id,
      input,
      token,
    );

    router.push("/companies");
  }

  return (
    <AppShell user={user}>
      <section className="mx-auto max-w-3xl">
        <div>
          <p className="text-sm font-medium text-blue-400">
            Companies
          </p>

          <h1 className="mt-1 text-3xl font-bold">
            Edit company
          </h1>

          <p className="mt-2 text-sm text-slate-400">
            Update the information stored for{" "}
            <span className="font-medium text-slate-200">
              {company.name}
            </span>
            .
          </p>
        </div>

        <div className="mt-8 rounded-2xl border border-slate-800 bg-slate-900 p-6 sm:p-8">
          <CompanyForm
            cancelHref="/companies"
            initialValues={{
              name: company.name,
              industry: company.industry ?? "",
              website: company.website ?? "",
              email: company.email ?? "",
              phone: company.phone ?? "",
              address: company.address ?? "",
            }}
            onSubmit={handleUpdateCompany}
            submitLabel="Save changes"
          />
        </div>
      </section>
    </AppShell>
  );
}