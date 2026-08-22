from pydantic import BaseModel

from app.schemas.company import CompanyRead
from app.schemas.contact import ContactRead
from app.schemas.lead import LeadRead


class SearchResults(BaseModel):
    companies: list[CompanyRead]
    contacts: list[ContactRead]
    leads: list[LeadRead]