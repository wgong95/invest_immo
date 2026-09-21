from app.models import Params

# Source of truth: frontend/app/page.tsx DEFAULT_PARAMS.
# Keep this dict and that object in sync — this test exists to catch drift.
FRONTEND_DEFAULTS = {
    "apport": 250000,
    "taux_interet": 3.3,
    "taux_assurance": 0.36,
    "revenu_mensuel_brut": 7000,
    "prix_m2_achat": 11500,
    "loyer_m2": 43,
    "surface": 20,
    "duree_pret_ans": 10,
    "frais_notaire_pct": 8.0,
    "charges_copro_mensuelle": 150,
    "taxe_fonciere_mensuelle": 125,
    "vacance_locative_pct": 5,
    "gestion_locative_pct": 0,
    "tmi": 30,
    "revalorisation_bien_pct": 3.5,
    "revalorisation_loyer_pct": 0.5,
    "horizon_ans": 20,
    "rendement_scpi": 4,
    "taux_actualisation": 5,
}


def test_backend_defaults_match_frontend_defaults():
    params = Params()
    for field, expected in FRONTEND_DEFAULTS.items():
        actual = getattr(params, field)
        assert actual == expected, f"{field} drifted: backend={actual} frontend={expected}"
