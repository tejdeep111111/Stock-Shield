from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.orm import Session

from ..models import (
    Disruption,
    Inventory,
    Product,
    RecoveryRun,
    RecoveryRunStrategy,
    Region,
    SalesHistory,
    Shipment,
    Supplier,
)
from .forecasting import build_demand_forecast
from .lost_revenue import predict_lost_revenue
from .optimizer import optimize_recommendation
from .recovery_prediction import score_strategy
from .regional_shift import detect_regional_shift
from .stockout import calculate_stockout
from .supplier_risk import predict_supplier_delay


def _historical_delay_rate(shipments: list[Shipment]) -> float:
    if not shipments:
        return 0.2
    delayed = 0
    for s in shipments:
        if s.actual_arrival_date and s.actual_arrival_date > s.expected_arrival_date:
            delayed += 1
    return delayed / len(shipments)


def run_recovery_analysis(db: Session, product_ids: list[int] | None, region_ids: list[int] | None, budget: float, scenario_id: str) -> dict:
    products = {p.id: p for p in db.query(Product).all()}
    regions = {r.id: r for r in db.query(Region).all()}
    suppliers = {s.id: s for s in db.query(Supplier).all()}

    disruptions = db.query(Disruption).filter(Disruption.active.is_(True)).all()
    all_shipments = db.query(Shipment).all()
    shipments_by_supplier: dict[int, list[Shipment]] = defaultdict(list)
    for shipment in all_shipments:
        shipments_by_supplier[shipment.supplier_id].append(shipment)

    inventory_rows = db.query(Inventory).all()
    if product_ids:
        inventory_rows = [row for row in inventory_rows if row.product_id in product_ids]
    if region_ids:
        inventory_rows = [row for row in inventory_rows if row.region_id in region_ids]

    sales = db.query(SalesHistory).all()
    sales_map: dict[tuple[int, int], list[int]] = defaultdict(list)
    for row in sales:
        sales_map[(row.product_id, row.region_id)].append(row.units_sold)

    shifts: list[str] = []
    risk_rows: list[dict] = []
    strategy_candidates: list[dict] = []

    for inv in inventory_rows:
        p = products[inv.product_id]
        r = regions[inv.region_id]
        supplier = suppliers[inv.supplier_id]

        history = sales_map[(inv.product_id, inv.region_id)]
        demand_multiplier = 1.0
        demand_severity = 0.0
        disruption_factor = 0.0
        extra_delay = 0
        for d in disruptions:
            if d.type == "demand_shock" and (d.product_id in (None, inv.product_id)) and (d.region_id in (None, inv.region_id)):
                demand_multiplier *= d.demand_multiplier
                demand_severity = max(demand_severity, d.severity)
            if d.type == "supplier_delay" and (d.supplier_id in (None, inv.supplier_id)) and (d.product_id in (None, inv.product_id)):
                disruption_factor = max(disruption_factor, d.severity)
                extra_delay = max(extra_delay, d.delay_days)

        forecast = build_demand_forecast(history, 14, demand_multiplier)
        recent_7 = sum(history[-7:]) / max(1, len(history[-7:])) if history else 0
        previous_28 = sum(history[-35:-7]) / max(1, len(history[-35:-7])) if len(history) >= 35 else recent_7
        shift = detect_regional_shift(recent_7, previous_28)
        if shift["shift_detected"]:
            shifts.append(f"{p.name} in {r.name}: {shift['change_percent']}% demand {shift['direction']}")

        supplier_shipments = shipments_by_supplier.get(supplier.id, [])
        delay_rate = _historical_delay_rate(supplier_shipments)
        capacity_pressure = (inv.on_hand_units + inv.reserved_units) / max(1, supplier.capacity_units)
        route_risk = 0.35 if r.name in {"Northeast", "West"} else 0.2
        supplier_risk = predict_supplier_delay(
            historical_delay_rate=delay_rate,
            disruption_factor=disruption_factor,
            capacity_pressure=min(1.0, capacity_pressure),
            route_risk=route_risk,
        )
        supplier_delay_prob = supplier_risk["delay_probability"]

        stockout = calculate_stockout(
            on_hand_units=inv.on_hand_units,
            reserved_units=inv.reserved_units,
            in_transit_units=inv.in_transit_units,
            forecast_daily=forecast["daily_forecast"],
            supplier_delay_probability=supplier_delay_prob,
            demand_uncertainty=(forecast["confidence_upper"] - forecast["confidence_lower"]) / max(1.0, forecast["average_daily_demand"] * 3),
            supplier_reliability=supplier.reliability_score,
            demand_shock_severity=demand_severity,
        )

        lost = predict_lost_revenue(stockout["available_inventory"], forecast["daily_forecast"], p.unit_price)

        risk_rows.append(
            {
                "product_id": p.id,
                "product_name": p.name,
                "region_id": r.id,
                "region_name": r.name,
                "current_inventory": stockout["available_inventory"],
                "daily_demand": forecast["average_daily_demand"],
                "stockout_date": stockout["stockout_date"],
                "days_to_stockout": stockout["days_to_stockout"],
                "stockout_probability": stockout["stockout_probability"],
                "risk_level": stockout["risk_level"],
                "expected_lost_revenue": lost["expected_lost_revenue"],
                "recommended_action": "Pending optimization",
            }
        )

        if stockout["risk_level"] in {"Critical", "High", "Medium"}:
            needed = max(30, int(forecast["average_daily_demand"] * 3))
            reorder_units = min(needed, supplier.capacity_units)
            reorder_lead = max(1, supplier.default_lead_time_days + extra_delay)
            strategy_candidates.append(
                score_strategy(
                    strategy=f"Reorder {reorder_units} units from {supplier.name}",
                    units=reorder_units,
                    arrival_days=reorder_lead,
                    success_probability=max(0.5, supplier.reliability_score - supplier_delay_prob * 0.2),
                    unit_price=p.unit_price,
                    cost=reorder_units * p.unit_cost * 0.1 + (220 if supplier.expedited_available else 90),
                    stockout_days=stockout["days_to_stockout"],
                )
            )
            strategy_candidates.append(
                score_strategy(
                    strategy=f"Transfer {needed} units to {r.name}",
                    units=needed,
                    arrival_days=2,
                    success_probability=0.91,
                    unit_price=p.unit_price,
                    cost=needed * 2.5,
                    stockout_days=stockout["days_to_stockout"],
                )
            )
            strategy_candidates.append(
                score_strategy(
                    strategy=f"Reallocate {needed} units to high-value demand in {r.name}",
                    units=needed,
                    arrival_days=1,
                    success_probability=0.8,
                    unit_price=p.unit_price,
                    cost=max(120.0, needed * 1.2),
                    stockout_days=stockout["days_to_stockout"],
                )
            )
            alternate = max(suppliers.values(), key=lambda s: (s.reliability_score, s.capacity_units))
            switch_units = min(needed, alternate.capacity_units)
            strategy_candidates.append(
                score_strategy(
                    strategy=f"Switch to {alternate.name} for {switch_units} units",
                    units=switch_units,
                    arrival_days=max(2, alternate.default_lead_time_days - 1),
                    success_probability=min(0.97, alternate.reliability_score),
                    unit_price=p.unit_price,
                    cost=switch_units * p.unit_cost * 0.2 + 320,
                    stockout_days=stockout["days_to_stockout"],
                )
            )

    recommendation = optimize_recommendation(strategy_candidates, budget)

    for row in risk_rows:
        if row["risk_level"] in {"Critical", "High", "Medium"}:
            row["recommended_action"] = recommendation["recommended_action"]

    run_id = f"run_{uuid4().hex[:8]}"
    run = RecoveryRun(
        run_id=run_id,
        status="completed",
        scenario_id=scenario_id,
        recommendation=recommendation["recommended_action"],
        expected_revenue_protected=recommendation["expected_revenue_protected"],
    )
    db.add(run)
    for strategy in strategy_candidates:
        db.add(
            RecoveryRunStrategy(
                run_id=run_id,
                strategy=strategy["strategy"],
                success_probability=strategy["success_probability"],
                arrival_days=strategy["arrival_days"],
                units_recovered=strategy["units_recovered"],
                revenue_protected=strategy["revenue_protected"],
                cost=strategy["cost"],
                net_value=strategy["net_value"],
            )
        )
    db.commit()

    return {
        "run_id": run_id,
        "status": "completed",
        "at_risk_products": sorted(risk_rows, key=lambda r: r["stockout_probability"], reverse=True),
        "strategies": sorted(strategy_candidates, key=lambda s: s["net_value"], reverse=True)[:12],
        "recommendation": recommendation,
        "explanations": [
            "Recovery pipeline executed: forecast, supplier risk, regional shift, stockout, lost revenue, strategy scoring, optimization",
            *shifts[:8],
        ],
        "timestamp": datetime.now(timezone.utc),
    }
