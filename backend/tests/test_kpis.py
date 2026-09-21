from app.kpis import (
    attach_yearly_financing_kpis,
    compute_dscr_an1,
    compute_period_net_profitability,
    compute_profitability_kpis,
)


def test_compute_profitability_kpis_zero_cost_is_safe():
    result = compute_profitability_kpis([], 0)
    assert result["rentabilite_nette_locative_hors_revalo"] == 0.0
    assert result["rentabilite_nette_totale_avec_revalo"] == 0.0


def test_compute_profitability_kpis_uses_last_two_years():
    yearly = [
        {"loyer_annuel": 10000, "charges": 2000, "impot": 1000, "valeur_bien": 200000},
        {"loyer_annuel": 10500, "charges": 2000, "impot": 1000, "valeur_bien": 205000},
    ]
    result = compute_profitability_kpis(yearly, 250000)
    locative_year = 10500 - 2000 - 1000
    asset_growth = 205000 - 200000
    assert result["rentabilite_nette_locative_hors_revalo"] == round(locative_year / 250000 * 100, 2)
    assert result["rentabilite_nette_totale_avec_revalo"] == round((locative_year + asset_growth) / 250000 * 100, 2)


def test_attach_yearly_financing_kpis_zero_cost_is_safe():
    yearly = [{"cash_flow": 100}]
    attach_yearly_financing_kpis(yearly, 0, 10000)
    assert yearly[0]["rentabilite_nette_apres_financement_pct"] == 0.0
    assert yearly[0]["cash_flow_yield_pct"] == 0.0


def test_attach_yearly_financing_kpis_computes_yields():
    yearly = [{"cash_flow": 1000}]
    attach_yearly_financing_kpis(yearly, 200000, 50000)
    assert yearly[0]["rentabilite_nette_apres_financement_pct"] == round(1000 / 200000 * 100, 2)
    assert yearly[0]["cash_flow_yield_pct"] == round(1000 / 50000 * 100, 2)


def test_compute_period_net_profitability_zero_cost_is_safe():
    assert compute_period_net_profitability([], 0, 100) == 0.0


def test_compute_period_net_profitability_sums_cashflow_and_gain():
    yearly = [{"cash_flow": 1000}, {"cash_flow": 1200}]
    result = compute_period_net_profitability(yearly, 100000, 120000)
    total_gain = 1000 + 1200 + 120000 - 100000
    assert result == round(total_gain / 100000 * 100, 2)


def test_compute_dscr_an1_ratio_of_income_to_debt_service():
    yearly = [{"loyer_annuel": 12000, "mensualite_an": 10000}]
    assert compute_dscr_an1(yearly, "loyer_annuel") == round(12000 / 10000, 2)


def test_compute_dscr_an1_none_without_debt():
    yearly = [{"loyer_annuel": 12000, "mensualite_an": 0}]
    assert compute_dscr_an1(yearly, "loyer_annuel") is None


def test_compute_dscr_an1_none_when_empty():
    assert compute_dscr_an1([], "loyer_annuel") is None
