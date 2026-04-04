from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal


@dataclass(frozen=True)
class Drug:
    slug: str
    mg_per_kg_min: Decimal
    mg_per_kg_max: Decimal


DRUGS: dict[str, Drug] = {
    "metronidazole": Drug("metronidazole", Decimal("15"), Decimal("25")),
    "amoxicillin": Drug("amoxicillin", Decimal("10"), Decimal("20")),
    "maropitant": Drug("maropitant", Decimal("1"), Decimal("2")),
    "buprenorphine": Drug("buprenorphine", Decimal("0.01"), Decimal("0.02")),
}


def compute_dose_mg(drug_slug: str, weight_kg: Decimal, use: str = "mid") -> dict:
    drug = DRUGS.get(drug_slug)
    if drug is None:
        raise KeyError("unknown_drug")
    if weight_kg <= 0:
        raise ValueError("bad_weight")

    if use == "min":
        dose_per_kg = drug.mg_per_kg_min
    elif use == "max":
        dose_per_kg = drug.mg_per_kg_max
    else:
        dose_per_kg = (drug.mg_per_kg_min + drug.mg_per_kg_max) / 2

    mg = (weight_kg * dose_per_kg).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
    return {
        "drug": drug_slug,
        "weight_kg": str(weight_kg),
        "mg": str(mg),
        "mg_per_kg_used": str(dose_per_kg),
    }
