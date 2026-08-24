from decimal import Decimal

from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_companies: int
    total_contacts: int
    total_leads: int
    active_opportunities: int
    pipeline_value: Decimal
    leads_by_stage: dict[str, int]
    pending_tasks: int
    completed_tasks: int
    overdue_tasks: int
    upcoming_meetings: int