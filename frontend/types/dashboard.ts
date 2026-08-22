export type DashboardSummary = {
  total_companies: number;
  total_contacts: number;
  total_leads: number;
  pipeline_value: string;
  leads_by_stage: Record<string, number>;
  pending_tasks: number;
  overdue_tasks: number;
  upcoming_meetings: number;
};