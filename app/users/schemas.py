from pydantic import BaseModel, EmailStr
from app.db.models.user import UserRole
from datetime import datetime


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.analyst


class UserUpdate(BaseModel):
    role: UserRole | None = None
    is_active: bool | None = None
    password: str | None = None


class UserOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    username: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime
