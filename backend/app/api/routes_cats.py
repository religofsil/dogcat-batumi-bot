from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser
from app.database import get_db
from app.models import Cat
from app.schemas.cats import CatCreate, CatOut, CatUpdate

router = APIRouter(prefix="/api/cats", tags=["cats"])


@router.get("", response_model=list[CatOut])
async def list_cats(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[CatOut]:
    res = await db.execute(select(Cat).where(Cat.user_id == user.id).order_by(Cat.id.desc()))
    cats = res.scalars().all()
    return [CatOut.model_validate(c) for c in cats]


@router.post("", response_model=CatOut, status_code=status.HTTP_201_CREATED)
async def create_cat(
    body: CatCreate,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CatOut:
    cat = Cat(user_id=user.id, name=body.name, weight_kg=body.weight_kg, notes=body.notes)
    db.add(cat)
    await db.flush()
    await db.refresh(cat)
    return CatOut.model_validate(cat)


@router.patch("/{cat_id}", response_model=CatOut)
async def update_cat(
    cat_id: int,
    body: CatUpdate,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CatOut:
    res = await db.execute(select(Cat).where(Cat.id == cat_id, Cat.user_id == user.id))
    cat = res.scalar_one_or_none()
    if cat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    if body.name is not None:
        cat.name = body.name
    if body.weight_kg is not None:
        cat.weight_kg = body.weight_kg
    if body.notes is not None:
        cat.notes = body.notes
    await db.flush()
    return CatOut.model_validate(cat)


@router.delete("/{cat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cat(
    cat_id: int,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    res = await db.execute(select(Cat).where(Cat.id == cat_id, Cat.user_id == user.id))
    cat = res.scalar_one_or_none()
    if cat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    await db.execute(delete(Cat).where(Cat.id == cat_id, Cat.user_id == user.id))
