from typing import Optional

from pydantic import BaseModel, Field


class Params(BaseModel):
    # Defaults mirror frontend/app/page.tsx DEFAULT_PARAMS — keep both in sync.
    apport: float = Field(250000, ge=0)
    taux_interet: float = Field(3.3, ge=0, le=30)
    taux_assurance: float = Field(0.36, ge=0, le=5)
    revenu_mensuel_brut: float = Field(7000, ge=0)
    prix_m2_achat: float = Field(11500, gt=0)
    loyer_m2: float = Field(43, gt=0)
    # Furnished (meuble) rent rate. Falls back to loyer_m2 * 1.15 when omitted,
    # preserving the previous single-rate behavior.
    loyer_m2_meuble: Optional[float] = Field(None, gt=0)
    surface: float = Field(20, gt=0)
    duree_pret_ans: int = Field(10, gt=0, le=40)
    frais_notaire_pct: float = Field(8, ge=0, le=20)
    frais_dossier: float = Field(0.0, ge=0)
    frais_garantie: float = Field(0.0, ge=0)
    charges_copro_mensuelle: float = Field(150, ge=0)
    taxe_fonciere_mensuelle: float = Field(125, ge=0)
    vacance_locative_pct: float = Field(5.0, ge=0, le=100)
    gestion_locative_pct: float = Field(0.0, ge=0, le=100)
    tmi: float = Field(30.0, ge=0, le=100)
    revalorisation_bien_pct: float = Field(3.5, ge=-20, le=50)
    revalorisation_loyer_pct: float = Field(0.5, ge=-20, le=50)
    horizon_ans: int = Field(20, gt=0, le=60)
    rendement_scpi: float = Field(4, ge=0, le=50)
    # Fixed VAN discount rate, overriding the CAPM+Hamada ke by default — ke is
    # highly leverage-sensitive (see ANALYSE_METHODOLOGY.md) and can produce
    # unrealistic hurdle rates at typical mortgage LTVs. Still overridable per run.
    taux_actualisation: Optional[float] = Field(5.0, ge=0, le=50)
    taux_sans_risque: float = Field(1.6, ge=0, le=20)
    prime_risque_marche: float = Field(5.0, ge=0, le=20)
    beta_u_location_nue: float = Field(0.70, ge=0, le=3)
    beta_u_lmnp: float = Field(0.85, ge=0, le=3)
    beta_u_airbnb: float = Field(1.05, ge=0, le=3)
    beta_u_scpi: float = Field(0.60, ge=0, le=3)
    beta_u_residence_principale: float = Field(0.55, ge=0, le=3)
    stress_cashflow_factor: float = Field(0.85, ge=0, le=1)
    stress_terminal_factor: float = Field(0.90, ge=0, le=1)
    travaux_annuel: float = Field(0.0, ge=0)
    assurance_pno_annuel: float = Field(0.0, ge=0)
    cfe_annuel: float = Field(0.0, ge=0)
    honoraires_comptable_annuel: float = Field(0.0, ge=0)
    amort_frais_acq_annuel: float = Field(0.0, ge=0)
