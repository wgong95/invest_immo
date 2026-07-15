from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

app = FastAPI(title="Invest Immo Analyser")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class Params(BaseModel):
    apport: float = 250000
    taux_interet: float = 3.3
    revenu_mensuel_brut: float = 7000
    prix_m2_achat: float = 11000
    loyer_m2: float = 38.5
    loyer_meuble_m2: float = 43.0
    surface: float = 30
    duree_pret_ans: int = 10
    frais_notaire_pct: float = 8
    charges_copro_mensuelle: float = 150
    taxe_fonciere_mensuelle: float = 125
    vacance_locative_pct: float = 5.0
    gestion_locative_pct: float = 0.0
    tmi: float = 30.0
    revalorisation_bien_pct: float = 3.0
    revalorisation_loyer_pct: float = 0.75
    horizon_ans: int = 20
    rendement_scpi: float = 4.5
    taux_actualisation: float = 4.0
    stress_cashflow_factor: float = 0.85
    stress_terminal_factor: float = 0.90
    travaux_annuel: float = 0.0
    assurance_pno_annuel: float = 0.0
    cfe_annuel: float = 0.0
    honoraires_comptable_annuel: float = 0.0
    amort_frais_acq_annuel: float = 0.0


def mensualite_credit(capital: float, taux_annuel: float, duree_ans: int) -> float:
    if capital <= 0:
        return 0.0
    t = taux_annuel / 100 / 12
    n = duree_ans * 12
    if t == 0:
        return capital / n
    return capital * t / (1 - (1 + t) ** (-n))


def tableau_amortissement(capital: float, taux_annuel: float, duree_ans: int) -> List[Dict]:
    t = taux_annuel / 100 / 12
    n = duree_ans * 12
    m = mensualite_credit(capital, taux_annuel, duree_ans)
    rows = []
    cap = capital
    for _ in range(n):
        interets = cap * t
        amort = m - interets
        cap = max(0.0, cap - amort)
        rows.append({"interets": interets, "capital_restant": cap})
    return rows


def irr(cash_flows: List[float]) -> Optional[float]:
    if not cash_flows or cash_flows[0] >= 0:
        return None
    rate = 0.1
    for _ in range(1000):
        npv = sum(cf / (1 + rate) ** i for i, cf in enumerate(cash_flows))
        dnpv = sum(-i * cf / (1 + rate) ** (i + 1) for i, cf in enumerate(cash_flows))
        if dnpv == 0:
            break
        new_rate = rate - npv / dnpv
        if abs(new_rate - rate) < 1e-8:
            rate = new_rate
            break
        rate = new_rate
    return rate * 100 if -1 < rate < 10 else None


def npv(cash_flows: List[float], taux_actualisation_annuel: float) -> float:
    if not cash_flows:
        return 0.0
    r = taux_actualisation_annuel / 100
    return sum(cf / ((1 + r) ** i) for i, cf in enumerate(cash_flows))


def _compute_strategy_decision_metrics(
    initial_outlay: float,
    yearly_cashflows: List[float],
    terminal_addition: float,
    params: Params,
) -> Dict[str, Any]:
    discount_rate = params.taux_actualisation

    base_cf = [initial_outlay] + yearly_cashflows
    base_cf[-1] += terminal_addition
    van = npv(base_cf, discount_rate)

    stress_cf = [initial_outlay] + [cf * params.stress_cashflow_factor for cf in yearly_cashflows]
    stress_cf[-1] += terminal_addition * params.stress_terminal_factor
    stress_van = npv(stress_cf, discount_rate)

    coc_return = 0.0
    if initial_outlay < 0 and yearly_cashflows:
        coc_return = yearly_cashflows[0] / abs(initial_outlay) * 100

    return {
        "van": round(van),
        "discount_rate_used": round(discount_rate, 2),
        "coc_return_pct": round(coc_return, 2),
        "stress_van": round(stress_van),
        "stress_pass": stress_van > 0,
        "is_candidate": van > 0,
    }


