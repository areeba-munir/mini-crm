"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { ApiError } from "@/lib/api";
import { getAccessToken, removeAccessToken } from "@/lib/auth-storage";
import { NOTIFICATIONS_UPDATED_EVENT } from "@/lib/notification-events";
import { getNotificationUnreadCount } from "@/lib/notifications-api";

const REFRESH_INTERVAL_MS = 60_000;

export function useNotificationUnreadCount(): number {
  const router = useRouter();
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    let cancelled = false;
    let latestRequest = 0;

    async function refreshUnreadCount() {
      const requestNumber = ++latestRequest;
      const token = getAccessToken();

      if (!token) {
        if (!cancelled) {
          setUnreadCount(0);
        }

        return;
      }

      try {
        const result = await getNotificationUnreadCount(token);

        if (!cancelled && requestNumber === latestRequest) {
          setUnreadCount(result.unread_count);
        }
      } catch (error) {
        if (cancelled || requestNumber !== latestRequest) {
          return;
        }

        if (error instanceof ApiError && error.status === 401) {
          removeAccessToken();
          router.replace("/login");
        }
      }
    }

    function handleNotificationsUpdated() {
      void refreshUnreadCount();
    }

    function handleVisibilityChange() {
      if (document.visibilityState === "visible") {
        void refreshUnreadCount();
      }
    }

    void refreshUnreadCount();

    window.addEventListener(
      NOTIFICATIONS_UPDATED_EVENT,
      handleNotificationsUpdated,
    );

    document.addEventListener("visibilitychange", handleVisibilityChange);

    const intervalId = window.setInterval(
      () => void refreshUnreadCount(),
      REFRESH_INTERVAL_MS,
    );

    return () => {
      cancelled = true;
      latestRequest += 1;

      window.removeEventListener(
        NOTIFICATIONS_UPDATED_EVENT,
        handleNotificationsUpdated,
      );

      document.removeEventListener("visibilitychange", handleVisibilityChange);

      window.clearInterval(intervalId);
    };
  }, [router]);

  return unreadCount;
}
