from datetime import datetime, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.models.lead import Lead, LeadStage
from app.schemas.lead import (
    LeadCreate,
    LeadRead,
    LeadUpdate,
)


def test_lead_create_normalizes_input_and_defaults_stage(
) -> None:
    lead = LeadCreate(
        title="  Website Redesign  ",
        company_id=1,
        estimated_value="1250.50",
        source="  Referral  ",
    )

    assert lead.title == "Website Redesign"
    assert lead.stage == LeadStage.NEW
    assert lead.estimated_value == Decimal("1250.50")
    assert lead.source == "Referral"


def test_lead_create_rejects_blank_title() -> None:
    with pytest.raises(ValidationError):
        LeadCreate(
            title="   ",
            company_id=1,
        )


def test_lead_create_rejects_invalid_stage() -> None:
    with pytest.raises(ValidationError):
        LeadCreate(
            title="Invalid Stage Lead",
            company_id=1,
            stage="In Progress",
        )


def test_lead_create_rejects_negative_value() -> None:
    with pytest.raises(ValidationError):
        LeadCreate(
            title="Negative Value Lead",
            company_id=1,
            estimated_value="-1.00",
        )


def test_lead_update_includes_only_provided_fields(
) -> None:
    update = LeadUpdate(
        stage=LeadStage.QUALIFIED,
    )

    assert update.model_dump(exclude_unset=True) == {
        "stage": LeadStage.QUALIFIED,
    }


def test_lead_read_accepts_sqlalchemy_model() -> None:
    now = datetime.now(timezone.utc)

    lead_model = Lead(
        id=1,
        title="Website Redesign",
        company_id=2,
        contact_id=None,
        stage=LeadStage.NEW,
        estimated_value=Decimal("2500.00"),
        source="Referral",
        expected_close_date=None,
        description=None,
        created_at=now,
        updated_at=now,
    )

    lead = LeadRead.model_validate(lead_model)

    assert lead.id == 1
    assert lead.title == "Website Redesign"
    assert lead.company_id == 2
    assert lead.stage == LeadStage.NEW