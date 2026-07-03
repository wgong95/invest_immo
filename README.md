# Invest Immo

A real-estate investment analysis app for comparing multiple strategies and multiple properties.

## What It Does

- Compare up to 4 properties side by side
- Evaluate 5 strategies:
  - Location Nue
  - LMNP Meuble
  - Airbnb / Location Courte Duree
  - SCPI
  - Residence Principale
- Compute yearly cash flow, taxes, net wealth, and financing effects
- Show decision metrics per strategy:
  - TRI (IRR)
  - VAN (NPV)
  - ke (Hamada + CAPM)
  - TRI - ke
  - CoC Return (year 1)
  - Stress-test VAN
- Export PDF / Excel
- Import / export flat configs (JSON)

## Tech Stack

- Frontend: Next.js 14 + React + TypeScript + Tailwind
- Backend: FastAPI + Pydantic

## Repository Structure

- `frontend/`: Next.js application
- `backend/`: FastAPI API and financial engine
- `docker-compose.yml`: local container orchestration
- `DOCKER.md`: Docker usage notes
- `start.sh`: legacy local startup script

## Prerequisites

- Node.js 20+
- Python 3.11+
- npm
- (Optional) Docker Desktop

## Run Locally (without Docker)

### 1) Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
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
- Body: `Params` object (see `backend/main.py` and `frontend/lib/types.ts`)

## Key Financial Metrics

- **TRI**: annualized internal rate of return from the project cash-flow timeline.
- **VAN**: net present value under a discount rate.
- **ke (Hamada + CAPM)**: strategy-specific cost of equity.
- **TRI - ke**: spread between project return and equity cost.
- **CoC Return**: first-year cash return on initial equity outlay.
- **Stress VAN**: downside NPV under reduced cash flow and terminal value factors.

## Notes

- Defaults can be overridden from the UI parameter panel.
- If `taux_actualisation` is set, it is used for VAN discounting; otherwise model defaults are applied.

## License

Private project.
