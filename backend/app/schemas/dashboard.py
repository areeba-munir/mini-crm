from decimal import Decimal

from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_companies: int
    total_contacts: int
    total_leads: int
    active_opportunities: int

    pipeline_value: Decimal
    weighted_pipeline_value: Decimal
    won_value: Decimal
    average_open_deal_value: Decimal
    pipeline_value_by_stage: dict[
        str,
        Decimal,
    ]

    leads_by_stage: dict[str, int]
    leads_created_last_30_days: int
    win_rate: Decimal

    pending_tasks: int
    completed_tasks: int
    overdue_tasks: int
    tasks_due_next_7_days: int
    task_completion_rate: Decimal

    upcoming_meetings: int
    meetings_next_7_days: int