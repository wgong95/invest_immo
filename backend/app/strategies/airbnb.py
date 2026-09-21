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
    mobilier = ctx.mobilier  # unified with LMNP furniture allowance
    # Paris/Paris-like regulatory cap for a primary residence short-term rental.
    # 120 days / 365 days ~= 32.9% occupancy.
    taux_occupation = 120 / 365
    revenu_nuitee = ctx.loyer_meuble * 2.8
    revenu_mensuel = revenu_nuitee * taux_occupation
    frais_plateforme_pct = 0.15
    frais_conciergerie_pct = 0.20
    amort_bien_an = ctx.prix_achat * 0.80 / 30

    yearly = []
    for an in range(1, params.horizon_ans + 1):
        coef_l = (1 + params.revalorisation_loyer_pct / 100) ** (an - 1)
        revenu = revenu_mensuel * 12 * coef_l
        interets = interets_annuels(ctx.amort, an, params.duree_pret_ans)
        charges = params.charges_copro_mensuelle * 12
        tf = params.taxe_fonciere_mensuelle * 12
        plateforme = revenu * frais_plateforme_pct
        conciergerie = revenu * frais_conciergerie_pct
        menage = 150 * 12
        amort_mob = mobilier / 7 if an <= 7 else 0

        bic = revenu - interets - charges - tf - plateforme - conciergerie - menage - amort_bien_an - amort_mob
        impot = max(0, bic) * ctx.taux_fiscal

        mensualite_an = ctx.mensualite * 12 if an <= params.duree_pret_ans else 0
        cf = revenu - mensualite_an - charges - tf - plateforme - conciergerie - menage - impot

        coef_b = (1 + params.revalorisation_bien_pct / 100) ** an
        valeur = ctx.prix_achat * coef_b
        cap_r = capital_restant(ctx.amort, an)

        yearly.append({
            "annee": an,
            "loyer_annuel": round(revenu),
            "interets": round(interets),
            "charges": round(charges + tf + plateforme + conciergerie + menage),
            "impot": round(impot),
            "mensualite_an": round(mensualite_an),
            "cash_flow": round(cf),
            "valeur_bien": round(valeur),
            "capital_restant": round(cap_r),
            "patrimoine_net": round(valeur - cap_r),
        })

    valeur_fin = ctx.prix_achat * (1 + params.revalorisation_bien_pct / 100) ** params.horizon_ans
    attach_yearly_financing_kpis(yearly, ctx.cout_total + mobilier, params.apport)
    attach_yearly_profitability_kpis(yearly, ctx.cout_total, ctx.prix_achat)
    cf_tri = [-(params.apport + ctx.frais_notaire + ctx.frais_annexes + mobilier)] + [y["cash_flow"] for y in yearly]
    terminal_add = valeur_fin - yearly[-1]["capital_restant"]
    cf_tri[-1] += terminal_add
    tri = irr(cf_tri)
    decision = compute_strategy_decision_metrics(
        tri=tri,
        initial_outlay=-(params.apport + ctx.frais_notaire + ctx.frais_annexes + mobilier),
        yearly_cashflows=[y["cash_flow"] for y in yearly],
        terminal_addition=terminal_add,
        debt=ctx.emprunt,
        equity=params.apport + ctx.frais_notaire + ctx.frais_annexes + mobilier,
        beta_u=params.beta_u_airbnb,
        params=params,
        hamada_tax_rate=ctx.hamada_tax_rate,
    )
    kpis = compute_profitability_kpis(yearly, ctx.cout_total, ctx.prix_achat)
    rentabilite_period = compute_period_net_profitability(yearly, ctx.cout_total + mobilier, yearly[-1]["patrimoine_net"])

    return {
        "id": "airbnb",
        "nom": "Location Courte Durée",
        "description": "Airbnb / saisonnier — revenus ×2,8 mais frais plateforme (15 %), conciergerie (20 %) et ménage. Risque réglementaire élevé à Paris.",
        "mensualite": round(ctx.mensualite),
        "loyer_mensuel": round(revenu_mensuel),
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
        "rendement_brut": round(revenu_mensuel * 12 / ctx.prix_achat * 100, 2),
        "rentabilite_nette_sur_periode": rentabilite_period,
        "rentabilite_nette_locative_hors_revalo": kpis["rentabilite_nette_locative_hors_revalo"],
        "rentabilite_nette_totale_avec_revalo": kpis["rentabilite_nette_totale_avec_revalo"],
        "yearly": yearly,
    }
