"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/layout/app-shell";
import { TaskForm } from "@/components/tasks/task-form";
import { useAuthenticatedUser } from "@/hooks/use-authenticated-user";
import { ApiError } from "@/lib/api";
import { removeAccessToken } from "@/lib/auth-storage";
import { listCompanies } from "@/lib/companies-api";
import { listContacts } from "@/lib/contacts-api";
import { listLeads } from "@/lib/leads-api";
import {
  getTask,
  updateTask,
} from "@/lib/tasks-api";
import type { Company } from "@/types/company";
import type { Contact } from "@/types/contact";
import type { Lead } from "@/types/lead";
import type {
  Task,
  TaskCreateInput,
} from "@/types/task";

export default function EditTaskPage() {
  const params = useParams<{
    taskId: string;
  }>();
  const router = useRouter();

  const taskId = Number(params.taskId);

  const isTaskIdValid =
    Number.isInteger(taskId) && taskId >= 1;

  const {
    user,
    token,
    isLoading: isAuthenticationLoading,
    errorMessage: authenticationError,
  } = useAuthenticatedUser();

  const [task, setTask] =
    useState<Task | null>(null);
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
    if (!token || !isTaskIdValid) {
      return;
    }

    let cancelled = false;

    async function loadTaskData(
      accessToken: string,
    ) {
      try {
        const [
          taskRecord,
          companyRecords,
          contactRecords,
          leadRecords,
        ] = await Promise.all([
          getTask(taskId, accessToken),
          listCompanies(accessToken),
          listContacts(accessToken),
          listLeads(accessToken),
        ]);

        if (!cancelled) {
          setTask(taskRecord);
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
            : "Unable to load the task.",
        );
        setIsDataLoading(false);
      }
    }

    void loadTaskData(token);

    return () => {
      cancelled = true;
    };
  }, [
    isTaskIdValid,
    router,
    taskId,
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
            "Loading task editor..."}
        </p>
      </main>
    );
  }

  if (!isTaskIdValid) {
    return (
      <AppShell user={user}>
        <section className="rounded-2xl border border-red-500/30 bg-red-500/10 p-6">
          <h1 className="text-lg font-semibold text-red-300">
            Invalid task
          </h1>

          <p className="mt-2 text-sm text-red-200">
            The task ID must be a positive number.
          </p>
        </section>
      </AppShell>
    );
  }

  if (isDataLoading) {
    return (
      <AppShell user={user}>
        <p className="text-sm text-slate-400">
          Loading task...
        </p>
      </AppShell>
    );
  }

  if (dataError || !task) {
    return (
      <AppShell user={user}>
        <section className="rounded-2xl border border-red-500/30 bg-red-500/10 p-6">
          <h1 className="text-lg font-semibold text-red-300">
            Task unavailable
          </h1>

          <p className="mt-2 text-sm text-red-200">
            {dataError ||
              "The task could not be found."}
          </p>
        </section>
      </AppShell>
    );
  }

  async function handleUpdateTask(
    input: TaskCreateInput,
  ) {
    if (!token || !task) {
      throw new Error(
        "Task or authentication data is unavailable.",
      );
    }

    await updateTask(
      task.id,
      input,
      token,
    );

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
            Edit task
          </h1>

          <p className="mt-2 text-sm text-slate-400">
            Update the task{" "}
            <span className="font-medium text-slate-200">
              {task.title}
            </span>
            .
          </p>
        </div>

        <div className="mt-8 rounded-2xl border border-slate-800 bg-slate-900 p-6 sm:p-8">
          <TaskForm
            cancelHref="/tasks"
            companies={companies}
            contacts={contacts}
            currentUserId={user.id}
            initialValues={{
              title: task.title,
              description: task.description,
              status: task.status,
              priority: task.priority,
              due_at: task.due_at,
              assigned_to_id:
                task.assigned_to_id,
              company_id: task.company_id,
              contact_id: task.contact_id,
              lead_id: task.lead_id,
            }}
            leads={leads}
            onSubmit={handleUpdateTask}
            submitLabel="Save changes"
          />
        </div>
      </section>
    </AppShell>
  );
}