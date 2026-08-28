from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import RecoveryRun
from ..schemas import RecoveryRunRecord, RecoveryRunRequest, RecoveryRunResponse
from ..services.agent import run_recovery_analysis

router = APIRouter(prefix="/api/recovery", tags=["recovery"])

_recent_runs: dict[str, dict] = {}


@router.post("/run", response_model=RecoveryRunResponse)
def run_recovery(payload: RecoveryRunRequest, db: Session = Depends(get_db)):
    result = run_recovery_analysis(db, payload.product_ids, payload.region_ids, payload.budget, payload.scenario_id)
    _recent_runs[result["run_id"]] = result
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
def get_run_strategies(run_id: str):
    if run_id not in _recent_runs:
        raise HTTPException(status_code=404, detail="Run details unavailable in current process")
    return {"run_id": run_id, "strategies": _recent_runs[run_id]["strategies"]}
