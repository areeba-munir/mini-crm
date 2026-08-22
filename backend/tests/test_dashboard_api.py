from datetime import (
    datetime,
    timedelta,
    timezone,
)
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.meeting import (
    Meeting,
    MeetingStatus,
)


def test_empty_dashboard_summary(
    authenticated_client: TestClient,
) -> None:
    response = authenticated_client.get(
        "/api/v1/dashboard/summary"
    )

    assert response.status_code == 200

    summary = response.json()

    assert summary["total_companies"] == 0
    assert summary["total_contacts"] == 0
    assert summary["total_leads"] == 0
    assert Decimal(summary["pipeline_value"]) == Decimal("0")
    assert summary["leads_by_stage"] == {
        "New": 0,
        "Contacted": 0,
        "Qualified": 0,
        "Won": 0,
        "Lost": 0,
    }
    assert summary["pending_tasks"] == 0
    assert summary["overdue_tasks"] == 0
    assert summary["upcoming_meetings"] == 0


def test_dashboard_calculates_crm_metrics(
    authenticated_client: TestClient,
    db_session: Session,
) -> None:
    now = datetime.now(timezone.utc)

    current_user = authenticated_client.get(
        "/api/v1/auth/me"
    ).json()

    company = authenticated_client.post(
        "/api/v1/companies",
        json={"name": "Dashboard Company"},
    ).json()

    authenticated_client.post(
        "/api/v1/contacts",
        json={
            "first_name": "Dashboard",
            "last_name": "Contact",
            "company_id": company["id"],
        },
    )

    lead_values = [
        ("New Lead", "New", "1000.00"),
        ("Contacted Lead", "Contacted", "500.00"),
        ("Qualified Lead", "Qualified", "2500.00"),
        ("Won Lead", "Won", "9000.00"),
        ("Lost Lead", "Lost", "7000.00"),
    ]

    for title, stage, value in lead_values:
        authenticated_client.post(
            "/api/v1/leads",
            json={
                "title": title,
                "company_id": company["id"],
                "stage": stage,
                "estimated_value": value,
            },
        )

    authenticated_client.post(
        "/api/v1/tasks",
        json={
            "title": "Overdue pending task",
            "assigned_to_id": current_user["id"],
            "status": "Pending",
            "due_at": (
                now - timedelta(days=1)
            ).isoformat(),
        },
    )

    authenticated_client.post(
        "/api/v1/tasks",
        json={
            "title": "Future in-progress task",
            "assigned_to_id": current_user["id"],
            "status": "In Progress",
            "due_at": (
                now + timedelta(days=1)
            ).isoformat(),
        },
    )

    authenticated_client.post(
        "/api/v1/tasks",
        json={
            "title": "Completed overdue task",
            "assigned_to_id": current_user["id"],
            "status": "Completed",
            "due_at": (
                now - timedelta(days=2)
            ).isoformat(),
        },
    )

    db_session.add_all(
        [
            Meeting(
                title="Upcoming scheduled meeting",
                starts_at=now + timedelta(days=1),
                ends_at=now + timedelta(
                    days=1,
                    hours=1,
                ),
                status=MeetingStatus.SCHEDULED,
                organizer_id=current_user["id"],
            ),
            Meeting(
                title="Past scheduled meeting",
                starts_at=now - timedelta(days=2),
                ends_at=now - timedelta(
                    days=2,
                    hours=-1,
                ),
                status=MeetingStatus.SCHEDULED,
                organizer_id=current_user["id"],
            ),
            Meeting(
                title="Cancelled future meeting",
                starts_at=now + timedelta(days=2),
                ends_at=now + timedelta(
                    days=2,
                    hours=1,
                ),
                status=MeetingStatus.CANCELLED,
                organizer_id=current_user["id"],
            ),
        ]
    )
    db_session.commit()

    response = authenticated_client.get(
        "/api/v1/dashboard/summary"
    )

    assert response.status_code == 200

    summary = response.json()

    assert summary["total_companies"] == 1
    assert summary["total_contacts"] == 1
    assert summary["total_leads"] == 5
    assert Decimal(
        summary["pipeline_value"]
    ) == Decimal("4000.00")
    assert summary["leads_by_stage"] == {
        "New": 1,
        "Contacted": 1,
        "Qualified": 1,
        "Won": 1,
        "Lost": 1,
    }
    assert summary["pending_tasks"] == 2
    assert summary["overdue_tasks"] == 1
    assert summary["upcoming_meetings"] == 1


def test_dashboard_requires_authentication(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/v1/dashboard/summary"
    )

    assert response.status_code == 401