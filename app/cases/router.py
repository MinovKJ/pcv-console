"""
Cases router: create, list, update, assign alerts to cases.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.case import Case
from app.db.models.alert_assignment import AlertAssignment
from app.db.models.user import User, UserRole
from app.db.mysql import get_db
from app.dependencies import get_current_user, record_audit, require_role
from app.cases.schemas import CaseCreate, CaseOut, CaseUpdate, AlertAssignRequest, AlertAssignOut

router = APIRouter(prefix="/cases", tags=["cases"])


@router.post("/", response_model=CaseOut, status_code=status.HTTP_201_CREATED)
async def create_case(
    body: CaseCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    case = Case(
        title=body.title,
        description=body.description,
        severity=body.severity,
        created_by=user.id,
        assigned_to=body.assigned_to,
    )
    db.add(case)
    await db.commit()
    await db.refresh(case)
    await record_audit(db, user.id, "CREATE_CASE", "case", str(case.id), request)
    return CaseOut.model_validate(case)


@router.get("/", response_model=list[CaseOut])
async def list_cases(
    skip: int = 0,
    limit: int = 50,
    status_filter: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = select(Case)
    if status_filter:
        q = q.where(Case.status == status_filter)
    q = q.offset(skip).limit(limit)
    result = await db.execute(q)
    return [CaseOut.model_validate(c) for c in result.scalars()]


@router.get("/{case_id}", response_model=CaseOut)
async def get_case(
    case_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return CaseOut.model_validate(case)


@router.patch("/{case_id}", response_model=CaseOut)
async def update_case(
    case_id: int,
    body: CaseUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    for field, val in body.model_dump(exclude_none=True).items():
        setattr(case, field, val)
    await db.commit()
    await db.refresh(case)
    await record_audit(db, user.id, "UPDATE_CASE", "case", str(case_id), request, str(body.model_dump()))
    return CaseOut.model_validate(case)


@router.post("/{case_id}/alerts", response_model=AlertAssignOut, status_code=status.HTTP_201_CREATED)
async def assign_alert_to_case(
    case_id: int,
    body: AlertAssignRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Case).where(Case.id == case_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Case not found")

    assignment = AlertAssignment(
        alert_mongo_id=body.alert_mongo_id,
        case_id=case_id,
        assigned_by=user.id,
    )
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)
    await record_audit(db, user.id, "ASSIGN_ALERT", "alert_assignment", str(assignment.id), request)
    return AlertAssignOut.model_validate(assignment)


@router.get("/{case_id}/alerts", response_model=list[AlertAssignOut])
async def list_case_alerts(
    case_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(AlertAssignment).where(AlertAssignment.case_id == case_id)
    )
    return [AlertAssignOut.model_validate(a) for a in result.scalars()]

