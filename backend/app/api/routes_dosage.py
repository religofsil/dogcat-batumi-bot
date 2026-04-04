from fastapi import APIRouter, HTTPException, status

from app.schemas.dosage import DosageRequest, DosageResponse
from app.services.dosage import DRUGS, compute_dose_mg

router = APIRouter(prefix="/api/dosage", tags=["dosage"])


@router.get("/drugs")
async def list_drugs() -> dict[str, list[str]]:
    return {"drugs": sorted(DRUGS.keys())}


@router.post("/calculate", response_model=DosageResponse)
async def calculate(body: DosageRequest) -> DosageResponse:
    try:
        out = compute_dose_mg(body.drug_slug, body.weight_kg, use=body.use)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="unknown_drug") from None
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return DosageResponse(**out)
