from dataclasses import dataclass
from typing import Dict, List, Optional

from .finance import calcul_taeg, mensualite_credit, tableau_amortissement
from .models import Params


@dataclass
class EngineContext:
    params: Params
    prix_achat: float
    frais_notaire: float
    frais_annexes: float
    cout_total: float
    emprunt: float
    mensualite: float
    mensualite_assurance: float
    cout_assurance_total: float
    taeg: Optional[float]
    amort: List[Dict[str, float]]
    interets_totaux: float
    loyer_nu: float
    loyer_meuble: float
    taux_fiscal: float
    hamada_tax_rate: float
    mobilier: float


def build_context(params: Params) -> EngineContext:
    prix_achat = params.prix_m2_achat * params.surface
    frais_notaire = prix_achat * params.frais_notaire_pct / 100
    frais_annexes = params.frais_dossier + params.frais_garantie
    cout_total = prix_achat + frais_notaire + frais_annexes
    emprunt = max(0.0, cout_total - params.apport)

    mensualite = mensualite_credit(emprunt, params.taux_interet, params.duree_pret_ans)
    amort = tableau_amortissement(emprunt, params.taux_interet, params.duree_pret_ans)
    interets_totaux = sum(row["interets"] for row in amort)

    duree_mois = params.duree_pret_ans * 12
    mensualite_assurance = emprunt * params.taux_assurance / 100 / 12
    cout_assurance_total = mensualite_assurance * duree_mois
    taeg = calcul_taeg(
        emprunt=emprunt,
        mensualite=mensualite,
        mensualite_assurance=mensualite_assurance,
        duree_mois=duree_mois,
        frais_annexes=frais_annexes,
    )

    loyer_nu = params.loyer_m2 * params.surface
    loyer_m2_meuble = params.loyer_m2_meuble if params.loyer_m2_meuble is not None else params.loyer_m2 * 1.15
    loyer_meuble = loyer_m2_meuble * params.surface
    taux_fiscal = (params.tmi + 17.2) / 100
    hamada_tax_rate = min(max(params.tmi / 100, 0.0), 0.45)

    # Furniture allowance, unified across LMNP and short-term rental strategies.
    mobilier = prix_achat * 0.12

    return EngineContext(
        params=params,
        prix_achat=prix_achat,
        frais_notaire=frais_notaire,
        frais_annexes=frais_annexes,
        cout_total=cout_total,
        emprunt=emprunt,
        mensualite=mensualite,
        mensualite_assurance=mensualite_assurance,
        cout_assurance_total=cout_assurance_total,
        taeg=taeg,
        amort=amort,
        interets_totaux=interets_totaux,
        loyer_nu=loyer_nu,
        loyer_meuble=loyer_meuble,
        taux_fiscal=taux_fiscal,
        hamada_tax_rate=hamada_tax_rate,
        mobilier=mobilier,
    )
