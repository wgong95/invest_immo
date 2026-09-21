from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

EXPECTED_STRATEGY_IDS = {"location_nue", "lmnp_meuble", "airbnb", "scpi", "residence_principale"}


def test_health():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_analyse_default_params():
    resp = client.post("/api/analyse", json={})
    assert resp.status_code == 200
    data = resp.json()
    assert "resume" in data
    ids = {s["id"] for s in data["strategies"]}
    assert ids == EXPECTED_STRATEGY_IDS
    assert sum(s["is_recommended"] for s in data["strategies"]) == 1
    assert all("dscr" in s for s in data["strategies"])
    scpi = next(s for s in data["strategies"] if s["id"] == "scpi")
    assert scpi["dscr"] is None


def test_analyse_rejects_zero_surface():
    resp = client.post("/api/analyse", json={"surface": 0})
    assert resp.status_code == 422


def test_analyse_rejects_zero_horizon():
    resp = client.post("/api/analyse", json={"horizon_ans": 0})
    assert resp.status_code == 422


def test_analyse_rejects_zero_loan_duration():
    resp = client.post("/api/analyse", json={"duree_pret_ans": 0})
    assert resp.status_code == 422


def test_analyse_accepts_valid_override():
    resp = client.post("/api/analyse", json={"apport": 100000, "horizon_ans": 10})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["strategies"][0]["yearly"]) == 10


def test_compare_loans_returns_result_per_offer():
    resp = client.post(
        "/api/compare-loans",
        json=[
            {
                "id": "a",
                "nom": "Banque A",
                "montant_emprunte": 177478,
                "taux_interet": 3.36,
                "taux_assurance": 0.17,
                "duree_pret_ans": 20,
                "frais_dossier": 887.83,
                "frais_garantie": 2590.33,
            },
            {
                "id": "b",
                "nom": "Banque B",
                "montant_emprunte": 177478,
                "taux_interet": 3.2,
                "taux_assurance": 0.25,
                "duree_pret_ans": 20,
            },
        ],
    )
    assert resp.status_code == 200
    data = resp.json()
    assert [r["id"] for r in data] == ["a", "b"]
    assert all(r["taeg"] is not None for r in data)


def test_compare_loans_rejects_invalid_offer():
    resp = client.post("/api/compare-loans", json=[{"id": "a", "nom": "Banque A", "montant_emprunte": 0, "taux_interet": 3, "duree_pret_ans": 20}])
    assert resp.status_code == 422
