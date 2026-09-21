from typing import Dict, List, Optional


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


def interets_annuels(amort_table: List[Dict], an: int, duree_pret_ans: int) -> float:
    debut = (an - 1) * 12
    fin = min(an * 12, duree_pret_ans * 12)
    if debut >= len(amort_table):
        return 0.0
    return sum(row["interets"] for row in amort_table[debut:fin])


def capital_restant(amort_table: List[Dict], an: int) -> float:
    idx = an * 12 - 1
    if idx < 0 or not amort_table:
        return 0.0
    return amort_table[min(idx, len(amort_table) - 1)]["capital_restant"]


def irr(cash_flows: List[float]) -> Optional[float]:
    if not cash_flows or cash_flows[0] >= 0:
        return None
    rate = 0.1
    for _ in range(1000):
        npv_val = sum(cf / (1 + rate) ** i for i, cf in enumerate(cash_flows))
        dnpv = sum(-i * cf / (1 + rate) ** (i + 1) for i, cf in enumerate(cash_flows))
        if dnpv == 0:
            break
        new_rate = rate - npv_val / dnpv
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


def calcul_taeg(
    emprunt: float,
    mensualite: float,
    mensualite_assurance: float,
    duree_mois: int,
    frais_annexes: float,
) -> Optional[float]:
    """Actuarial TAEG (taux annuel effectif global) on the loan, per the
    French method: solve the monthly rate equating the net amount disbursed
    (loan minus upfront fees) with the discounted insured monthly payments,
    then annualize as a compound rate."""
    capital_net = emprunt - frais_annexes
    mensualite_totale = mensualite + mensualite_assurance
    if capital_net <= 0 or duree_mois <= 0 or mensualite_totale <= 0:
        return None

    cash_flows = [capital_net] + [-mensualite_totale] * duree_mois
    rate = 0.01
    for _ in range(1000):
        npv_val = sum(cf / (1 + rate) ** i for i, cf in enumerate(cash_flows))
        dnpv = sum(-i * cf / (1 + rate) ** (i + 1) for i, cf in enumerate(cash_flows))
        if dnpv == 0:
            break
        new_rate = rate - npv_val / dnpv
        if abs(new_rate - rate) < 1e-10:
            rate = new_rate
            break
        rate = new_rate

    if rate <= -1:
        return None
    return round(((1 + rate) ** 12 - 1) * 100, 2)


def compute_ke_hamada_capm(
    beta_u: float,
    debt: float,
    equity: float,
    tax_rate: float,
    risk_free_rate: float,
    market_risk_premium: float,
) -> Dict[str, float]:
    e = max(equity, 1.0)
    d_e = max(0.0, debt) / e
    t = min(max(tax_rate, 0.0), 0.45)
    beta_l = beta_u * (1 + (1 - t) * d_e)
    ke = risk_free_rate + beta_l * market_risk_premium
    return {
        "beta_u": round(beta_u, 4),
        "beta_l": round(beta_l, 4),
        "ke": round(ke, 2),
    }
