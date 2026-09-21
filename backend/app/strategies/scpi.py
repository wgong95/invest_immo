from typing import Any, Dict

from ..context import EngineContext
from ..finance import irr
from ..kpis import (
    attach_yearly_financing_kpis,
    attach_yearly_profitability_kpis,
    compute_period_net_profitability,
    compute_profitability_kpis,
    compute_strategy_decision_metrics,
)


def compute(ctx: EngineContext) -> Dict[str, Any]:
    params = ctx.params
    frais_entree = 0.09
    capital_net = params.apport * (1 - frais_entree)
    rendement = params.rendement_scpi / 100
    revalorisation_parts = 0.01

    yearly = []
    valeur_parts = capital_net

    for an in range(1, params.horizon_ans + 1):
        revenu = valeur_parts * rendement
        impot = revenu * ctx.taux_fiscal
        cf = revenu - impot
        valeur_parts = valeur_parts * (1 + revalorisation_parts)

        yearly.append({
            "annee": an,
            "loyer_annuel": round(revenu),
            "impot": round(impot),
            "cash_flow": round(cf),
            "patrimoine_net": round(valeur_parts),
        })

    attach_yearly_financing_kpis(yearly, params.apport, params.apport)
    attach_yearly_profitability_kpis(yearly, params.apport, capital_net)
    cf_tri = [-params.apport] + [y["cash_flow"] for y in yearly]
    terminal_add = yearly[-1]["patrimoine_net"]
    cf_tri[-1] += terminal_add
    tri = irr(cf_tri)
    decision = compute_strategy_decision_metrics(
        tri=tri,
        initial_outlay=-params.apport,
        yearly_cashflows=[y["cash_flow"] for y in yearly],
        terminal_addition=terminal_add,
        debt=0,
        equity=params.apport,
        beta_u=params.beta_u_scpi,
        params=params,
        hamada_tax_rate=ctx.hamada_tax_rate,
    )
    kpis = compute_profitability_kpis(yearly, params.apport, capital_net)
    rentabilite_period = compute_period_net_profitability(yearly, params.apport, yearly[-1]["patrimoine_net"])

    return {
        "id": "scpi",
        "nom": "SCPI",
        "description": f"Pierre-papier — {params.apport:,.0f} € investis directement. Rendement {params.rendement_scpi} %, pas de gestion, pas d'effet de levier.",
        "mensualite": 0,
        "loyer_mensuel": round(capital_net * rendement / 12),
        "cash_flow_moyen": round(sum(y["cash_flow"] for y in yearly) / len(yearly) / 12),
        "patrimoine_net_final": yearly[-1]["patrimoine_net"],
        "tri": round(tri, 2) if tri else None,
        "van": decision["van"],
        "ke": decision["ke"],
        "beta_u": decision["beta_u"],
        "beta_l": decision["beta_l"],
        "discount_rate_used": decision["discount_rate_used"],
        "tri_minus_ke": decision["tri_minus_ke"],
        "dscr": None,
        "coc_return_pct": decision["coc_return_pct"],
        "stress_van": decision["stress_van"],
        "stress_pass": decision["stress_pass"],
        "is_candidate": decision["is_candidate"],
        "rendement_brut": round(params.rendement_scpi, 2),
        "rentabilite_nette_sur_periode": rentabilite_period,
        "rentabilite_nette_locative_hors_revalo": kpis["rentabilite_nette_locative_hors_revalo"],
        "rentabilite_nette_totale_avec_revalo": kpis["rentabilite_nette_totale_avec_revalo"],
        "yearly": yearly,
    }
