# Invest Immo

A real-estate investment analysis app for comparing multiple ownership strategies
across multiple properties, using French tax and financing rules.

## What It Does

- Compare up to 4 properties side by side
- Evaluate 5 ownership strategies for each property:
  - **Location Nue** — unfurnished long-term rental (régime réel foncier)
  - **LMNP Meublé** — furnished long-term rental (BIC régime réel)
  - **Location Courte Durée** — Airbnb-style short-term rental
  - **SCPI** — unleveraged "paper real estate" fund, as a benchmark alternative
  - **Résidence Principale** — buying to live in (avoided-rent economics)
- Simulate yearly cash flow, taxation, loan amortization, and net wealth over a
  configurable horizon (default 20 years)
- Score each strategy with decision metrics — TRI, VAN, ke, TRI − ke, Cash-on-Cash
  return, stress-tested VAN — and flag the recommended one
- Export a run to PDF / Excel, and import/export per-property configs as JSON

The full mathematical specification — every formula, every strategy's fiscal
pipeline, every output indicator — lives in
[ANALYSE_METHODOLOGY.md](ANALYSE_METHODOLOGY.md). This file covers the app's
shape: what runs where, and how a request flows through it.

## How It's Built

### Data flow

```
Browser (Next.js)
  ParamPanel / FlatComparePanel  →  Params (+ per-flat overrides)
        │
        ▼  POST /api/analyse  (one call per enabled flat, up to 4 in parallel)
FastAPI (backend/main.py)
        │
        ▼
run_analyse(params)                     backend/app/analyse.py
        │
        ├─ build_context(params)        backend/app/context.py
        │     → loan amortization table, purchase cost, shared tax rate,
        │       unified furniture allowance ("mobilier")
        │
        ├─ 5× strategy.compute(ctx)     backend/app/strategies/*.py
        │     → yearly rows + TRI/VAN/ke/stress metrics per strategy
        │
        └─ pick the strategy with the highest positive VAN → is_recommended
        │
        ▼  AnalyseResult { resume, strategies[] }
Browser renders StrategyCards, PatrimoineChart, CashFlowChart, DetailTable
```

There is no database — every run is a pure computation from the posted
`Params` to a JSON response. "Saving a flat" is just exporting/importing that
JSON on the client.

### Backend (`backend/`)

FastAPI + Pydantic, organized as one module per responsibility so each piece is
independently testable:

| Module | Responsibility |
|---|---|
| `main.py` | FastAPI app, CORS, the two HTTP routes (`/api/analyse`, `/api/health`) |
| `app/models.py` | `Params` — every input field, its default, and its validation bounds |
| `app/finance.py` | Pure numeric primitives: loan annuity, amortization table, IRR (Newton-Raphson), NPV, CAPM/Hamada cost of equity |
| `app/context.py` | `build_context()` — computes the values every strategy shares once per request (purchase price, loan schedule, tax rate, furniture allowance) into an `EngineContext` |
| `app/kpis.py` | Post-processing shared by all strategies: decision metrics (VAN/ke/stress-VAN/CoC), per-year and per-period profitability ratios |
| `app/strategies/*.py` | One file per strategy (`location_nue`, `lmnp`, `airbnb`, `scpi`, `residence_principale`), each exposing `compute(ctx) -> dict` |
| `app/analyse.py` | Orchestrator: runs all 5 strategies against one `EngineContext`, picks the recommendation, assembles the response |
| `tests/` | pytest suite — finance primitives, KPI helpers, each strategy, input validation, default-drift guard, and the HTTP endpoints |

### Frontend (`frontend/`)

Next.js 14 (App Router) + TypeScript + Tailwind, single page, no routing:

