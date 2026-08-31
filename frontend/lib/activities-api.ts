import { apiRequest } from "@/lib/api";
import type { ActivityLog } from "@/types/activity";

export function listActivityLogs(token: string): Promise<ActivityLog[]> {
  return apiRequest<ActivityLog[]>("/activities?limit=200", {
    token,
  });
}
