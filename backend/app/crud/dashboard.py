from datetime import (
    datetime,
    timedelta,
    timezone,
)
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


PERCENT_QUANTUM = Decimal("0.01")
MONEY_QUANTUM = Decimal("0.01")

OPEN_STAGE_WEIGHTS = {
    LeadStage.NEW: Decimal("0.10"),
    LeadStage.CONTACTED: Decimal("0.30"),
    LeadStage.QUALIFIED: Decimal("0.60"),
}


def _percentage(
    numerator: int,
    denominator: int,
) -> Decimal:
    if denominator == 0:
        return Decimal("0.00")

    return (
        Decimal(numerator)
        * Decimal("100")
        / Decimal(denominator)
    ).quantize(PERCENT_QUANTUM)


def get_dashboard_summary(
    db: Session,
    current_time: datetime | None = None,
) -> DashboardSummary:
    if current_time is None:
        current_time = datetime.now(timezone.utc)

    next_seven_days = (
        current_time + timedelta(days=7)
    )
    last_thirty_days = (
        current_time - timedelta(days=30)
    )

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
            func.coalesce(
                func.sum(Lead.estimated_value),
                0,
            ),
        ).group_by(Lead.stage)
    ).all()

    leads_by_stage = {
        stage.value: 0
        for stage in LeadStage
    }

    pipeline_value_by_stage = {
        stage.value: Decimal("0.00")
        for stage in LeadStage
    }

    for stage, count, stage_value in stage_rows:
        leads_by_stage[stage.value] = count
        pipeline_value_by_stage[
            stage.value
        ] = Decimal(
            stage_value or 0
        ).quantize(MONEY_QUANTUM)

    open_stages = tuple(
        OPEN_STAGE_WEIGHTS
    )

    active_opportunities = sum(
        leads_by_stage[stage.value]
        for stage in open_stages
    )

    pipeline_value = sum(
        (
            pipeline_value_by_stage[
                stage.value
            ]
            for stage in open_stages
        ),
        Decimal("0.00"),
    ).quantize(MONEY_QUANTUM)

    weighted_pipeline_value = sum(
        (
            pipeline_value_by_stage[
                stage.value
            ]
            * OPEN_STAGE_WEIGHTS[stage]
            for stage in open_stages
        ),
        Decimal("0.00"),
    ).quantize(MONEY_QUANTUM)

    won_value = pipeline_value_by_stage[
        LeadStage.WON.value
    ]

    if active_opportunities == 0:
        average_open_deal_value = Decimal(
            "0.00"
        )
    else:
        average_open_deal_value = (
            pipeline_value
            / Decimal(active_opportunities)
        ).quantize(MONEY_QUANTUM)

    won_leads = leads_by_stage[
        LeadStage.WON.value
    ]
    lost_leads = leads_by_stage[
        LeadStage.LOST.value
    ]
    closed_leads = won_leads + lost_leads

    win_rate = _percentage(
        won_leads,
        closed_leads,
    )

    leads_created_last_30_days = db.scalar(
        select(func.count(Lead.id)).where(
            Lead.created_at >= last_thirty_days
        )
    ) or 0

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

    total_tasks = (
        pending_tasks + completed_tasks
    )

    task_completion_rate = _percentage(
        completed_tasks,
        total_tasks,
    )

    overdue_tasks = db.scalar(
        select(func.count(Task.id)).where(
            Task.status != TaskStatus.COMPLETED,
            Task.due_at.is_not(None),
            Task.due_at < current_time,
        )
    ) or 0

    tasks_due_next_7_days = db.scalar(
        select(func.count(Task.id)).where(
            Task.status != TaskStatus.COMPLETED,
            Task.due_at.is_not(None),
            Task.due_at >= current_time,
            Task.due_at <= next_seven_days,
        )
    ) or 0

    upcoming_meetings = db.scalar(
        select(func.count(Meeting.id)).where(
            Meeting.status
            == MeetingStatus.SCHEDULED,
            Meeting.starts_at >= current_time,
        )
    ) or 0

    meetings_next_7_days = db.scalar(
        select(func.count(Meeting.id)).where(
            Meeting.status
            == MeetingStatus.SCHEDULED,
            Meeting.starts_at >= current_time,
            Meeting.starts_at <= next_seven_days,
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
        weighted_pipeline_value=(
            weighted_pipeline_value
        ),
        won_value=won_value,
        average_open_deal_value=(
            average_open_deal_value
        ),
        pipeline_value_by_stage=(
            pipeline_value_by_stage
        ),
        leads_by_stage=leads_by_stage,
        leads_created_last_30_days=(
            leads_created_last_30_days
        ),
        win_rate=win_rate,
        pending_tasks=pending_tasks,
        completed_tasks=completed_tasks,
        overdue_tasks=overdue_tasks,
        tasks_due_next_7_days=(
            tasks_due_next_7_days
        ),
        task_completion_rate=(
            task_completion_rate
        ),
        upcoming_meetings=upcoming_meetings,
        meetings_next_7_days=(
            meetings_next_7_days
        ),
    )