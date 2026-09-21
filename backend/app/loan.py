from typing import Any, Dict, List

from pydantic import BaseModel, Field

from .finance import calcul_taeg, mensualite_credit, tableau_amortissement


class LoanOffer(BaseModel):
    id: str
    nom: str
    montant_emprunte: float = Field(..., gt=0)
    taux_interet: float = Field(..., ge=0, le=30)
    taux_assurance: float = Field(0.0, ge=0, le=5)
    duree_pret_ans: int = Field(..., gt=0, le=40)
    frais_dossier: float = Field(0.0, ge=0)
    frais_garantie: float = Field(0.0, ge=0)


def compute_loan_offer(offer: LoanOffer) -> Dict[str, Any]:
    mensualite = mensualite_credit(offer.montant_emprunte, offer.taux_interet, offer.duree_pret_ans)
    amort = tableau_amortissement(offer.montant_emprunte, offer.taux_interet, offer.duree_pret_ans)
    interets_totaux = sum(row["interets"] for row in amort)

    duree_mois = offer.duree_pret_ans * 12
    mensualite_assurance = offer.montant_emprunte * offer.taux_assurance / 100 / 12
    cout_assurance_total = mensualite_assurance * duree_mois
    frais_annexes = offer.frais_dossier + offer.frais_garantie

    taeg = calcul_taeg(
        emprunt=offer.montant_emprunte,
        mensualite=mensualite,
        mensualite_assurance=mensualite_assurance,
        duree_mois=duree_mois,
        frais_annexes=frais_annexes,
    )

    cout_total_credit = interets_totaux + cout_assurance_total + frais_annexes

    return {
        "id": offer.id,
        "nom": offer.nom,
        "mensualite": round(mensualite, 2),
        "mensualite_assurance": round(mensualite_assurance, 2),
        "mensualite_totale": round(mensualite + mensualite_assurance, 2),
        "interets_totaux": round(interets_totaux),
        "cout_assurance_total": round(cout_assurance_total),
        "frais_annexes": round(frais_annexes),
        "cout_total_credit": round(cout_total_credit),
        "taeg": taeg,
    }


def compare_loan_offers(offers: List[LoanOffer]) -> List[Dict[str, Any]]:
    return [compute_loan_offer(offer) for offer in offers]
