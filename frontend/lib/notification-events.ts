export const NOTIFICATIONS_UPDATED_EVENT = "mini-crm:notifications-updated";

export function dispatchNotificationsUpdated(): void {
  if (typeof window === "undefined") {
    return;
  }

  window.dispatchEvent(new Event(NOTIFICATIONS_UPDATED_EVENT));
}
