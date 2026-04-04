from decimal import Decimal

import pytest
from app.services.dosage import compute_dose_mg


def test_compute_mid() -> None:
    out = compute_dose_mg("metronidazole", Decimal("4.0"), use="mid")
    assert out["drug"] == "metronidazole"
    assert float(out["mg"]) > 0


def test_unknown_drug() -> None:
    with pytest.raises(KeyError):
        compute_dose_mg("nope", Decimal("3"))
