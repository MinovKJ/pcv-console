from datetime import datetime
from pydantic import BaseModel
from app.db.models.case import CaseSeverity, CaseStatus


class CaseCreate(BaseModel):
    title: str
    description: str | None = None
    severity: CaseSeverity = CaseSeverity.medium
    assigned_to: int | None = None


class CaseUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    severity: CaseSeverity | None = None
    status: CaseStatus | None = None
    assigned_to: int | None = None


class CaseOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    title: str
    description: str | None
    severity: CaseSeverity
    status: CaseStatus
    created_by: int
    assigned_to: int | None
    created_at: datetime
    updated_at: datetime


class AlertAssignRequest(BaseModel):
    alert_mongo_id: str


class AlertAssignOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    alert_mongo_id: str
    case_id: int
    assigned_by: int
    assigned_at: datetime

