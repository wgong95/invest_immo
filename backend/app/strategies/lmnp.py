from typing import Any, Dict, List

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
    mobilier = ctx.mobilier
    amort_bien_an = ctx.prix_achat * 0.80 / 30
    loyer_meuble = ctx.loyer_meuble

    yearly = []
    amort_reporte = 0.0
    deficits_10_ans: List[Dict[str, float]] = []

    for an in range(1, params.horizon_ans + 1):
        # Décrément du stock de déficits reportables (10 ans glissants)
        for d in deficits_10_ans:
            d["annees_restantes"] -= 1
        deficits_10_ans = [d for d in deficits_10_ans if d["annees_restantes"] > 0 and d["montant"] > 0]

        coef_l = (1 + params.revalorisation_loyer_pct / 100) ** (an - 1)
        loyer = loyer_meuble * 12 * coef_l * (1 - params.vacance_locative_pct / 100)
        interets = interets_annuels(ctx.amort, an, params.duree_pret_ans)
        charges_copro = params.charges_copro_mensuelle * 12
        tf = params.taxe_fonciere_mensuelle * 12
        gestion = loyer * params.gestion_locative_pct / 100
        amort_mob = mobilier / 7 if an <= 7 else 0

        # Charges déductibles hors amortissements
        charges_courantes = (
            interets
            + charges_copro
            + tf
            + gestion
            + params.travaux_annuel
            + params.assurance_pno_annuel
            + params.cfe_annuel
            + params.honoraires_comptable_annuel
        )
        charges_exploitation = (
            charges_copro
            + tf
            + gestion
            + params.travaux_annuel
            + params.assurance_pno_annuel
            + params.cfe_annuel
            + params.honoraires_comptable_annuel
        )

        # BIC avant amortissement
        bic_avant_amort = loyer - charges_courantes

        # Amortissements plafonnés
        amort_total = amort_bien_an + amort_mob + params.amort_frais_acq_annuel + amort_reporte
        amort_deductible = min(amort_total, max(0.0, bic_avant_amort))
        amort_reporte_incremental = amort_total - amort_deductible
        amort_reporte = amort_reporte_incremental

        # Résultat après amortissement
        bic_apres_amort = bic_avant_amort - amort_deductible

        # Application du déficit reporté des 10 dernières années
        imputation_deficit = 0.0
        if bic_apres_amort > 0:
            reste_a_imputer = bic_apres_amort
            for d in deficits_10_ans:
                if reste_a_imputer <= 0:
                    break
                part = min(d["montant"], reste_a_imputer)
                d["montant"] -= part
                reste_a_imputer -= part
                imputation_deficit += part
            deficits_10_ans = [d for d in deficits_10_ans if d["montant"] > 0 and d["annees_restantes"] > 0]

        bic_net_imposable = max(0.0, bic_apres_amort - imputation_deficit)

        # Si résultat fiscal négatif, il alimente un déficit reportable 10 ans
        if bic_apres_amort < 0:
            deficits_10_ans.append({"montant": abs(bic_apres_amort), "annees_restantes": 10.0})

        impot = bic_net_imposable * ctx.taux_fiscal

        mensualite_an = ctx.mensualite * 12 if an <= params.duree_pret_ans else 0
        cf = loyer - mensualite_an - charges_exploitation - impot

        coef_b = (1 + params.revalorisation_bien_pct / 100) ** an
        valeur = ctx.prix_achat * coef_b
        cap_r = capital_restant(ctx.amort, an)

        yearly.append({
            "annee": an,
            "loyer_annuel": round(loyer),
            "interets": round(interets),
            "charges": round(charges_exploitation),
            "amortissement": round(amort_deductible),
            "bic_imposable": round(bic_net_imposable),
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
        beta_u=params.beta_u_lmnp,
        params=params,
        hamada_tax_rate=ctx.hamada_tax_rate,
    )
    kpis = compute_profitability_kpis(yearly, ctx.cout_total, ctx.prix_achat)
    rentabilite_period = compute_period_net_profitability(yearly, ctx.cout_total + mobilier, yearly[-1]["patrimoine_net"])

    return {
        "id": "lmnp_meuble",
        "nom": "LMNP Meublé",
        "description": "BIC régime réel — amortissement du bien (30 ans) et du mobilier (7 ans). Fiscalité quasi nulle pendant ~15 ans.",
        "mensualite": round(ctx.mensualite),
        "loyer_mensuel": round(loyer_meuble),
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
        "rendement_brut": round(loyer_meuble * 12 / ctx.prix_achat * 100, 2),
        "rentabilite_nette_sur_periode": rentabilite_period,
        "rentabilite_nette_locative_hors_revalo": kpis["rentabilite_nette_locative_hors_revalo"],
        "rentabilite_nette_totale_avec_revalo": kpis["rentabilite_nette_totale_avec_revalo"],
        "yearly": yearly,
    }
