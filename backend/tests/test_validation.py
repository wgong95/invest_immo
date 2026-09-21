import pytest
from pydantic import ValidationError

from app.models import Params


def test_defaults_are_valid():
    Params()  # should not raise


@pytest.mark.parametrize(
    "field,value",
    [
        ("surface", 0),
        ("surface", -10),
        ("prix_m2_achat", 0),
        ("prix_m2_achat", -1),
        ("loyer_m2", 0),
        ("duree_pret_ans", 0),
        ("duree_pret_ans", -5),
        ("horizon_ans", 0),
        ("apport", -1000),
        ("tmi", -5),
        ("vacance_locative_pct", 150),
        ("gestion_locative_pct", -1),
        ("frais_notaire_pct", -1),
    ],
)
def test_invalid_values_are_rejected(field, value):
    with pytest.raises(ValidationError):
        Params(**{field: value})


def test_valid_overrides_are_accepted():
    params = Params(surface=45.5, prix_m2_achat=9500, duree_pret_ans=25, horizon_ans=30)
    assert params.surface == 45.5
    assert params.duree_pret_ans == 25