def _dscr_an1(yearly: List[Dict[str, Any]], income_key: str) -> Optional[float]:
    if not yearly:
        return None
    row = yearly[0]
    mensualite_an = row.get("mensualite_an") or 0
    revenu = row.get(income_key) or 0
    if mensualite_an <= 0:
        return None
    return round(revenu / mensualite_an, 2)


def _interets_annuels(amort_table: List[Dict], an: int, duree_pret_ans: int) -> float:
    debut = (an - 1) * 12
    fin = min(an * 12, duree_pret_ans * 12)
    if debut >= len(amort_table):
        return 0.0
    return sum(row["interets"] for row in amort_table[debut:fin])


def _capital_restant(amort_table: List[Dict], an: int) -> float:
    idx = an * 12 - 1
    if idx < 0 or not amort_table:
        return 0.0
    return amort_table[min(idx, len(amort_table) - 1)]["capital_restant"]


def _compute_profitability_kpis(
    yearly: List[Dict[str, Any]],
    initial_cost: float,
    asset_base_value: Optional[float] = None,
) -> Dict[str, float]:
    if not yearly or initial_cost <= 0:
        return {
            "rentabilite_nette_locative_hors_revalo": 0.0,
            "rentabilite_nette_totale_avec_revalo": 0.0,
        }

    def row_income(row: Dict[str, Any]) -> float:
        revenu = float(row.get("loyer_annuel", row.get("loyer_economise", 0.0)) or 0.0)
        charges = float(row.get("charges", 0.0) or 0.0)
        impot = float(row.get("impot", 0.0) or 0.0)
        return revenu - charges - impot

    # Yearly-based KPI: use the last simulated year (not horizon-average)
    last_row = yearly[-1]
    locative_year = row_income(last_row)

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


