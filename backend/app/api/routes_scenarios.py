from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser
from app.config import get_settings
from app.database import get_db
from app.models import Reminder, ScenarioRun, ScenarioStatus
from app.schemas.scenarios import ScenarioOut, ScenarioStartRequest
from app.services.scenarios import start_scenario

router = APIRouter(prefix="/api/cats/{cat_id}/scenarios", tags=["scenarios"])


@router.get("", response_model=list[ScenarioOut])
async def list_scenarios(
    cat_id: int,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[ScenarioOut]:
    from app.services.scenarios import ensure_cat_owned

    try:
        await ensure_cat_owned(db, user.id, cat_id)
    except PermissionError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found") from None
    res = await db.execute(
        select(ScenarioRun).where(ScenarioRun.cat_id == cat_id).order_by(ScenarioRun.id.desc())
    )
    runs = res.scalars().all()
    return [ScenarioOut.model_validate(r) for r in runs]


@router.post("", response_model=ScenarioOut, status_code=status.HTTP_201_CREATED)
async def start_scenario_route(
    cat_id: int,
    body: ScenarioStartRequest,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ScenarioOut:
    settings = get_settings()
    try:
        run = await start_scenario(
            db,
            user_id=user.id,
            cat_id=cat_id,
            scenario_type=body.scenario_type,
            default_tz=settings.default_tz,
            anchor=body.anchor_at,
            context=body.context,
        )
        await db.refresh(run)
    except PermissionError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found") from None
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return ScenarioOut.model_validate(run)


@router.post("/{run_id}/cancel", response_model=ScenarioOut)
async def cancel_scenario(
    cat_id: int,
    run_id: int,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ScenarioOut:
    from app.services.scenarios import ensure_cat_owned

    try:
        await ensure_cat_owned(db, user.id, cat_id)
    except PermissionError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found") from None
    res = await db.execute(
        select(ScenarioRun).where(
            ScenarioRun.id == run_id,
            ScenarioRun.cat_id == cat_id,
        )
    )
    run = res.scalar_one_or_none()
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    run.status = ScenarioStatus.cancelled
    await db.execute(
        update(Reminder)
        .where(
            Reminder.scenario_run_id == run.id,
            Reminder.sent_at.is_(None),
        )
        .values(cancelled=True)
    )
    await db.flush()
    return ScenarioOut.model_validate(run)
