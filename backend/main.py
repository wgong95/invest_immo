from typing import Any, Dict, List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.analyse import run_analyse
from app.loan import LoanOffer, compare_loan_offers
from app.models import Params

app = FastAPI(title="Invest Immo Analyser")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/analyse")
def analyse(params: Params) -> Dict[str, Any]:
    return run_analyse(params)


@app.post("/api/compare-loans")
def compare_loans(offers: List[LoanOffer]) -> List[Dict[str, Any]]:
    return compare_loan_offers(offers)


@app.get("/api/health")
def health():
    return {"status": "ok"}
