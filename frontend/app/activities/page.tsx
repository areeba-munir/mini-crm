"use client";

import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { AppShell } from "@/components/layout/app-shell";
import { useAuthenticatedUser } from "@/hooks/use-authenticated-user";
import { ApiError } from "@/lib/api";
import { removeAccessToken } from "@/lib/auth-storage";
import { listActivityLogs } from "@/lib/activities-api";
import type {
  ActivityAction,
  ActivityActor,
  ActivityLog,
} from "@/types/activity";

type ActionFilter = "" | ActivityAction;

function getActionClasses(action: ActivityAction): string {
  if (action === "Created") {
    return "bg-emerald-500/10 text-emerald-300";
  }

  if (action === "Deleted") {
    return "bg-red-500/10 text-red-300";
  }

  return "bg-blue-500/10 text-blue-300";
}

function getChangedFields(activity: ActivityLog): string[] {
  const fields = activity.details?.fields;

  if (!Array.isArray(fields)) {
    return [];
  }

  return fields.filter((field): field is string => typeof field === "string");
}

export default function ActivitiesPage() {
  const router = useRouter();

  const {
    user,
    token,
    isLoading: isAuthenticationLoading,
    errorMessage: authenticationError,
  } = useAuthenticatedUser();

  const [activities, setActivities] = useState<ActivityLog[]>([]);
  const [isActivitiesLoading, setIsActivitiesLoading] = useState(true);
  const [activitiesError, setActivitiesError] = useState("");

  const [actionFilter, setActionFilter] = useState<ActionFilter>("");
  const [entityFilter, setEntityFilter] = useState("");
  const [actorFilter, setActorFilter] = useState("");

  const canViewActivities = user?.role === "Admin" || user?.role === "Manager";

  useEffect(() => {
    if (!token || !canViewActivities) {
      return;
    }

    let cancelled = false;

    async function loadActivities(accessToken: string) {
      try {
        const activityRecords = await listActivityLogs(accessToken);

        if (!cancelled) {
          setActivities(activityRecords);
          setIsActivitiesLoading(false);
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

        setActivitiesError(
          error instanceof ApiError
            ? error.message
            : "Unable to load activity history.",
        );
        setIsActivitiesLoading(false);
      }
    }

    void loadActivities(token);

    return () => {
      cancelled = true;
    };
  }, [canViewActivities, router, token]);

  const entityTypes = useMemo(
    () =>
      Array.from(
        new Set(activities.map((activity) => activity.entity_type)),
      ).sort(),
    [activities],
  );

  const actors = useMemo(() => {
    const actorsById = new Map<number, ActivityActor>();

    for (const activity of activities) {
      if (activity.actor) {
        actorsById.set(activity.actor.id, activity.actor);
      }
    }

    return Array.from(actorsById.values()).sort((firstActor, secondActor) =>
      firstActor.full_name.localeCompare(secondActor.full_name),
    );
  }, [activities]);

  const filteredActivities = useMemo(
    () =>
      activities.filter((activity) => {
        if (actionFilter && activity.action !== actionFilter) {
          return false;
        }

        if (entityFilter && activity.entity_type !== entityFilter) {
          return false;
        }

        if (actorFilter && activity.actor_id !== Number(actorFilter)) {
          return false;
        }

        return true;
      }),
    [actionFilter, activities, actorFilter, entityFilter],
  );

  if (isAuthenticationLoading || !user || !token) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-950 px-4">
        <p
          className={`text-sm ${
            authenticationError ? "text-red-300" : "text-slate-400"
          }`}
        >
          {authenticationError || "Loading activity history..."}
        </p>
      </main>
    );
  }

  if (!canViewActivities) {
    return (
      <AppShell user={user}>
        <section className="rounded-2xl border border-red-500/30 bg-red-500/10 p-6">
          <h1 className="text-lg font-semibold text-red-300">
            Manager access required
          </h1>

          <p className="mt-2 text-sm text-red-200">
            You do not have permission to view the CRM activity history.
          </p>
        </section>
      </AppShell>
    );
  }

  return (
    <AppShell user={user}>
      <section>
        <p className="text-sm font-medium text-blue-400">Audit</p>

        <h1 className="mt-1 text-3xl font-bold">Activity history</h1>

        <p className="mt-2 text-sm text-slate-400">
          Review recorded changes across CRM records.
        </p>
      </section>

      <section className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <label className="text-sm text-slate-300">
          <span className="mb-2 block">Action</span>

          <select
            className="w-full rounded-lg border border-slate-700 bg-slate-900 px-4 py-3 text-white outline-none focus:border-blue-500"
            onChange={(event) =>
              setActionFilter(event.target.value as ActionFilter)
            }
            value={actionFilter}
          >
            <option value="">All actions</option>
            <option value="Created">Created</option>
            <option value="Updated">Updated</option>
            <option value="Deleted">Deleted</option>
          </select>
        </label>

        <label className="text-sm text-slate-300">
          <span className="mb-2 block">Record type</span>

          <select
            className="w-full rounded-lg border border-slate-700 bg-slate-900 px-4 py-3 text-white outline-none focus:border-blue-500"
            onChange={(event) => setEntityFilter(event.target.value)}
            value={entityFilter}
          >
            <option value="">All records</option>

            {entityTypes.map((entityType) => (
              <option key={entityType} value={entityType}>
                {entityType}
              </option>
            ))}
          </select>
        </label>

        <label className="text-sm text-slate-300">
          <span className="mb-2 block">User</span>

          <select
            className="w-full rounded-lg border border-slate-700 bg-slate-900 px-4 py-3 text-white outline-none focus:border-blue-500"
            onChange={(event) => setActorFilter(event.target.value)}
            value={actorFilter}
          >
            <option value="">All users</option>

            {actors.map((actor) => (
              <option key={actor.id} value={actor.id}>
                {actor.full_name}
              </option>
            ))}
          </select>
        </label>

        <article className="rounded-lg border border-slate-800 bg-slate-900 px-4 py-3">
          <p className="text-sm text-slate-400">Matching activities</p>

          <p className="mt-2 text-2xl font-bold">{filteredActivities.length}</p>
        </article>
      </section>

      {isActivitiesLoading && (
        <section className="mt-8 rounded-2xl border border-slate-800 bg-slate-900 p-8 text-center">
          <p className="text-sm text-slate-400">Loading activity records...</p>
        </section>
      )}

      {!isActivitiesLoading && activitiesError && (
        <section className="mt-8 rounded-2xl border border-red-500/30 bg-red-500/10 p-6">
          <h2 className="font-semibold text-red-300">
            Activity history unavailable
          </h2>

          <p className="mt-2 text-sm text-red-200">{activitiesError}</p>
        </section>
      )}

      {!isActivitiesLoading &&
        !activitiesError &&
        filteredActivities.length === 0 && (
          <section className="mt-8 rounded-2xl border border-dashed border-slate-700 bg-slate-900 p-10 text-center">
            <h2 className="text-lg font-semibold">No activities found</h2>

            <p className="mt-2 text-sm text-slate-400">
              Change the filters or update a CRM record to generate activity.
            </p>
          </section>
        )}

      {!isActivitiesLoading &&
        !activitiesError &&
        filteredActivities.length > 0 && (
          <section className="mt-8 space-y-4">
            {filteredActivities.map((activity) => {
              const changedFields = getChangedFields(activity);

              return (
                <article
                  className="rounded-2xl border border-slate-800 bg-slate-900 p-5 sm:p-6"
                  key={activity.id}
                >
                  <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <span
                          className={`rounded-full px-2.5 py-1 text-xs font-semibold ${getActionClasses(
                            activity.action,
                          )}`}
                        >
                          {activity.action}
                        </span>

                        <span className="text-sm font-medium text-white">
                          {activity.entity_type}
                          {activity.entity_id !== null
                            ? ` #${activity.entity_id}`
                            : ""}
                        </span>
                      </div>

                      <p className="mt-3 text-sm text-slate-300">
                        {activity.description}
                      </p>

                      {changedFields.length > 0 && (
                        <p className="mt-2 text-xs text-slate-500">
                          Fields: {changedFields.join(", ")}
                        </p>
                      )}
                    </div>

                    <div className="shrink-0 text-left sm:text-right">
                      <p className="text-sm text-slate-300">
                        {activity.actor?.full_name ?? "Deleted user"}
                      </p>

                      <p className="mt-1 text-xs text-slate-500">
                        {new Date(activity.created_at).toLocaleString()}
                      </p>
                    </div>
                  </div>
                </article>
              );
            })}
          </section>
        )}
    </AppShell>
  );
}
