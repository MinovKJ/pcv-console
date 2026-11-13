"""
MySQL ORM model: alert_assignments
Links a MongoDB alert document to a Case.
"""
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.mysql import Base


class AlertAssignment(Base):
    __tablename__ = "alert_assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    alert_mongo_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    case_id: Mapped[int] = mapped_column(Integer, ForeignKey("cases.id"), nullable=False)
    assigned_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    case: Mapped["Case"] = relationship("Case", back_populates="alert_assignments")

