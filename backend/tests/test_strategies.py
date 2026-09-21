import pytest

from app.context import build_context
from app.models import Params
from app.strategies import airbnb, lmnp, location_nue, residence_principale, scpi

ALL_STRATEGIES = [location_nue, lmnp, airbnb, scpi, residence_principale]


def make_ctx(**overrides):
    return build_context(Params(**overrides))


def test_mobilier_is_unified_across_ctx():
    ctx = make_ctx()
    assert ctx.mobilier == pytest.approx(ctx.prix_achat * 0.12)


def test_loyer_meuble_defaults_to_15_pct_premium_when_not_set():
    ctx = make_ctx(loyer_m2=42, surface=26.12)
    assert ctx.loyer_meuble == pytest.approx(ctx.loyer_nu * 1.15)


def test_loyer_meuble_uses_explicit_rate_when_set():
    ctx = make_ctx(loyer_m2=42, loyer_m2_meuble=42, surface=26.12)
    assert ctx.loyer_meuble == pytest.approx(ctx.loyer_nu)
    assert ctx.loyer_meuble == pytest.approx(42 * 26.12)


@pytest.mark.parametrize("module", ALL_STRATEGIES)
def test_strategy_produces_full_horizon(module):
    ctx = make_ctx(horizon_ans=15)
    result = module.compute(ctx)
    assert len(result["yearly"]) == 15
    assert result["yearly"][-1]["annee"] == 15


@pytest.mark.parametrize("module", ALL_STRATEGIES)
def test_strategy_patrimoine_final_matches_last_row(module):
    ctx = make_ctx()
    result = module.compute(ctx)
    assert result["patrimoine_net_final"] == result["yearly"][-1]["patrimoine_net"]


@pytest.mark.parametrize("module", ALL_STRATEGIES)
def test_strategy_exposes_decision_metrics(module):
    ctx = make_ctx()
    result = module.compute(ctx)
    for key in ("van", "ke", "tri_minus_ke", "stress_van", "stress_pass", "is_candidate"):
        assert key in result


def test_scpi_has_no_leverage():
    ctx = make_ctx()
    result = scpi.compute(ctx)
    assert result["mensualite"] == 0


def test_residence_principale_has_no_rental_income():
    ctx = make_ctx()
    result = residence_principale.compute(ctx)
    assert result["loyer_mensuel"] == 0
    assert result["rendement_brut"] == 0


def test_airbnb_occupancy_reflects_120_day_paris_cap():
    ctx = make_ctx(loyer_m2=42, surface=30, vacance_locative_pct=0)
    result = airbnb.compute(ctx)
    revenu_nuitee = ctx.loyer_meuble * 2.8
    expected_monthly = revenu_nuitee * (120 / 365)
    assert result["loyer_mensuel"] == round(expected_monthly)
