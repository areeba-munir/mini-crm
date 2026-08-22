"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/layout/app-shell";
import { DeleteTaskDialog } from "@/components/tasks/delete-task-dialog";
import { useAuthenticatedUser } from "@/hooks/use-authenticated-user";
import { ApiError } from "@/lib/api";
import { removeAccessToken } from "@/lib/auth-storage";
import { listCompanies } from "@/lib/companies-api";
import { listContacts } from "@/lib/contacts-api";
import { listLeads } from "@/lib/leads-api";
import {
  deleteTask,
  listTasks,
} from "@/lib/tasks-api";
import type { Company } from "@/types/company";
import type { Contact } from "@/types/contact";
import type { Lead } from "@/types/lead";
import type {
  Task,
  TaskPriority,
  TaskStatus,
} from "@/types/task";

const taskStatuses: TaskStatus[] = [
  "Pending",
  "In Progress",
  "Completed",
];

const taskPriorities: TaskPriority[] = [
  "Low",
  "Medium",
  "High",
];

function getStatusClassName(status: TaskStatus) {
  switch (status) {
    case "Completed":
      return "bg-emerald-500/10 text-emerald-300";
    case "In Progress":
      return "bg-blue-500/10 text-blue-300";
    default:
      return "bg-amber-500/10 text-amber-300";
  }
}

function getPriorityClassName(
  priority: TaskPriority,
) {
  switch (priority) {
    case "High":
      return "text-red-300";
    case "Low":
      return "text-slate-400";
    default:
      return "text-amber-300";
  }
}