| File | Responsibility |
|---|---|
| `app/page.tsx` | Page state: `Params`, up to 4 `FlatConfig`s, calls the API once per enabled flat, holds the active flat/strategy selection |
| `components/ParamPanel.tsx` | Shared assumptions form (financing, charges, market hypotheses, discount rate) |
| `components/FlatComparePanel.tsx` | Per-property overrides (price, rent, surface, fees) for up to 4 flats; JSON import/export |
| `components/StrategyCards.tsx` | One card per strategy: TRI, VAN, ke, stress-VAN, recommendation badge |
| `components/PatrimoineChart.tsx` / `CashFlowChart.tsx` | Recharts visualizations of net wealth and cash flow over the horizon |
| `components/DetailTable.tsx` | Full yearly breakdown for the selected strategy |
| `components/ResumeBar.tsx` | Purchase price / loan / monthly payment summary strip |
| `components/FlatComparisonSummary.tsx` | Compact side-by-side table across all enabled flats |
| `lib/api.ts` | Thin `fetch` wrapper to `POST /api/analyse` |
| `lib/types.ts` | TypeScript mirror of the backend's `Params` / response shapes |
| `lib/report.ts` | PDF / Excel export of a comparison run |

## Repository Structure

```
backend/
  main.py                    FastAPI app + routes
  app/
    models.py                Params (inputs, defaults, validation)
    finance.py                loan math, IRR, NPV, CAPM/Hamada
    context.py                EngineContext shared by all strategies
    kpis.py                   decision metrics & profitability KPIs
    strategies/
      location_nue.py
      lmnp.py
      airbnb.py
      scpi.py
      residence_principale.py
    analyse.py                orchestrator: run_analyse(params)
  tests/                      pytest suite
  requirements.txt            runtime deps
  requirements-dev.txt        + pytest, httpx
  Dockerfile
frontend/
  app/page.tsx                single page, top-level state
  components/                 param forms, cards, charts, tables
  lib/                        api client, types, PDF/Excel export
  Dockerfile
flat_*.json                   example saved property configs (import via UI)
docker-compose.yml             local container orchestration
DOCKER.md                      Docker usage notes
ANALYSE_METHODOLOGY.md         full mathematical specification
start.sh                       legacy local startup script
```

## Prerequisites

- Node.js 20+
- Python 3.11+ (backend deps currently fail to build on 3.14 — use 3.11–3.13)
- npm
- (Optional) Docker Desktop

## Run Locally (without Docker)

### 1) Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Backend tests

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

### 2) Frontend

```bash
cd frontend
npm install
npm run dev
```

Open:

- Frontend: http://localhost:3000
- Backend: http://localhost:8000

## Run with Docker

```bash
docker compose up --build
```

Open:

- Frontend: http://localhost:3000
- Backend: http://localhost:8000

Stop:

```bash
docker compose down
```

## API

### Health

- `GET /api/health`

### Analysis

- `POST /api/analyse`
- Body: `Params` object (see `backend/app/models.py` and `frontend/lib/types.ts`)
- Returns: `{ resume, strategies[] }` — see [ANALYSE_METHODOLOGY.md](ANALYSE_METHODOLOGY.md) for every field's definition
- Invalid input (e.g. `surface <= 0`, `horizon_ans <= 0`) returns `422` instead of crashing

## Key Financial Metrics

- **TRI**: annualized internal rate of return from the project's equity cash-flow timeline (Newton-Raphson).
- **VAN**: net present value of that same cash-flow timeline, discounted at `taux_actualisation` (defaults to 5%).
- **ke (Hamada + CAPM)**: strategy-specific cost of equity — shown as a risk indicator, not the default discount rate (see Notes).
- **TRI − ke**: spread between the project's actual return and its CAPM-implied cost of equity.
- **CoC Return**: first-year cash return on the initial equity outlay.
- **Stress VAN**: downside NPV under reduced cash flow and terminal value factors.

Full formulas and per-strategy fiscal pipelines: [ANALYSE_METHODOLOGY.md](ANALYSE_METHODOLOGY.md).

## Notes

- Defaults can be overridden from the UI parameter panel; backend and frontend
  defaults are kept in sync and pinned by `backend/tests/test_defaults.py`.
- `taux_actualisation` defaults to 5% and drives VAN/stress-VAN discounting.
  Clear it to fall back to the CAPM+Hamada `ke`, but note `ke` is highly
  leverage-sensitive (see ANALYSE_METHODOLOGY.md §7.2) and can produce
  unrealistic hurdle rates at typical mortgage LTVs.
- This is a decision-support model, not legal, tax, or accounting advice.

## License

Private project.
