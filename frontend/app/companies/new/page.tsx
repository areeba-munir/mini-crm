"use client";

import { useRouter } from "next/navigation";

import { CompanyForm } from "@/components/companies/company-form";
import { AppShell } from "@/components/layout/app-shell";
import { useToast } from "@/components/ui/toast-provider";
import { useAuthenticatedUser } from "@/hooks/use-authenticated-user";
import { createCompany } from "@/lib/companies-api";
import type { CompanyCreateInput } from "@/types/company";

export default function NewCompanyPage() {
  const router = useRouter();
  const { showToast } = useToast();

  const { user, token, isLoading, errorMessage } = useAuthenticatedUser();

  if (isLoading || !user || !token) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-950 px-4">
        <p
          className={`text-sm ${
            errorMessage ? "text-red-300" : "text-slate-400"
          }`}
        >
          {errorMessage || "Loading company form..."}
        </p>
      </main>
    );
  }

  async function handleCreateCompany(input: CompanyCreateInput) {
    if (!token) {
      throw new Error("Authentication token is unavailable.");
    }

    await createCompany(input, token);

    showToast("Company created successfully.", "success");

    router.push("/companies");
  }

  return (
    <AppShell user={user}>
      <section className="mx-auto max-w-3xl">
        <div>
          <p className="text-sm font-medium text-blue-400">Companies</p>

          <h1 className="mt-1 text-3xl font-bold">Add company</h1>

          <p className="mt-2 text-sm text-slate-400">
            Create an organization that can later be connected to contacts and
            leads.
          </p>
        </div>

        <div className="mt-8 rounded-2xl border border-slate-800 bg-slate-900 p-6 sm:p-8">
          <CompanyForm
            cancelHref="/companies"
            onSubmit={handleCreateCompany}
            submitLabel="Create company"
          />
        </div>
      </section>
    </AppShell>
  );
}
