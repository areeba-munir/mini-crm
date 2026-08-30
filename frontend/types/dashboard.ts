export type DashboardSummary = {
  total_companies: number;
  total_contacts: number;
  total_leads: number;
  active_opportunities: number;

  pipeline_value: string;
  weighted_pipeline_value: string;
  won_value: string;
  average_open_deal_value: string;
  pipeline_value_by_stage: Record<string, string>;

  leads_by_stage: Record<string, number>;
  leads_created_last_30_days: number;
  win_rate: string;

  pending_tasks: number;
  completed_tasks: number;
  overdue_tasks: number;
  tasks_due_next_7_days: number;
  task_completion_rate: string;

  upcoming_meetings: number;
  meetings_next_7_days: number;
};
