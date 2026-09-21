import pytest

from app.finance import (
    calcul_taeg,
    capital_restant,
    compute_ke_hamada_capm,
    interets_annuels,
    irr,
    mensualite_credit,
    npv,
    tableau_amortissement,
)


def test_mensualite_credit_zero_capital():
    assert mensualite_credit(0, 3.3, 10) == 0.0


def test_mensualite_credit_zero_rate_is_linear():
    assert mensualite_credit(120_000, 0, 10) == pytest.approx(1000.0)


def test_mensualite_credit_standard_annuity():
    m = mensualite_credit(200_000, 3.3, 20)
    assert m == pytest.approx(1139.47, abs=0.5)


def test_tableau_amortissement_length_matches_duration():
    rows = tableau_amortissement(150_000, 3.0, 15)
    assert len(rows) == 15 * 12


def test_tableau_amortissement_fully_repays_loan():
    rows = tableau_amortissement(150_000, 3.0, 15)
    assert rows[-1]["capital_restant"] == pytest.approx(0.0, abs=1.0)


def test_interets_annuels_zero_after_loan_ends():
    amort = tableau_amortissement(100_000, 3.0, 5)
    assert interets_annuels(amort, 10, 5) == 0.0


def test_interets_annuels_positive_during_loan():
    amort = tableau_amortissement(100_000, 3.0, 5)
    assert interets_annuels(amort, 1, 5) > 0


def test_capital_restant_zero_when_no_loan():
    assert capital_restant([], 5) == 0.0


def test_capital_restant_decreases_over_time():
    amort = tableau_amortissement(100_000, 3.0, 10)
    assert capital_restant(amort, 5) > capital_restant(amort, 9)


def test_irr_simple_one_year_case():
    rate = irr([-100, 110])
    assert rate == pytest.approx(10.0, abs=0.01)


def test_irr_requires_negative_initial_cash_flow():
    assert irr([100, 100]) is None
    assert irr([]) is None


def test_npv_zero_rate_is_plain_sum():
    assert npv([-100, 50, 60], 0) == pytest.approx(10.0)


def test_npv_empty_is_zero():
    assert npv([], 5.0) == 0.0


def test_calcul_taeg_exceeds_nominal_rate_with_insurance_and_fees():
    capital = 200_000
    taux_nominal = 3.3
    duree_ans = 20
    m = mensualite_credit(capital, taux_nominal, duree_ans)
    assurance = capital * 0.36 / 100 / 12
    taeg = calcul_taeg(
        emprunt=capital,
        mensualite=m,
        mensualite_assurance=assurance,
        duree_mois=duree_ans * 12,
        frais_annexes=1000,
    )
    assert taeg is not None
    assert taeg > taux_nominal


def test_calcul_taeg_none_when_no_loan():
    assert calcul_taeg(emprunt=0, mensualite=0, mensualite_assurance=0, duree_mois=240, frais_annexes=0) is None


def test_compute_ke_hamada_capm_unlevers_with_no_debt():
    result = compute_ke_hamada_capm(
        beta_u=0.8,
        debt=0,
        equity=100_000,
        tax_rate=0.3,
        risk_free_rate=1.6,
        market_risk_premium=5.0,
    )
    assert result["beta_l"] == pytest.approx(0.8)
    assert result["ke"] == pytest.approx(1.6 + 0.8 * 5.0, abs=0.01)


def test_compute_ke_hamada_capm_levers_up_with_debt():
    unlevered = compute_ke_hamada_capm(
        beta_u=0.8, debt=0, equity=100_000, tax_rate=0.3,
        risk_free_rate=1.6, market_risk_premium=5.0,
    )
    levered = compute_ke_hamada_capm(
        beta_u=0.8, debt=200_000, equity=100_000, tax_rate=0.3,
        risk_free_rate=1.6, market_risk_premium=5.0,
    )
    assert levered["beta_l"] > unlevered["beta_l"]
    assert levered["ke"] > unlevered["ke"]
