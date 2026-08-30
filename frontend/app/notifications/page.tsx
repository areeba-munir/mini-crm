"use client";

import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { AppShell } from "@/components/layout/app-shell";
import { useAuthenticatedUser } from "@/hooks/use-authenticated-user";
import { ApiError } from "@/lib/api";
import { removeAccessToken } from "@/lib/auth-storage";
import { dispatchNotificationsUpdated } from "@/lib/notification-events";
import {
  listNotifications,
  markAllNotificationsRead,
  markNotificationRead,
} from "@/lib/notifications-api";
import type { CrmNotification, NotificationType } from "@/types/notification";

type NotificationFilter = "all" | "unread";

function getNotificationTypeClasses(
  notificationType: NotificationType,
): string {
  if (notificationType === "Task Assigned") {
    return "bg-blue-500/10 text-blue-300";
  }

  if (notificationType === "Meeting Invitation") {
    return "bg-violet-500/10 text-violet-300";
  }

  return "bg-slate-700 text-slate-300";
}

function getSafeNotificationLink(link: string | null): string | null {
  if (!link || !link.startsWith("/") || link.startsWith("//")) {
    return null;
  }

  return link;
}

export default function NotificationsPage() {
  const router = useRouter();

  const {
    user,
    token,
    isLoading: isAuthenticationLoading,
    errorMessage: authenticationError,
  } = useAuthenticatedUser();

  const [notifications, setNotifications] = useState<CrmNotification[]>([]);
  const [isNotificationsLoading, setIsNotificationsLoading] = useState(true);
  const [notificationsError, setNotificationsError] = useState("");
  const [actionError, setActionError] = useState("");
  const [filter, setFilter] = useState<NotificationFilter>("all");
  const [pendingNotificationIds, setPendingNotificationIds] = useState<
    Set<number>
  >(new Set());
  const [isMarkingAll, setIsMarkingAll] = useState(false);

  useEffect(() => {
    if (!token) {
      return;
    }

    let cancelled = false;

    async function loadNotificationRecords(accessToken: string) {
      try {
        const records = await listNotifications(accessToken, {
          limit: 200,
        });

        if (!cancelled) {
          setNotifications(records);
          setNotificationsError("");
          setIsNotificationsLoading(false);
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

        setNotificationsError(
          error instanceof ApiError
            ? error.message
            : "Unable to load notifications.",
        );
        setIsNotificationsLoading(false);
      }
    }

    void loadNotificationRecords(token);

    return () => {
      cancelled = true;
    };
  }, [router, token]);

  const unreadCount = useMemo(
    () => notifications.filter((notification) => !notification.is_read).length,
    [notifications],
  );

  const filteredNotifications = useMemo(() => {
    if (filter === "unread") {
      return notifications.filter((notification) => !notification.is_read);
    }

    return notifications;
  }, [filter, notifications]);

  async function markAsRead(notification: CrmNotification): Promise<boolean> {
    if (notification.is_read) {
      return true;
    }

    if (!token) {
      return false;
    }

    setActionError("");

    setPendingNotificationIds((currentIds) => {
      const nextIds = new Set(currentIds);
      nextIds.add(notification.id);
      return nextIds;
    });

    try {
      const updatedNotification = await markNotificationRead(
        token,
        notification.id,
      );

      setNotifications((currentNotifications) =>
        currentNotifications.map((currentNotification) =>
          currentNotification.id === updatedNotification.id
            ? updatedNotification
            : currentNotification,
        ),
      );

      dispatchNotificationsUpdated();
      return true;
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        removeAccessToken();
        router.replace("/login");
        return false;
      }

      setActionError(
        error instanceof ApiError
          ? error.message
          : "Unable to mark the notification as read.",
      );

      return false;
    } finally {
      setPendingNotificationIds((currentIds) => {
        const nextIds = new Set(currentIds);
        nextIds.delete(notification.id);
        return nextIds;
      });
    }
  }

  async function handleOpenNotification(
    notification: CrmNotification,
    link: string,
  ) {
    const wasMarked = await markAsRead(notification);

    if (wasMarked) {
      router.push(link);
    }
  }

  async function handleMarkAllRead() {
    if (!token || unreadCount === 0) {
      return;
    }

    setActionError("");
    setIsMarkingAll(true);

    try {
      await markAllNotificationsRead(token);

      const readAt = new Date().toISOString();

      setNotifications((currentNotifications) =>
        currentNotifications.map((notification) =>
          notification.is_read
            ? notification
            : {
                ...notification,
                is_read: true,
                read_at: readAt,
              },
        ),
      );

      dispatchNotificationsUpdated();
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        removeAccessToken();
        router.replace("/login");
        return;
      }

      setActionError(
        error instanceof ApiError
          ? error.message
          : "Unable to mark all notifications as read.",
      );
    } finally {
      setIsMarkingAll(false);
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
          {authenticationError || "Loading notifications..."}
        </p>
      </main>
    );
  }

  return (
    <AppShell user={user}>
      <section className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-sm font-medium text-blue-400">Inbox</p>

          <h1 className="mt-1 text-3xl font-bold">Notifications</h1>

          <p className="mt-2 text-sm text-slate-400">
            Review task assignments, meeting invitations, and system updates.
          </p>
        </div>

        <button
          className="rounded-lg border border-slate-700 px-4 py-2.5 text-sm font-medium text-slate-200 transition hover:border-slate-500 hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
          disabled={unreadCount === 0 || isMarkingAll}
          onClick={() => void handleMarkAllRead()}
          type="button"
        >
          {isMarkingAll ? "Marking all..." : "Mark all as read"}
        </button>
      </section>

      <section className="mt-6 flex flex-col gap-4 rounded-2xl border border-slate-800 bg-slate-900 p-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex gap-2">
          <button
            aria-pressed={filter === "all"}
            className={`rounded-lg px-4 py-2 text-sm font-medium transition ${
              filter === "all"
                ? "bg-blue-600 text-white"
                : "text-slate-400 hover:bg-slate-800 hover:text-white"
            }`}
            onClick={() => setFilter("all")}
            type="button"
          >
            All ({notifications.length})
          </button>

          <button
            aria-pressed={filter === "unread"}
            className={`rounded-lg px-4 py-2 text-sm font-medium transition ${
              filter === "unread"
                ? "bg-blue-600 text-white"
                : "text-slate-400 hover:bg-slate-800 hover:text-white"
            }`}
            onClick={() => setFilter("unread")}
            type="button"
          >
            Unread ({unreadCount})
          </button>
        </div>

        <p className="text-sm text-slate-400">
          {unreadCount === 1
            ? "1 unread notification"
            : `${unreadCount} unread notifications`}
        </p>
      </section>

      {actionError && (
        <section className="mt-5 rounded-xl border border-red-500/30 bg-red-500/10 p-4">
          <p className="text-sm text-red-200">{actionError}</p>
        </section>
      )}

      {isNotificationsLoading && (
        <section className="mt-8 rounded-2xl border border-slate-800 bg-slate-900 p-8 text-center">
          <p className="text-sm text-slate-400">
            Loading notification records...
          </p>
        </section>
      )}

      {!isNotificationsLoading && notificationsError && (
        <section className="mt-8 rounded-2xl border border-red-500/30 bg-red-500/10 p-6">
          <h2 className="font-semibold text-red-300">
            Notifications unavailable
          </h2>

          <p className="mt-2 text-sm text-red-200">{notificationsError}</p>
        </section>
      )}

      {!isNotificationsLoading &&
        !notificationsError &&
        filteredNotifications.length === 0 && (
          <section className="mt-8 rounded-2xl border border-dashed border-slate-700 bg-slate-900 p-10 text-center">
            <h2 className="text-lg font-semibold">
              {filter === "unread"
                ? "You are all caught up"
                : "No notifications yet"}
            </h2>

            <p className="mt-2 text-sm text-slate-400">
              {filter === "unread"
                ? "There are no unread notifications."
                : "New assignments and meeting invitations will appear here."}
            </p>
          </section>
        )}

      {!isNotificationsLoading &&
        !notificationsError &&
        filteredNotifications.length > 0 && (
          <section className="mt-8 space-y-4">
            {filteredNotifications.map((notification) => {
              const safeLink = getSafeNotificationLink(notification.link);

              const isPending = pendingNotificationIds.has(notification.id);

              return (
                <article
                  className={`rounded-2xl border p-5 transition sm:p-6 ${
                    notification.is_read
                      ? "border-slate-800 bg-slate-900"
                      : "border-blue-500/30 bg-blue-500/5"
                  }`}
                  key={notification.id}
                >
                  <div className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <span
                          className={`rounded-full px-2.5 py-1 text-xs font-semibold ${getNotificationTypeClasses(
                            notification.notification_type,
                          )}`}
                        >
                          {notification.notification_type}
                        </span>

                        {!notification.is_read && (
                          <span className="rounded-full bg-red-500/10 px-2.5 py-1 text-xs font-semibold text-red-300">
                            Unread
                          </span>
                        )}
                      </div>

                      <h2 className="mt-3 text-lg font-semibold text-white">
                        {notification.title}
                      </h2>

                      <p className="mt-2 text-sm leading-6 text-slate-300">
                        {notification.message}
                      </p>

                      <p className="mt-3 text-xs text-slate-500">
                        {new Date(notification.created_at).toLocaleString()}
                      </p>
                    </div>

                    <div className="flex shrink-0 flex-wrap gap-2">
                      {!notification.is_read && (
                        <button
                          className="rounded-lg border border-slate-700 px-3 py-2 text-sm font-medium text-slate-300 transition hover:border-slate-500 hover:bg-slate-800 hover:text-white disabled:cursor-not-allowed disabled:opacity-50"
                          disabled={isPending || isMarkingAll}
                          onClick={() => void markAsRead(notification)}
                          type="button"
                        >
                          {isPending ? "Marking..." : "Mark as read"}
                        </button>
                      )}

                      {safeLink && (
                        <button
                          className="rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
                          disabled={isPending || isMarkingAll}
                          onClick={() =>
                            void handleOpenNotification(notification, safeLink)
                          }
                          type="button"
                        >
                          Open
                        </button>
                      )}
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
