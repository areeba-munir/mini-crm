from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.contact import Contact
from app.models.lead import Lead, LeadStage
from app.models.meeting import (
    Meeting,
    MeetingStatus,
)
from app.models.task import Task, TaskStatus
from app.schemas.dashboard import DashboardSummary


def get_dashboard_summary(
    db: Session,
    current_time: datetime | None = None,
) -> DashboardSummary:
    if current_time is None:
        current_time = datetime.now(timezone.utc)

    total_companies = db.scalar(
        select(func.count(Company.id))
    ) or 0

    total_contacts = db.scalar(
        select(func.count(Contact.id))
    ) or 0

    total_leads = db.scalar(
        select(func.count(Lead.id))
    ) or 0

    stage_rows = db.execute(
        select(
            Lead.stage,
            func.count(Lead.id),
        ).group_by(Lead.stage)
    ).all()

    leads_by_stage = {
        stage.value: 0
        for stage in LeadStage
    }

    for stage, count in stage_rows:
        leads_by_stage[stage.value] = count

    open_stages = (
        LeadStage.NEW,
        LeadStage.CONTACTED,
        LeadStage.QUALIFIED,
    )

    active_opportunities = sum(
        leads_by_stage[stage.value]
        for stage in open_stages
    )

    pipeline_value_result = db.scalar(
        select(
            func.coalesce(
                func.sum(Lead.estimated_value),
                0,
            )
        ).where(
            Lead.stage.in_(open_stages)
        )
    )

    pipeline_value = Decimal(
        pipeline_value_result or 0
    )

    pending_tasks = db.scalar(
        select(func.count(Task.id)).where(
            Task.status != TaskStatus.COMPLETED
        )
    ) or 0

    completed_tasks = db.scalar(
        select(func.count(Task.id)).where(
            Task.status == TaskStatus.COMPLETED
        )
    ) or 0

    overdue_tasks = db.scalar(
        select(func.count(Task.id)).where(
            Task.status != TaskStatus.COMPLETED,
            Task.due_at.is_not(None),
            Task.due_at < current_time,
        )
    ) or 0

    upcoming_meetings = db.scalar(
        select(func.count(Meeting.id)).where(
            Meeting.status
            == MeetingStatus.SCHEDULED,
            Meeting.starts_at >= current_time,
        )
    ) or 0

    return DashboardSummary(
        total_companies=total_companies,
        total_contacts=total_contacts,
        total_leads=total_leads,
        active_opportunities=(
            active_opportunities
        ),
        pipeline_value=pipeline_value,
        leads_by_stage=leads_by_stage,
        pending_tasks=pending_tasks,
        completed_tasks=completed_tasks,
        overdue_tasks=overdue_tasks,
        upcoming_meetings=upcoming_meetings,
    )