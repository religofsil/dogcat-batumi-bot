from fastapi import APIRouter

from app.api.deps import CurrentUser
from app.services.i18n import t

router = APIRouter(prefix="/api/templates", tags=["templates"])


@router.get("/sterilization_clinic")
async def sterilization_clinic(user: CurrentUser) -> dict[str, str]:
    return {"text": t(user.locale, "templates.sterilization_clinic")}


@router.get("/potential_adopter_questions")
async def potential_adopter_questions(user: CurrentUser) -> dict[str, str]:
    return {"text": t(user.locale, "templates.potential_adopter_questions")}


@router.get("/post_structure")
async def post_structure(user: CurrentUser) -> dict[str, str]:
    return {"text": t(user.locale, "templates.post_structure")}
