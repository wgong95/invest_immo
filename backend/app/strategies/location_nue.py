from typing import Any, Dict

from ..context import EngineContext
from ..finance import capital_restant, interets_annuels, irr
from ..kpis import (
    attach_yearly_financing_kpis,
    attach_yearly_profitability_kpis,
    compute_dscr_an1,
    compute_period_net_profitability,
    compute_profitability_kpis,
    compute_strategy_decision_metrics,
)


def compute(ctx: EngineContext) -> Dict[str, Any]:
    params = ctx.params
    yearly = []
    for an in range(1, params.horizon_ans + 1):
        coef_l = (1 + params.revalorisation_loyer_pct / 100) ** (an - 1)
        loyer = ctx.loyer_nu * 12 * coef_l * (1 - params.vacance_locative_pct / 100)
        interets = interets_annuels(ctx.amort, an, params.duree_pret_ans)
        charges = params.charges_copro_mensuelle * 12
        tf = params.taxe_fonciere_mensuelle * 12
        gestion = loyer * params.gestion_locative_pct / 100

        revenu_foncier = loyer - interets - charges - tf - gestion
        if revenu_foncier > 0:
            impot = revenu_foncier * ctx.taux_fiscal
        else:
            # Déficit imputable sur revenu global (plafond 10 700 €)
            impot = -min(abs(revenu_foncier), 10700) * params.tmi / 100

        mensualite_an = ctx.mensualite * 12 if an <= params.duree_pret_ans else 0
        cf = loyer - mensualite_an - charges - tf - gestion - impot

        coef_b = (1 + params.revalorisation_bien_pct / 100) ** an
        valeur = ctx.prix_achat * coef_b
        cap_r = capital_restant(ctx.amort, an)

        yearly.append({
            "annee": an,
            "loyer_annuel": round(loyer),
            "interets": round(interets),
            "charges": round(charges + tf + gestion),
            "impot": round(impot),
            "mensualite_an": round(mensualite_an),
            "cash_flow": round(cf),
            "valeur_bien": round(valeur),
            "capital_restant": round(cap_r),
            "patrimoine_net": round(valeur - cap_r),
        })

    valeur_fin = ctx.prix_achat * (1 + params.revalorisation_bien_pct / 100) ** params.horizon_ans
    attach_yearly_financing_kpis(yearly, ctx.cout_total, params.apport)
    attach_yearly_profitability_kpis(yearly, ctx.cout_total, ctx.prix_achat)
    cf_tri = [-(params.apport + ctx.frais_notaire + ctx.frais_annexes)] + [y["cash_flow"] for y in yearly]
    terminal_add = valeur_fin - yearly[-1]["capital_restant"]
    cf_tri[-1] += terminal_add
    tri = irr(cf_tri)
    decision = compute_strategy_decision_metrics(
        tri=tri,
        initial_outlay=-(params.apport + ctx.frais_notaire + ctx.frais_annexes),
        yearly_cashflows=[y["cash_flow"] for y in yearly],
        terminal_addition=terminal_add,
        debt=ctx.emprunt,
        equity=params.apport + ctx.frais_notaire + ctx.frais_annexes,
        beta_u=params.beta_u_location_nue,
        params=params,
        hamada_tax_rate=ctx.hamada_tax_rate,
    )
    kpis = compute_profitability_kpis(yearly, ctx.cout_total, ctx.prix_achat)
    rentabilite_period = compute_period_net_profitability(yearly, ctx.cout_total, yearly[-1]["patrimoine_net"])

    return {
        "id": "location_nue",
        "nom": "Location Nue",
        "description": "Régime réel — déduction intérêts, charges et travaux. Déficit imputable sur revenu global (plafond 10 700 €/an).",
        "mensualite": round(ctx.mensualite),
        "loyer_mensuel": round(ctx.loyer_nu),
        "cash_flow_moyen": round(sum(y["cash_flow"] for y in yearly) / len(yearly) / 12),
        "patrimoine_net_final": yearly[-1]["patrimoine_net"],
        "tri": round(tri, 2) if tri else None,
        "van": decision["van"],
        "ke": decision["ke"],
        "beta_u": decision["beta_u"],
        "beta_l": decision["beta_l"],
        "discount_rate_used": decision["discount_rate_used"],
        "tri_minus_ke": decision["tri_minus_ke"],
        "dscr": compute_dscr_an1(yearly, "loyer_annuel"),
        "coc_return_pct": decision["coc_return_pct"],
        "stress_van": decision["stress_van"],
        "stress_pass": decision["stress_pass"],
        "is_candidate": decision["is_candidate"],
        "rendement_brut": round(ctx.loyer_nu * 12 / ctx.prix_achat * 100, 2),
        "rentabilite_nette_sur_periode": rentabilite_period,
        "rentabilite_nette_locative_hors_revalo": kpis["rentabilite_nette_locative_hors_revalo"],
        "rentabilite_nette_totale_avec_revalo": kpis["rentabilite_nette_totale_avec_revalo"],
        "yearly": yearly,
    }
