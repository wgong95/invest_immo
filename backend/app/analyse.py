from typing import Any, Dict

from .context import build_context
from .models import Params
from .strategies import airbnb, lmnp, location_nue, residence_principale, scpi


def run_analyse(params: Params) -> Dict[str, Any]:
    ctx = build_context(params)

    strategies = [
        location_nue.compute(ctx),
        lmnp.compute(ctx),
        airbnb.compute(ctx),
        scpi.compute(ctx),
        residence_principale.compute(ctx),
    ]

    candidates = [s for s in strategies if s.get("is_candidate")]
    pool = candidates if candidates else strategies
    best = max(pool, key=lambda s: s.get("van", float("-inf"))) if pool else None
    for s in strategies:
        s["is_recommended"] = best is not None and s["id"] == best["id"]

    return {
        "resume": {
            "prix_achat": round(ctx.prix_achat),
            "frais_notaire": round(ctx.frais_notaire),
            "frais_dossier": round(params.frais_dossier),
            "frais_garantie": round(params.frais_garantie),
            "cout_total": round(ctx.cout_total),
            "emprunt": round(ctx.emprunt),
            "mensualite": round(ctx.mensualite),
            "mensualite_assurance": round(ctx.mensualite_assurance),
            "cout_assurance_total": round(ctx.cout_assurance_total),
            "taeg": ctx.taeg,
            "interets_totaux": round(ctx.interets_totaux),
            "loyer_mensuel_brut": round(ctx.loyer_nu),
            "rendement_brut_nu": round(ctx.loyer_nu * 12 / ctx.prix_achat * 100, 2),
        },
        "strategies": strategies,
    }
