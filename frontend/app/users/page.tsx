"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/layout/app-shell";
import { useToast } from "@/components/ui/toast-provider";
import { useAuthenticatedUser } from "@/hooks/use-authenticated-user";
import { ApiError } from "@/lib/api";
import { removeAccessToken } from "@/lib/auth-storage";
import { listUsers, updateUserAdministration } from "@/lib/users-api";
import type { User, UserAdminUpdateInput, UserRole } from "@/types/auth";

const userRoles: UserRole[] = ["Admin", "Manager", "Member"];

function getRoleClasses(role: UserRole): string {
  if (role === "Admin") {
    return "bg-purple-500/10 text-purple-300";
  }

  if (role === "Manager") {
    return "bg-blue-500/10 text-blue-300";
  }

  return "bg-slate-700 text-slate-300";
}

export default function UsersPage() {
  const router = useRouter();
  const { showToast } = useToast();

  const {
    user,
    token,
    isLoading: isAuthenticationLoading,
    errorMessage: authenticationError,
  } = useAuthenticatedUser();

  const [users, setUsers] = useState<User[]>([]);
  const [isUsersLoading, setIsUsersLoading] = useState(true);
  const [usersError, setUsersError] = useState("");
  const [updatingUserId, setUpdatingUserId] = useState<number | null>(null);

  const isAdmin = user?.role === "Admin";

  useEffect(() => {
    if (!token || !isAdmin) {
      return;
    }

    let cancelled = false;

    async function loadUsers(accessToken: string) {
      try {
        const userRecords = await listUsers(accessToken);

        if (!cancelled) {
          setUsers(userRecords);
          setIsUsersLoading(false);
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

        setUsersError(
          error instanceof ApiError ? error.message : "Unable to load users.",
        );
        setIsUsersLoading(false);
      }
    }

    void loadUsers(token);

    return () => {
      cancelled = true;
    };
  }, [isAdmin, router, token]);

  async function updateManagedUser(
    managedUser: User,
    input: UserAdminUpdateInput,
    successMessage: string,
  ) {
    if (!token) {
      return;
    }

    setUpdatingUserId(managedUser.id);

    try {
      const updatedUser = await updateUserAdministration(
        managedUser.id,
        input,
        token,
      );

      setUsers((currentUsers) =>
        currentUsers.map((currentUser) =>
          currentUser.id === updatedUser.id ? updatedUser : currentUser,
        ),
      );

      showToast(successMessage, "success");
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        removeAccessToken();
        router.replace("/login");
        return;
      }

      showToast(
        error instanceof ApiError
          ? error.message
          : "Unable to update the user.",
        "error",
      );
    } finally {
      setUpdatingUserId(null);
    }
  }

  function handleRoleChange(managedUser: User, role: UserRole) {
    void updateManagedUser(
      managedUser,
      {
        role,
      },
      `${managedUser.full_name}'s role was updated.`,
    );
  }

  function handleStatusChange(managedUser: User) {
    const nextStatus = !managedUser.is_active;

    void updateManagedUser(
      managedUser,
      {
        is_active: nextStatus,
      },
      `${managedUser.full_name} was ${
        nextStatus ? "activated" : "deactivated"
      }.`,
    );
  }

  if (isAuthenticationLoading || !user || !token) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-950 px-4">
        <p
          className={`text-sm ${
            authenticationError ? "text-red-300" : "text-slate-400"
          }`}
        >
          {authenticationError || "Loading user management..."}
        </p>
      </main>
    );
  }

  if (!isAdmin) {
    return (
      <AppShell user={user}>
        <section className="rounded-2xl border border-red-500/30 bg-red-500/10 p-6">
          <h1 className="text-lg font-semibold text-red-300">
            Administrator access required
          </h1>

          <p className="mt-2 text-sm text-red-200">
            You do not have permission to manage users or roles.
          </p>
        </section>
      </AppShell>
    );
  }

  return (
    <AppShell user={user}>
      <section>
        <p className="text-sm font-medium text-blue-400">Administration</p>

        <h1 className="mt-1 text-3xl font-bold">Users</h1>

        <p className="mt-2 text-sm text-slate-400">
          Manage account access and CRM roles.
        </p>
      </section>

      <section className="mt-6 grid gap-4 sm:grid-cols-3">
        <article className="rounded-xl border border-slate-800 bg-slate-900 p-5">
          <p className="text-sm text-slate-400">Total users</p>

          <p className="mt-2 text-2xl font-bold">{users.length}</p>
        </article>

        <article className="rounded-xl border border-slate-800 bg-slate-900 p-5">
          <p className="text-sm text-slate-400">Active users</p>

          <p className="mt-2 text-2xl font-bold">
            {users.filter((managedUser) => managedUser.is_active).length}
          </p>
        </article>

        <article className="rounded-xl border border-slate-800 bg-slate-900 p-5">
          <p className="text-sm text-slate-400">Administrators</p>

          <p className="mt-2 text-2xl font-bold">
            {users.filter((managedUser) => managedUser.role === "Admin").length}
          </p>
        </article>
      </section>

      {isUsersLoading && (
        <section className="mt-8 rounded-2xl border border-slate-800 bg-slate-900 p-8 text-center">
          <p className="text-sm text-slate-400">Loading user accounts...</p>
        </section>
      )}

      {!isUsersLoading && usersError && (
        <section className="mt-8 rounded-2xl border border-red-500/30 bg-red-500/10 p-6">
          <h2 className="font-semibold text-red-300">Users unavailable</h2>

          <p className="mt-2 text-sm text-red-200">{usersError}</p>
        </section>
      )}

      {!isUsersLoading && !usersError && users.length > 0 && (
        <>
          <section className="mt-8 grid gap-4 md:hidden">
            {users.map((managedUser) => {
              const isCurrentUser = managedUser.id === user.id;
              const isUpdating = updatingUserId === managedUser.id;

              return (
                <article
                  className="rounded-2xl border border-slate-800 bg-slate-900 p-5"
                  key={managedUser.id}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <h2 className="truncate font-semibold">
                        {managedUser.full_name}
                      </h2>

                      <p className="mt-1 truncate text-sm text-slate-400">
                        {managedUser.email}
                      </p>
                    </div>

                    <span
                      className={`rounded-full px-2.5 py-1 text-xs font-medium ${getRoleClasses(
                        managedUser.role,
                      )}`}
                    >
                      {managedUser.role}
                    </span>
                  </div>

                  <div className="mt-5">
                    <label
                      className="text-sm text-slate-300"
                      htmlFor={`mobile-role-${managedUser.id}`}
                    >
                      Role
                    </label>

                    <select
                      className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-blue-500 disabled:opacity-60"
                      disabled={isCurrentUser || isUpdating}
                      id={`mobile-role-${managedUser.id}`}
                      onChange={(event) =>
                        handleRoleChange(
                          managedUser,
                          event.target.value as UserRole,
                        )
                      }
                      value={managedUser.role}
                    >
                      {userRoles.map((role) => (
                        <option key={role} value={role}>
                          {role}
                        </option>
                      ))}
                    </select>
                  </div>

                  <button
                    className={`mt-4 w-full rounded-lg border px-4 py-2 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-50 ${
                      managedUser.is_active
                        ? "border-red-500/40 text-red-300 hover:bg-red-500/10"
                        : "border-emerald-500/40 text-emerald-300 hover:bg-emerald-500/10"
                    }`}
                    disabled={isCurrentUser || isUpdating}
                    onClick={() => handleStatusChange(managedUser)}
                    type="button"
                  >
                    {isUpdating
                      ? "Updating..."
                      : managedUser.is_active
                        ? "Deactivate"
                        : "Activate"}
                  </button>
                </article>
              );
            })}
          </section>

          <section className="mt-8 hidden overflow-hidden rounded-2xl border border-slate-800 bg-slate-900 md:block">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[800px] text-left">
                <thead className="border-b border-slate-800">
                  <tr className="text-xs uppercase tracking-wider text-slate-500">
                    <th className="px-6 py-4 font-medium">User</th>
                    <th className="px-6 py-4 font-medium">Role</th>
                    <th className="px-6 py-4 font-medium">Status</th>
                    <th className="px-6 py-4 text-right font-medium">Action</th>
                  </tr>
                </thead>

                <tbody className="divide-y divide-slate-800">
                  {users.map((managedUser) => {
                    const isCurrentUser = managedUser.id === user.id;
                    const isUpdating = updatingUserId === managedUser.id;

                    return (
                      <tr key={managedUser.id}>
                        <td className="px-6 py-4">
                          <p className="font-medium">
                            {managedUser.full_name}
                            {isCurrentUser && (
                              <span className="ml-2 text-xs text-blue-400">
                                You
                              </span>
                            )}
                          </p>

                          <p className="mt-1 text-sm text-slate-500">
                            {managedUser.email}
                          </p>
                        </td>

                        <td className="px-6 py-4">
                          <select
                            aria-label={`Role for ${managedUser.full_name}`}
                            className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-blue-500 disabled:opacity-60"
                            disabled={isCurrentUser || isUpdating}
                            onChange={(event) =>
                              handleRoleChange(
                                managedUser,
                                event.target.value as UserRole,
                              )
                            }
                            value={managedUser.role}
                          >
                            {userRoles.map((role) => (
                              <option key={role} value={role}>
                                {role}
                              </option>
                            ))}
                          </select>
                        </td>

                        <td className="px-6 py-4">
                          <span
                            className={`rounded-full px-2.5 py-1 text-xs font-medium ${
                              managedUser.is_active
                                ? "bg-emerald-500/10 text-emerald-300"
                                : "bg-red-500/10 text-red-300"
                            }`}
                          >
                            {managedUser.is_active ? "Active" : "Inactive"}
                          </span>
                        </td>

                        <td className="px-6 py-4 text-right">
                          <button
                            className={`text-sm font-semibold transition disabled:cursor-not-allowed disabled:text-slate-600 ${
                              managedUser.is_active
                                ? "text-red-400 hover:text-red-300"
                                : "text-emerald-400 hover:text-emerald-300"
                            }`}
                            disabled={isCurrentUser || isUpdating}
                            onClick={() => handleStatusChange(managedUser)}
                            type="button"
                          >
                            {isUpdating
                              ? "Updating..."
                              : managedUser.is_active
                                ? "Deactivate"
                                : "Activate"}
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </AppShell>
  );
}