def _attach_yearly_financing_kpis(
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


def _compute_period_net_profitability(
    yearly: List[Dict[str, Any]],
    initial_cost: float,
    final_net_asset_value: float,
) -> float:
    if not yearly or initial_cost <= 0:
        return 0.0
    cumulative_cash_flow = sum(float(row.get("cash_flow", 0.0) or 0.0) for row in yearly)
    total_gain = cumulative_cash_flow + final_net_asset_value - initial_cost
    return round(total_gain / initial_cost * 100, 2)


def _attach_yearly_profitability_kpis(
    yearly: List[Dict[str, Any]],
    initial_cost: float,
    asset_base_value: Optional[float] = None,
) -> None:
    if not yearly or initial_cost <= 0:
        for row in yearly:
            row["rentabilite_nette_locative_hors_revalo_pct"] = 0.0
            row["rentabilite_nette_totale_avec_revalo_pct"] = 0.0
        return

    def row_income(row: Dict[str, Any]) -> float:
        revenu = float(row.get("loyer_annuel", row.get("loyer_economise", 0.0)) or 0.0)
        charges = float(row.get("charges", 0.0) or 0.0)
        impot = float(row.get("impot", 0.0) or 0.0)
        return revenu - charges - impot

    prev_asset_value = asset_base_value
    for row in yearly:
        locative_year = row_income(row)

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


@app.post("/api/analyse")
def analyse(params: Params) -> Dict[str, Any]:
    prix_achat = params.prix_m2_achat * params.surface
    frais_notaire = prix_achat * params.frais_notaire_pct / 100
    cout_total = prix_achat + frais_notaire
    emprunt = max(0.0, cout_total - params.apport)

    mensualite = mensualite_credit(emprunt, params.taux_interet, params.duree_pret_ans)
    amort = tableau_amortissement(emprunt, params.taux_interet, params.duree_pret_ans)

    loyer_nu = params.loyer_m2 * params.surface
    taux_fiscal = (params.tmi + 17.2) / 100

    # ── Stratégie 1 : Location Nue (Régime Réel) ──────────────────────────
    def location_nue():
        yearly = []
        for an in range(1, params.horizon_ans + 1):
            coef_l = (1 + params.revalorisation_loyer_pct / 100) ** (an - 1)
            loyer = loyer_nu * 12 * coef_l * (1 - params.vacance_locative_pct / 100)
            interets = _interets_annuels(amort, an, params.duree_pret_ans)
            charges = params.charges_copro_mensuelle * 12
            tf = params.taxe_fonciere_mensuelle * 12
            gestion = loyer * params.gestion_locative_pct / 100

            revenu_foncier = loyer - interets - charges - tf - gestion
            if revenu_foncier > 0:
                impot = revenu_foncier * taux_fiscal
            else:
                # Déficit imputable sur revenu global (plafond 10 700 €)
                impot = -min(abs(revenu_foncier), 10700) * params.tmi / 100

            mensualite_an = mensualite * 12 if an <= params.duree_pret_ans else 0
            cf = loyer - mensualite_an - charges - tf - gestion - impot

            coef_b = (1 + params.revalorisation_bien_pct / 100) ** an
            valeur = prix_achat * coef_b
            cap_r = _capital_restant(amort, an)

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

        valeur_fin = prix_achat * (1 + params.revalorisation_bien_pct / 100) ** params.horizon_ans
        _attach_yearly_financing_kpis(yearly, cout_total, params.apport)
        _attach_yearly_profitability_kpis(yearly, cout_total, prix_achat)
        cf_tri = [-(params.apport + frais_notaire)] + [y["cash_flow"] for y in yearly]
        terminal_add = valeur_fin - yearly[-1]["capital_restant"]
        cf_tri[-1] += terminal_add
        tri = irr(cf_tri)
        decision = _compute_strategy_decision_metrics(
            initial_outlay=-(params.apport + frais_notaire),
            yearly_cashflows=[y["cash_flow"] for y in yearly],
            terminal_addition=terminal_add,
            params=params,
        )
        kpis = _compute_profitability_kpis(yearly, cout_total, prix_achat)
        rentabilite_period = _compute_period_net_profitability(yearly, cout_total, yearly[-1]["patrimoine_net"])

        return {
            "id": "location_nue",
            "nom": "Location Nue",
            "description": "Régime réel — déduction intérêts, charges et travaux. Déficit imputable sur revenu global (plafond 10 700 €/an).",
            "mensualite": round(mensualite),
            "loyer_mensuel": round(loyer_nu),
            "cash_flow_moyen": round(sum(y["cash_flow"] for y in yearly) / len(yearly) / 12),
            "patrimoine_net_final": yearly[-1]["patrimoine_net"],
            "tri": round(tri, 2) if tri else None,
            "van": decision["van"],
            "discount_rate_used": decision["discount_rate_used"],
            "dscr": _dscr_an1(yearly, "loyer_annuel"),
            "coc_return_pct": decision["coc_return_pct"],
            "stress_van": decision["stress_van"],
            "stress_pass": decision["stress_pass"],
            "is_candidate": decision["is_candidate"],
            "rendement_brut": round(loyer_nu * 12 / prix_achat * 100, 2),
            "rentabilite_nette_sur_periode": rentabilite_period,
            "rentabilite_nette_locative_hors_revalo": kpis["rentabilite_nette_locative_hors_revalo"],
            "rentabilite_nette_totale_avec_revalo": kpis["rentabilite_nette_totale_avec_revalo"],
            "yearly": yearly,
        }

    # ── Stratégie 2 : LMNP Meublé (Régime Réel) ───────────────────────────
    def lmnp_meuble():
        mobilier = prix_achat * 0.12
        amort_bien_an = prix_achat * 0.80 / 30
        loyer_meuble = params.loyer_meuble_m2 * params.surface

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
            interets = _interets_annuels(amort, an, params.duree_pret_ans)
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

            impot = bic_net_imposable * taux_fiscal

            mensualite_an = mensualite * 12 if an <= params.duree_pret_ans else 0
            cf = loyer - mensualite_an - charges_exploitation - impot

            coef_b = (1 + params.revalorisation_bien_pct / 100) ** an
            valeur = prix_achat * coef_b
            cap_r = _capital_restant(amort, an)

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

        valeur_fin = prix_achat * (1 + params.revalorisation_bien_pct / 100) ** params.horizon_ans
        _attach_yearly_financing_kpis(yearly, cout_total + mobilier, params.apport)
        _attach_yearly_profitability_kpis(yearly, cout_total, prix_achat)
        cf_tri = [-(params.apport + frais_notaire + mobilier)] + [y["cash_flow"] for y in yearly]
        terminal_add = valeur_fin - yearly[-1]["capital_restant"]
        cf_tri[-1] += terminal_add
        tri = irr(cf_tri)
        decision = _compute_strategy_decision_metrics(
            initial_outlay=-(params.apport + frais_notaire + mobilier),
            yearly_cashflows=[y["cash_flow"] for y in yearly],
            terminal_addition=terminal_add,
            params=params,
        )
        kpis = _compute_profitability_kpis(yearly, cout_total, prix_achat)
        rentabilite_period = _compute_period_net_profitability(yearly, cout_total + mobilier, yearly[-1]["patrimoine_net"])

        return {
            "id": "lmnp_meuble",
            "nom": "LMNP Meublé",
            "description": "BIC régime réel — amortissement du bien (30 ans) et du mobilier (7 ans). Fiscalité quasi nulle pendant ~15 ans.",
            "mensualite": round(mensualite),
            "loyer_mensuel": round(loyer_meuble),
            "cash_flow_moyen": round(sum(y["cash_flow"] for y in yearly) / len(yearly) / 12),
            "patrimoine_net_final": yearly[-1]["patrimoine_net"],
            "tri": round(tri, 2) if tri else None,
            "van": decision["van"],
            "discount_rate_used": decision["discount_rate_used"],
            "dscr": _dscr_an1(yearly, "loyer_annuel"),
            "coc_return_pct": decision["coc_return_pct"],
            "stress_van": decision["stress_van"],
            "stress_pass": decision["stress_pass"],
            "is_candidate": decision["is_candidate"],
            "rendement_brut": round(loyer_meuble * 12 / prix_achat * 100, 2),
            "rentabilite_nette_sur_periode": rentabilite_period,
            "rentabilite_nette_locative_hors_revalo": kpis["rentabilite_nette_locative_hors_revalo"],
            "rentabilite_nette_totale_avec_revalo": kpis["rentabilite_nette_totale_avec_revalo"],
            "yearly": yearly,
        }

    # ── Stratégie 3 : Airbnb / Location Courte Durée ──────────────────────
    def airbnb():
        mobilier = 20000
        taux_occupation = 0.70
        revenu_nuitee = loyer_nu * 2.8
        revenu_mensuel = revenu_nuitee * taux_occupation
        frais_plateforme_pct = 0.15
        frais_conciergerie_pct = 0.20
        amort_bien_an = prix_achat * 0.80 / 30

        yearly = []
        for an in range(1, params.horizon_ans + 1):
            coef_l = (1 + params.revalorisation_loyer_pct / 100) ** (an - 1)
            revenu = revenu_mensuel * 12 * coef_l
            interets = _interets_annuels(amort, an, params.duree_pret_ans)
            charges = params.charges_copro_mensuelle * 12
            tf = params.taxe_fonciere_mensuelle * 12
            plateforme = revenu * frais_plateforme_pct
            conciergerie = revenu * frais_conciergerie_pct
            menage = 150 * 12
            amort_mob = mobilier / 7 if an <= 7 else 0

            bic = revenu - interets - charges - tf - plateforme - conciergerie - menage - amort_bien_an - amort_mob
            impot = max(0, bic) * taux_fiscal

            mensualite_an = mensualite * 12 if an <= params.duree_pret_ans else 0
            cf = revenu - mensualite_an - charges - tf - plateforme - conciergerie - menage - impot

            coef_b = (1 + params.revalorisation_bien_pct / 100) ** an
            valeur = prix_achat * coef_b
            cap_r = _capital_restant(amort, an)

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

        valeur_fin = prix_achat * (1 + params.revalorisation_bien_pct / 100) ** params.horizon_ans
        _attach_yearly_financing_kpis(yearly, cout_total + mobilier, params.apport)
        _attach_yearly_profitability_kpis(yearly, cout_total, prix_achat)
        cf_tri = [-(params.apport + frais_notaire + mobilier)] + [y["cash_flow"] for y in yearly]
        terminal_add = valeur_fin - yearly[-1]["capital_restant"]
        cf_tri[-1] += terminal_add
        tri = irr(cf_tri)
        decision = _compute_strategy_decision_metrics(
            initial_outlay=-(params.apport + frais_notaire + mobilier),
            yearly_cashflows=[y["cash_flow"] for y in yearly],
            terminal_addition=terminal_add,
            params=params,
        )
        kpis = _compute_profitability_kpis(yearly, cout_total, prix_achat)
        rentabilite_period = _compute_period_net_profitability(yearly, cout_total + mobilier, yearly[-1]["patrimoine_net"])

        return {
            "id": "airbnb",
            "nom": "Location Courte Durée",
            "description": "Airbnb / saisonnier — revenus ×2,8 mais frais plateforme (15 %), conciergerie (20 %) et ménage. Risque réglementaire élevé à Paris.",
            "mensualite": round(mensualite),
            "loyer_mensuel": round(revenu_mensuel),
            "cash_flow_moyen": round(sum(y["cash_flow"] for y in yearly) / len(yearly) / 12),
            "patrimoine_net_final": yearly[-1]["patrimoine_net"],
            "tri": round(tri, 2) if tri else None,
            "van": decision["van"],
            "discount_rate_used": decision["discount_rate_used"],
            "dscr": _dscr_an1(yearly, "loyer_annuel"),
            "coc_return_pct": decision["coc_return_pct"],
            "stress_van": decision["stress_van"],
            "stress_pass": decision["stress_pass"],
            "is_candidate": decision["is_candidate"],
            "rendement_brut": round(revenu_mensuel * 12 / prix_achat * 100, 2),
            "rentabilite_nette_sur_periode": rentabilite_period,
            "rentabilite_nette_locative_hors_revalo": kpis["rentabilite_nette_locative_hors_revalo"],
            "rentabilite_nette_totale_avec_revalo": kpis["rentabilite_nette_totale_avec_revalo"],
            "yearly": yearly,
        }

    # ── Stratégie 4 : SCPI (sans effet de levier) ─────────────────────────
    def scpi():
        frais_entree = 0.09
        capital_net = params.apport * (1 - frais_entree)
        rendement = params.rendement_scpi / 100
        revalorisation_parts = 0.01

        yearly = []
        valeur_parts = capital_net

        for an in range(1, params.horizon_ans + 1):
            revenu = valeur_parts * rendement
            impot = revenu * taux_fiscal
            cf = revenu - impot
            valeur_parts = valeur_parts * (1 + revalorisation_parts)

            yearly.append({
                "annee": an,
                "loyer_annuel": round(revenu),
                "impot": round(impot),
                "cash_flow": round(cf),
                "patrimoine_net": round(valeur_parts),
            })

        _attach_yearly_financing_kpis(yearly, params.apport, params.apport)
        _attach_yearly_profitability_kpis(yearly, params.apport, capital_net)
        cf_tri = [-params.apport] + [y["cash_flow"] for y in yearly]
        terminal_add = yearly[-1]["patrimoine_net"]
        cf_tri[-1] += terminal_add
        tri = irr(cf_tri)
        decision = _compute_strategy_decision_metrics(
            initial_outlay=-params.apport,
            yearly_cashflows=[y["cash_flow"] for y in yearly],
            terminal_addition=terminal_add,
            params=params,
        )
        kpis = _compute_profitability_kpis(yearly, params.apport, capital_net)
        rentabilite_period = _compute_period_net_profitability(yearly, params.apport, yearly[-1]["patrimoine_net"])

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
            "discount_rate_used": decision["discount_rate_used"],
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

    # ── Stratégie 5 : Résidence Principale ────────────────────────────────
    def residence_principale():
        yearly = []
        for an in range(1, params.horizon_ans + 1):
            coef_l = (1 + params.revalorisation_loyer_pct / 100) ** (an - 1)
            loyer_eco = loyer_nu * 12 * coef_l  # loyer qu'on n'aurait plus à payer
            charges = params.charges_copro_mensuelle * 12
            tf = params.taxe_fonciere_mensuelle * 12
            mensualite_an = mensualite * 12 if an <= params.duree_pret_ans else 0
            # Cash flow différentiel vs locataire
            cf = loyer_eco - mensualite_an - charges - tf

            coef_b = (1 + params.revalorisation_bien_pct / 100) ** an
            valeur = prix_achat * coef_b
            cap_r = _capital_restant(amort, an)

            yearly.append({
                "annee": an,
                "loyer_economise": round(loyer_eco),
                "charges": round(charges + tf),
                "mensualite_an": round(mensualite_an),
                "cash_flow": round(cf),
                "valeur_bien": round(valeur),
                "capital_restant": round(cap_r),
                "patrimoine_net": round(valeur - cap_r),
            })

        valeur_fin = prix_achat * (1 + params.revalorisation_bien_pct / 100) ** params.horizon_ans
        _attach_yearly_financing_kpis(yearly, cout_total, params.apport)
        _attach_yearly_profitability_kpis(yearly, cout_total, prix_achat)
        # Plus-value exonérée pour résidence principale
        cf_tri = [-(params.apport + frais_notaire)] + [y["cash_flow"] for y in yearly]
        terminal_add = valeur_fin
        cf_tri[-1] += terminal_add
        tri = irr(cf_tri)
        decision = _compute_strategy_decision_metrics(
            initial_outlay=-(params.apport + frais_notaire),
            yearly_cashflows=[y["cash_flow"] for y in yearly],
            terminal_addition=terminal_add,
            params=params,
        )
        kpis = _compute_profitability_kpis(yearly, cout_total, prix_achat)
        rentabilite_period = _compute_period_net_profitability(yearly, cout_total, yearly[-1]["patrimoine_net"])

        return {
            "id": "residence_principale",
            "nom": "Résidence Principale",
            "description": "Achat RP — économie de loyer, exonération totale de plus-value à la revente. Pas de revenus locatifs.",
            "mensualite": round(mensualite),
            "loyer_mensuel": 0,
            "cash_flow_moyen": round(sum(y["cash_flow"] for y in yearly) / len(yearly) / 12),
            "patrimoine_net_final": yearly[-1]["patrimoine_net"],
            "tri": round(tri, 2) if tri else None,
            "van": decision["van"],
            "discount_rate_used": decision["discount_rate_used"],
            "dscr": _dscr_an1(yearly, "loyer_economise"),
            "coc_return_pct": decision["coc_return_pct"],
            "stress_van": decision["stress_van"],
            "stress_pass": decision["stress_pass"],
            "is_candidate": decision["is_candidate"],
            "rendement_brut": 0,
            "rentabilite_nette_sur_periode": rentabilite_period,
            "rentabilite_nette_locative_hors_revalo": kpis["rentabilite_nette_locative_hors_revalo"],
            "rentabilite_nette_totale_avec_revalo": kpis["rentabilite_nette_totale_avec_revalo"],
            "yearly": yearly,
        }

    strategies = [
        location_nue(),
        lmnp_meuble(),
        airbnb(),
        scpi(),
        residence_principale(),
    ]

    candidates = [s for s in strategies if s.get("is_candidate")]
    pool = candidates if candidates else strategies
    best = max(pool, key=lambda s: s.get("van", float("-inf"))) if pool else None
    for s in strategies:
        s["is_recommended"] = best is not None and s["id"] == best["id"]

    return {
        "resume": {
            "prix_achat": round(prix_achat),
            "frais_notaire": round(frais_notaire),
            "cout_total": round(cout_total),
            "emprunt": round(emprunt),
            "mensualite": round(mensualite),
            "loyer_mensuel_brut": round(loyer_nu),
            "rendement_brut_nu": round(loyer_nu * 12 / prix_achat * 100, 2),
        },
        "strategies": strategies,
    }


@app.get("/api/health")
def health():
    return {"status": "ok"}
