from __future__ import annotations

from datetime import date, timedelta


def calculate_stockout(
    *,
    on_hand_units: int,
    reserved_units: int,
    in_transit_units: int,
    forecast_daily: list[float],
    supplier_delay_probability: float,
    demand_uncertainty: float,
    supplier_reliability: float,
    demand_shock_severity: float,
) -> dict:
    available = max(0.0, float(on_hand_units - reserved_units + in_transit_units))
    remaining = available

    days_to_stockout = None
    for day_idx, demand in enumerate(forecast_daily, start=1):
        remaining -= demand
        if remaining <= 0 and days_to_stockout is None:
            days_to_stockout = day_idx
            break

    stockout_date = date.today() + timedelta(days=days_to_stockout) if days_to_stockout else None

    avg_demand = max(1.0, sum(forecast_daily) / max(1, len(forecast_daily)))
    coverage_days = available / avg_demand
    inventory_coverage_risk = max(0.0, min(1.0, 1 - (coverage_days / max(1.0, len(forecast_daily) * 0.75))))

    demand_risk = max(0.0, min(1.0, demand_uncertainty + 0.4 * demand_shock_severity))
    supplier_risk = max(0.0, min(1.0, supplier_delay_probability + (1 - supplier_reliability)))

    probability = 0.45 * demand_risk + 0.35 * supplier_risk + 0.20 * inventory_coverage_risk
    probability = max(0.0, min(1.0, probability))

    if probability >= 0.75:
        risk_level = "Critical"
    elif probability >= 0.5:
        risk_level = "High"
    elif probability >= 0.25:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    return {
        "available_inventory": int(available),
        "days_to_stockout": days_to_stockout,
        "stockout_date": stockout_date,
        "stockout_probability": round(probability, 2),
        "risk_level": risk_level,
    }
