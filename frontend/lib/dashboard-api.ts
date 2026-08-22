import { apiRequest } from "@/lib/api";
import type { DashboardSummary } from "@/types/dashboard";

export function getDashboardSummary(
  token: string,
): Promise<DashboardSummary> {
  return apiRequest<DashboardSummary>(
    "/dashboard/summary",
    {
      token,
    },
  );
}