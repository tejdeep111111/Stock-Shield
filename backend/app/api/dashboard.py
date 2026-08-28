from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import SalesHistory
from ..schemas import DashboardSummary, ForecastChartResponse, ForecastPoint, RiskMatrixResponse
from ..services.agent import run_recovery_analysis
from ..services.forecasting import build_demand_forecast

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def get_summary(db: Session = Depends(get_db)):
    analysis = run_recovery_analysis(db, None, None, 10000, "dashboard-summary")
    risk_rows = analysis["at_risk_products"]
    supplier_critical = len([r for r in risk_rows if r["risk_level"] == "Critical"])
    days = [r["days_to_stockout"] for r in risk_rows if r["days_to_stockout"] is not None]
    return DashboardSummary(
        products_at_risk=len([r for r in risk_rows if r["risk_level"] in {"Critical", "High", "Medium"}]),
        expected_lost_revenue=round(sum(r["expected_lost_revenue"] for r in risk_rows), 2),
        revenue_protected=analysis["recommendation"]["expected_revenue_protected"],
        critical_supplier_risks=supplier_critical,
        average_days_to_stockout=round(sum(days) / len(days), 2) if days else 0.0,
        last_analysis_timestamp=datetime.now(timezone.utc),
    )


@router.get("/risk-matrix", response_model=RiskMatrixResponse)
def get_risk_matrix(db: Session = Depends(get_db)):
    analysis = run_recovery_analysis(db, None, None, 10000, "risk-matrix")
    return {"risks": analysis["at_risk_products"]}


@router.get("/forecast", response_model=ForecastChartResponse)
def get_forecast(
    product_id: int = Query(...),
    region_id: int = Query(...),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(SalesHistory)
        .filter(SalesHistory.product_id == product_id, SalesHistory.region_id == region_id)
        .order_by(SalesHistory.date.asc())
        .all()
    )
    history_vals = [r.units_sold for r in rows][-30:]
    forecast = build_demand_forecast(history_vals, 14, 1.0)

    history_points = [ForecastPoint(day=i + 1, demand=float(v)) for i, v in enumerate(history_vals)]
    forecast_points = [ForecastPoint(day=31 + i, demand=float(v)) for i, v in enumerate(forecast["daily_forecast"])]
    lower = [ForecastPoint(day=31 + i, demand=float(forecast["confidence_lower"])) for i in range(14)]
    upper = [ForecastPoint(day=31 + i, demand=float(forecast["confidence_upper"])) for i in range(14)]
    return {
        "product_id": product_id,
        "region_id": region_id,
        "history": history_points,
        "forecast": forecast_points,
        "lower_band": lower,
        "upper_band": upper,
    }
