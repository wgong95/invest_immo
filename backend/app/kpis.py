from typing import Any, Dict, List, Optional

from .finance import compute_ke_hamada_capm, npv
from .models import Params


def compute_strategy_decision_metrics(
    tri: Optional[float],
    initial_outlay: float,
    yearly_cashflows: List[float],
    terminal_addition: float,
    debt: float,
    equity: float,
    beta_u: float,
    params: Params,
    hamada_tax_rate: float,
) -> Dict[str, Any]:
    capm = compute_ke_hamada_capm(
        beta_u=beta_u,
        debt=debt,
        equity=equity,
        tax_rate=hamada_tax_rate,
        risk_free_rate=params.taux_sans_risque,
        market_risk_premium=params.prime_risque_marche,
    )
    ke = capm["ke"]
    discount_rate = params.taux_actualisation if params.taux_actualisation is not None else ke

    base_cf = [initial_outlay] + yearly_cashflows
    base_cf[-1] += terminal_addition
    van = npv(base_cf, discount_rate)

    stress_cf = [initial_outlay] + [cf * params.stress_cashflow_factor for cf in yearly_cashflows]
    stress_cf[-1] += terminal_addition * params.stress_terminal_factor
    stress_van = npv(stress_cf, discount_rate)

    coc_return = 0.0
    if initial_outlay < 0 and yearly_cashflows:
        coc_return = yearly_cashflows[0] / abs(initial_outlay) * 100

    tri_minus_ke = None if tri is None else round(tri - ke, 2)

    return {
        "van": round(van),
        "discount_rate_used": round(discount_rate, 2),
        "ke": ke,
        "beta_u": capm["beta_u"],
        "beta_l": capm["beta_l"],
        "tri_minus_ke": tri_minus_ke,
        "coc_return_pct": round(coc_return, 2),
        "stress_van": round(stress_van),
        "stress_pass": stress_van > 0,
        "is_candidate": van > 0,
    }


def compute_dscr_an1(yearly: List[Dict[str, Any]], income_key: str) -> Optional[float]:
    """Debt Service Coverage Ratio for year 1: rental income / annual mortgage payment."""
    if not yearly:
        return None
    row = yearly[0]
    mensualite_an = row.get("mensualite_an") or 0
    revenu = row.get(income_key) or 0
    if mensualite_an <= 0:
        return None
    return round(revenu / mensualite_an, 2)


def _row_income(row: Dict[str, Any]) -> float:
    revenu = float(row.get("loyer_annuel", row.get("loyer_economise", 0.0)) or 0.0)
    charges = float(row.get("charges", 0.0) or 0.0)
    impot = float(row.get("impot", 0.0) or 0.0)
    return revenu - charges - impot


def compute_profitability_kpis(
    yearly: List[Dict[str, Any]],
    initial_cost: float,
    asset_base_value: Optional[float] = None,
) -> Dict[str, float]:
    if not yearly or initial_cost <= 0:
        return {
            "rentabilite_nette_locative_hors_revalo": 0.0,
            "rentabilite_nette_totale_avec_revalo": 0.0,
        }

    # Yearly-based KPI: use the last simulated year (not horizon-average)
    last_row = yearly[-1]
    locative_year = _row_income(last_row)

    current_asset_value = last_row.get("valeur_bien")
    if current_asset_value is None:
        current_asset_value = last_row.get("patrimoine_net")

    previous_asset_value = asset_base_value
    if len(yearly) >= 2:
        prev_row = yearly[-2]
        previous_asset_value = prev_row.get("valeur_bien")
        if previous_asset_value is None:
            previous_asset_value = prev_row.get("patrimoine_net")

    asset_growth_year = 0.0
    if current_asset_value is not None and previous_asset_value is not None:
        asset_growth_year = float(current_asset_value) - float(previous_asset_value)

    total_year = locative_year + asset_growth_year

    return {
        "rentabilite_nette_locative_hors_revalo": round(locative_year / initial_cost * 100, 2),
        "rentabilite_nette_totale_avec_revalo": round(total_year / initial_cost * 100, 2),
    }


def attach_yearly_financing_kpis(
    yearly: List[Dict[str, Any]],
    initial_cost: float,
    apport: float,
) -> None:
    if not yearly or initial_cost <= 0:
        for row in yearly:
            row["rentabilite_nette_apres_financement_pct"] = 0.0
            row["cash_flow_yield_pct"] = 0.0
        return

    base_apport = apport if apport > 0 else initial_cost
    for row in yearly:
        cash_flow = float(row.get("cash_flow", 0.0) or 0.0)
        row["rentabilite_nette_apres_financement_pct"] = round(cash_flow / initial_cost * 100, 2)
        row["cash_flow_yield_pct"] = round(cash_flow / base_apport * 100, 2)


def compute_period_net_profitability(
    yearly: List[Dict[str, Any]],
    initial_cost: float,
    final_net_asset_value: float,
) -> float:
    if not yearly or initial_cost <= 0:
        return 0.0
    cumulative_cash_flow = sum(float(row.get("cash_flow", 0.0) or 0.0) for row in yearly)
    total_gain = cumulative_cash_flow + final_net_asset_value - initial_cost
    return round(total_gain / initial_cost * 100, 2)


def attach_yearly_profitability_kpis(
    yearly: List[Dict[str, Any]],
    initial_cost: float,
    asset_base_value: Optional[float] = None,
) -> None:
    if not yearly or initial_cost <= 0:
        for row in yearly:
            row["rentabilite_nette_locative_hors_revalo_pct"] = 0.0
            row["rentabilite_nette_totale_avec_revalo_pct"] = 0.0
        return

    prev_asset_value = asset_base_value
    for row in yearly:
        locative_year = _row_income(row)

        current_asset_value = row.get("valeur_bien")
        if current_asset_value is None:
            current_asset_value = row.get("patrimoine_net")

        asset_growth_year = 0.0
        if current_asset_value is not None and prev_asset_value is not None:
            asset_growth_year = float(current_asset_value) - float(prev_asset_value)

        if current_asset_value is not None:
            prev_asset_value = float(current_asset_value)

        total_year = locative_year + asset_growth_year
        row["rentabilite_nette_locative_hors_revalo_pct"] = round(locative_year / initial_cost * 100, 2)
        row["rentabilite_nette_totale_avec_revalo_pct"] = round(total_year / initial_cost * 100, 2)
