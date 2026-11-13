from pydantic import BaseModel
from datetime import datetime


class AlertOut(BaseModel):
    id: str
    label: str | None
    submitted_by: int
    submitted_at: datetime

