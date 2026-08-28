# StockShield

StockShield is a full-stack demo app for stockout risk prediction and recovery optimization.

## Round 1 capabilities

- Six integrated intelligence components:
  - Demand forecasting
  - Stockout probability prediction
  - Supplier-delay prediction
  - Regional demand-shift detection
  - Recovery-outcome prediction
  - Lost-revenue prediction
- Multiple products, suppliers, and regions with deterministic seeded data
- Demand-shock and supplier-delay disruption injection
- Four recovery strategies:
  - Reorder
  - Transfer
  - Reallocate
  - Supplier switch
- Recovery optimization for expected net revenue protection
- Dashboard with risk matrix, financial impact, strategy comparison, and recommendation reasoning

## Project structure

- `/backend`: FastAPI + SQLAlchemy + SQLite
- `/frontend`: React + Vite + TypeScript
- `docker-compose.yml`: local full-stack run

## Quick start

### Option 1: Docker Compose

```bash
docker compose up --build
```

- Frontend: `http://localhost:5173`
- Backend health: `http://localhost:8000/api/health`

### Option 2: Local development

Backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Key API endpoints

- `GET /api/health`
- `GET /api/dashboard/summary`
- `GET /api/dashboard/risk-matrix`
- `GET /api/dashboard/forecast?product_id=1&region_id=1`
- `GET /api/products`
- `GET /api/products/{product_id}`
- `GET /api/products/{product_id}/risk`
- `GET /api/suppliers`
- `GET /api/suppliers/{supplier_id}/risk`
- `GET /api/disruptions`
- `POST /api/disruptions`
- `POST /api/disruptions/{disruption_id}/activate`
- `POST /api/disruptions/{disruption_id}/deactivate`
- `POST /api/recovery/run`
- `GET /api/recovery/runs/{run_id}`
- `GET /api/recovery/runs/{run_id}/strategies`

## Tests

```bash
cd backend
pytest -q
```
