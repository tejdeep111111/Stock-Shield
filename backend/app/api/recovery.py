from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import RecoveryRun, RecoveryRunStrategy
from ..schemas import RecoveryRunRecord, RecoveryRunRequest, RecoveryRunResponse
from ..services.agent import run_recovery_analysis

router = APIRouter(prefix="/api/recovery", tags=["recovery"])

@router.post("/run", response_model=RecoveryRunResponse)
def run_recovery(payload: RecoveryRunRequest, db: Session = Depends(get_db)):
    result = run_recovery_analysis(db, payload.product_ids, payload.region_ids, payload.budget, payload.scenario_id)
    return result


@router.get("/runs/{run_id}", response_model=RecoveryRunRecord)
def get_run(run_id: str, db: Session = Depends(get_db)):
    run = db.query(RecoveryRun).filter(RecoveryRun.run_id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return {
        "run_id": run.run_id,
        "created_at": run.created_at,
        "status": run.status,
        "recommendation": run.recommendation,
        "expected_revenue_protected": run.expected_revenue_protected,
    }


@router.get("/runs/{run_id}/strategies")
def get_run_strategies(run_id: str, db: Session = Depends(get_db)):
    rows = db.query(RecoveryRunStrategy).filter(RecoveryRunStrategy.run_id == run_id).all()
    if not rows:
        raise HTTPException(status_code=404, detail="Run strategies not found")
    return {
        "run_id": run_id,
        "strategies": [
            {
                "strategy": row.strategy,
                "success_probability": row.success_probability,
                "arrival_days": row.arrival_days,
                "units_recovered": row.units_recovered,
                "revenue_protected": row.revenue_protected,
                "cost": row.cost,
                "net_value": row.net_value,
            }
            for row in rows
        ],
    }
