from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Disruption, Shipment, Supplier
from ..schemas import SupplierOut, SupplierRiskOut
from ..services.supplier_risk import predict_supplier_delay

router = APIRouter(prefix="/api/suppliers", tags=["suppliers"])


@router.get("", response_model=list[SupplierOut])
def list_suppliers(db: Session = Depends(get_db)):
    return db.query(Supplier).all()


@router.get("/{supplier_id}/risk", response_model=SupplierRiskOut)
def supplier_risk(supplier_id: int, db: Session = Depends(get_db)):
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    shipments = db.query(Shipment).filter(Shipment.supplier_id == supplier.id).all()
    if shipments:
        delayed = sum(
            1
            for s in shipments
            if s.actual_arrival_date and s.actual_arrival_date > s.expected_arrival_date
        )
        historical_delay_rate = delayed / len(shipments)
    else:
        historical_delay_rate = 0.2

    disruptions = db.query(Disruption).filter(Disruption.active.is_(True), Disruption.supplier_id == supplier.id).all()
    disruption_factor = max([d.severity for d in disruptions], default=0.0)
    capacity_pressure = min(1.0, 0.7)
    route_risk = 0.3
    risk = predict_supplier_delay(
        historical_delay_rate=historical_delay_rate,
        disruption_factor=disruption_factor,
        capacity_pressure=capacity_pressure,
        route_risk=route_risk,
    )
    return {
        "supplier_id": supplier.id,
        "delay_probability": risk["delay_probability"],
        "expected_delay_days": risk["expected_delay_days"],
        "risk_level": risk["risk_level"],
        "explanation": [
            f"Supplier has {historical_delay_rate:.0%} historical late-delivery rate",
            f"Disruption factor score: {disruption_factor:.2f}",
            f"Supplier reliability score: {supplier.reliability_score:.2f}",
        ],
    }
