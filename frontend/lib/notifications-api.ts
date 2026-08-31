import { apiRequest } from "@/lib/api";
import type {
  CrmNotification,
  NotificationUnreadCount,
} from "@/types/notification";

type ListNotificationsOptions = {
  unreadOnly?: boolean;
  offset?: number;
  limit?: number;
};

export function listNotifications(
  token: string,
  options: ListNotificationsOptions = {},
): Promise<CrmNotification[]> {
  const parameters = new URLSearchParams();

  if (options.unreadOnly) {
    parameters.set("unread_only", "true");
  }

  if (options.offset !== undefined) {
    parameters.set("offset", String(options.offset));
  }

  if (options.limit !== undefined) {
    parameters.set("limit", String(options.limit));
  }

  const query = parameters.toString();

  return apiRequest<CrmNotification[]>(
    `/notifications${query ? `?${query}` : ""}`,
    {
      token,
    },
  );
}

export function getNotificationUnreadCount(
  token: string,
): Promise<NotificationUnreadCount> {
  return apiRequest<NotificationUnreadCount>("/notifications/unread-count", {
    token,
  });
}

export function markNotificationRead(
  token: string,
  notificationId: number,
): Promise<CrmNotification> {
  return apiRequest<CrmNotification>(`/notifications/${notificationId}/read`, {
    method: "PATCH",
    token,
  });
}

export function markAllNotificationsRead(
  token: string,
): Promise<NotificationUnreadCount> {
  return apiRequest<NotificationUnreadCount>("/notifications/read-all", {
    method: "PATCH",
    token,
  });
}
