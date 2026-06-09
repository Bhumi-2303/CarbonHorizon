"""
Report Pydantic schemas — no logic yet.
"""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel


class ReportBase(BaseModel):
    title: str
    period_start: datetime
    period_end: datetime
    status: Literal["draft", "published", "archived"] = "draft"
    summary: Optional[str] = None


class ReportCreate(ReportBase):
    organization_id: int


class ReportUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[Literal["draft", "published", "archived"]] = None
    summary: Optional[str] = None


class ReportResponse(ReportBase):
    id: int
    organization_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
