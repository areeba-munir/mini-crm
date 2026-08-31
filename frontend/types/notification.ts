export type NotificationType =
  "Task Assigned" | "Meeting Invitation" | "System";

export type CrmNotification = {
  id: number;
  recipient_id: number;
  notification_type: NotificationType;
  title: string;
  message: string;
  link: string | null;
  is_read: boolean;
  read_at: string | null;
  created_at: string;
};

export type NotificationUnreadCount = {
  unread_count: number;
};