export default function TasksPage() {
  const router = useRouter();

  const {
    user,
    token,
    isLoading: isAuthenticationLoading,
    errorMessage: authenticationError,
  } = useAuthenticatedUser();

  const [tasks, setTasks] = useState<Task[]>([]);
  const [companies, setCompanies] = useState<Company[]>(
    [],
  );
  const [contacts, setContacts] = useState<Contact[]>(
    [],
  );
  const [leads, setLeads] = useState<Lead[]>([]);

  const [selectedStatus, setSelectedStatus] =
    useState<TaskStatus | "">("");
  const [selectedPriority, setSelectedPriority] =
    useState<TaskPriority | "">("");
  const [showMyTasks, setShowMyTasks] =
    useState(false);

  const [isDataLoading, setIsDataLoading] =
    useState(true);
  const [dataError, setDataError] = useState("");

  const [taskToDelete, setTaskToDelete] =
    useState<Task | null>(null);
  const [isDeleting, setIsDeleting] =
    useState(false);
  const [deleteError, setDeleteError] =
    useState("");

  useEffect(() => {
    if (!token || !user) {
      return;
    }

    const currentUserId = user.id;
    let cancelled = false;

    async function loadTaskData(
      accessToken: string,
    ) {
      try {
        const [
          taskRecords,
          companyRecords,
          contactRecords,
          leadRecords,
        ] = await Promise.all([
          listTasks(accessToken, {
            ...(selectedStatus
              ? { status: selectedStatus }
              : {}),
            ...(selectedPriority
              ? { priority: selectedPriority }
              : {}),
            ...(showMyTasks
              ? {
                  assigned_to_id:
                    currentUserId,
                }
              : {}),
          }),
          listCompanies(accessToken),
          listContacts(accessToken),
          listLeads(accessToken),
        ]);

        if (!cancelled) {
          setTasks(taskRecords);
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
            : "Unable to load tasks.",
        );
        setIsDataLoading(false);
      }
    }

    void loadTaskData(token);

    return () => {
      cancelled = true;
    };
  }, [
    router,
    selectedPriority,
    selectedStatus,
    showMyTasks,
    token,
    user,
  ]);

  const companyNamesById = new Map(
    companies.map((company) => [
      company.id,
      company.name,
    ]),
  );

  const contactNamesById = new Map(
    contacts.map((contact) => [
      contact.id,
      [
        contact.first_name,
        contact.last_name,
      ]
        .filter(Boolean)
        .join(" "),
    ]),
  );

  const leadTitlesById = new Map(
    leads.map((lead) => [
      lead.id,
      lead.title,
    ]),
  );

  function getRelatedRecord(task: Task) {
    if (task.company_id !== null) {
      return (
        companyNamesById.get(task.company_id) ??
        "Unknown company"
      );
    }

    if (task.contact_id !== null) {
      return (
        contactNamesById.get(task.contact_id) ??
        "Unknown contact"
      );
    }

    if (task.lead_id !== null) {
      return (
        leadTitlesById.get(task.lead_id) ??
        "Unknown lead"
      );
    }

    return "General task";
  }

  async function handleDeleteTask() {
    if (!token || !taskToDelete) {
      return;
    }

    setIsDeleting(true);
    setDeleteError("");

    try {
      await deleteTask(
        taskToDelete.id,
        token,
      );

      setTasks((currentTasks) =>
        currentTasks.filter(
          (task) =>
            task.id !== taskToDelete.id,
        ),
      );

      setTaskToDelete(null);
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
          : "Unable to delete the task.",
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
          Loading tasks...
        </p>
      </main>
    );
  }

  return (
    <AppShell user={user}>
      <section className="flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between">
        <div>
          <p className="text-sm font-medium text-blue-400">
            Work
          </p>

          <h1 className="mt-1 text-3xl font-bold">
            Tasks
          </h1>

          <p className="mt-2 text-sm text-slate-400">
            Organize work and track its progress.
          </p>
        </div>

        <div className="flex flex-wrap items-end gap-3">
          <label className="text-sm text-slate-300">
            <span className="mb-2 block">
              Status
            </span>

            <select
              className="rounded-lg border border-slate-700 bg-slate-900 px-4 py-3 text-sm text-white outline-none focus:border-blue-500"
              onChange={(event) => {
                setDataError("");
                setIsDataLoading(true);
                setSelectedStatus(
                  event.target.value as
                    | TaskStatus
                    | "",
                );
              }}
              value={selectedStatus}
            >
              <option value="">All statuses</option>

              {taskStatuses.map((status) => (
                <option key={status} value={status}>
                  {status}
                </option>
              ))}
            </select>
          </label>

          <label className="text-sm text-slate-300">
            <span className="mb-2 block">
              Priority
            </span>

            <select
              className="rounded-lg border border-slate-700 bg-slate-900 px-4 py-3 text-sm text-white outline-none focus:border-blue-500"
              onChange={(event) => {
                setDataError("");
                setIsDataLoading(true);
                setSelectedPriority(
                  event.target.value as
                    | TaskPriority
                    | "",
                );
              }}
              value={selectedPriority}
            >
              <option value="">All priorities</option>

              {taskPriorities.map((priority) => (
                <option
                  key={priority}
                  value={priority}
                >
                  {priority}
                </option>
              ))}
            </select>
          </label>

          <label className="flex min-h-11 items-center gap-2 rounded-lg border border-slate-700 bg-slate-900 px-4 text-sm text-slate-300">
            <input
              checked={showMyTasks}
              className="size-4 accent-blue-600"
              onChange={(event) => {
                setDataError("");
                setIsDataLoading(true);
                setShowMyTasks(
                  event.target.checked,
                );
              }}
              type="checkbox"
            />

            My tasks
          </label>

          <Link
            className="rounded-lg bg-blue-600 px-5 py-3 text-center text-sm font-semibold text-white transition hover:bg-blue-500"
            href="/tasks/new"
          >
            Add task
          </Link>
        </div>
      </section>

      <p className="mt-5 text-sm text-slate-400">
        Total tasks:{" "}
        <span className="font-semibold text-white">
          {tasks.length}
        </span>
      </p>

      {isDataLoading && (
        <section className="mt-8 rounded-2xl border border-slate-800 bg-slate-900 p-8 text-center">
          <p className="text-sm text-slate-400">
            Loading task records...
          </p>
        </section>
      )}

      {!isDataLoading && dataError && (
        <section className="mt-8 rounded-2xl border border-red-500/30 bg-red-500/10 p-6">
          <h2 className="font-semibold text-red-300">
            Tasks unavailable
          </h2>

          <p className="mt-2 text-sm text-red-200">
            {dataError}
          </p>
        </section>
      )}

      {!isDataLoading &&
        !dataError &&
        tasks.length === 0 && (
          <section className="mt-8 rounded-2xl border border-dashed border-slate-700 bg-slate-900 p-10 text-center">
            <h2 className="text-lg font-semibold">
              No tasks found
            </h2>

            <p className="mt-2 text-sm text-slate-400">
              Create a task or change the selected
              filters.
            </p>
          </section>
        )}

      {!isDataLoading &&
        !dataError &&
        tasks.length > 0 && (
          <section className="mt-8 overflow-hidden rounded-2xl border border-slate-800 bg-slate-900">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[1100px] text-left">
                <thead className="border-b border-slate-800">
                  <tr className="text-xs uppercase tracking-wider text-slate-500">
                    <th className="px-6 py-4 font-medium">
                      Task
                    </th>

                    <th className="px-6 py-4 font-medium">
                      Status
                    </th>

                    <th className="px-6 py-4 font-medium">
                      Priority
                    </th>

                    <th className="px-6 py-4 font-medium">
                      Due
                    </th>

                    <th className="px-6 py-4 font-medium">
                      Related to
                    </th>

                    <th className="px-6 py-4 font-medium">
                      Assigned to
                    </th>

                    <th className="px-6 py-4 text-right font-medium">
                      Actions
                    </th>
                  </tr>
                </thead>

                <tbody className="divide-y divide-slate-800">
                  {tasks.map((task) => {
                    const isOverdue =
                      task.due_at !== null &&
                      task.status !== "Completed" &&
                      new Date(task.due_at) <
                        new Date();

                    return (
                      <tr
                        className="transition hover:bg-slate-800/50"
                        key={task.id}
                      >
                        <td className="px-6 py-4">
                          <p className="font-medium text-white">
                            {task.title}
                          </p>

                          <p className="mt-1 text-xs text-slate-500">
                            Task #{task.id}
                          </p>
                        </td>

                        <td className="px-6 py-4">
                          <span
                            className={`rounded-full px-3 py-1 text-xs font-medium ${getStatusClassName(
                              task.status,
                            )}`}
                          >
                            {task.status}
                          </span>
                        </td>

                        <td
                          className={`px-6 py-4 text-sm font-medium ${getPriorityClassName(
                            task.priority,
                          )}`}
                        >
                          {task.priority}
                        </td>

                        <td
                          className={`px-6 py-4 text-sm ${
                            isOverdue
                              ? "font-medium text-red-300"
                              : "text-slate-300"
                          }`}
                        >
                          {task.due_at
                            ? new Date(
                                task.due_at,
                              ).toLocaleString()
                            : "—"}
                        </td>

                        <td className="px-6 py-4 text-sm text-slate-300">
                          {getRelatedRecord(task)}
                        </td>

                        <td className="px-6 py-4 text-sm text-slate-300">
                          {task.assigned_to_id === user.id
                            ? "You"
                            : `User #${task.assigned_to_id}`}
                        </td>

                        <td className="px-6 py-4">
                          <div className="flex justify-end gap-4">
                            <Link
                              className="text-sm font-semibold text-blue-400 transition hover:text-blue-300"
                              href={`/tasks/${task.id}/edit`}
                            >
                              Edit
                            </Link>

                            <button
                              className="text-sm font-semibold text-red-400 transition hover:text-red-300"
                              onClick={() => {
                                setDeleteError("");
                                setTaskToDelete(task);
                              }}
                              type="button"
                            >
                              Delete
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </section>
        )}

      {taskToDelete && (
        <DeleteTaskDialog
          errorMessage={deleteError}
          isDeleting={isDeleting}
          onCancel={() => {
            setDeleteError("");
            setTaskToDelete(null);
          }}
          onConfirm={handleDeleteTask}
          taskTitle={taskToDelete.title}
        />
      )}
    </AppShell>
  );
}