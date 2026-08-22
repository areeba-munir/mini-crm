"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/layout/app-shell";
import { TaskForm } from "@/components/tasks/task-form";
import { useAuthenticatedUser } from "@/hooks/use-authenticated-user";
import { ApiError } from "@/lib/api";
import { removeAccessToken } from "@/lib/auth-storage";
import { listCompanies } from "@/lib/companies-api";
import { listContacts } from "@/lib/contacts-api";
import { listLeads } from "@/lib/leads-api";
import { createTask } from "@/lib/tasks-api";
import type { Company } from "@/types/company";
import type { Contact } from "@/types/contact";
import type { Lead } from "@/types/lead";
import type { TaskCreateInput } from "@/types/task";

export default function NewTaskPage() {
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
  const [leads, setLeads] = useState<Lead[]>([]);
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
          leadRecords,
        ] = await Promise.all([
          listCompanies(accessToken),
          listContacts(accessToken),
          listLeads(accessToken),
        ]);

        if (!cancelled) {
          setCompanies(companyRecords);
          setContacts(contactRecords);
          setLeads(leadRecords);
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
            : "Unable to load the task form.",
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
            "Loading task form..."}
        </p>
      </main>
    );
  }

  if (isDataLoading) {
    return (
      <AppShell user={user}>
        <p className="text-sm text-slate-400">
          Loading related CRM records...
        </p>
      </AppShell>
    );
  }

  if (dataError) {
    return (
      <AppShell user={user}>
        <section className="rounded-2xl border border-red-500/30 bg-red-500/10 p-6">
          <h1 className="text-lg font-semibold text-red-300">
            Task form unavailable
          </h1>

          <p className="mt-2 text-sm text-red-200">
            {dataError}
          </p>
        </section>
      </AppShell>
    );
  }

  async function handleCreateTask(
    input: TaskCreateInput,
  ) {
    if (!token) {
      throw new Error(
        "Authentication token is unavailable.",
      );
    }

    await createTask(input, token);
    router.push("/tasks");
  }

  return (
    <AppShell user={user}>
      <section className="mx-auto max-w-3xl">
        <div>
          <p className="text-sm font-medium text-blue-400">
            Tasks
          </p>

          <h1 className="mt-1 text-3xl font-bold">
            Add task
          </h1>

          <p className="mt-2 text-sm text-slate-400">
            Create work for yourself and optionally
            connect it to a CRM record.
          </p>
        </div>

        <div className="mt-8 rounded-2xl border border-slate-800 bg-slate-900 p-6 sm:p-8">
          <TaskForm
            cancelHref="/tasks"
            companies={companies}
            contacts={contacts}
            currentUserId={user.id}
            leads={leads}
            onSubmit={handleCreateTask}
            submitLabel="Create task"
          />
        </div>
      </section>
    </AppShell>
  );
}