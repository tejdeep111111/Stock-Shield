from __future__ import annotations


def score_strategy(
    *,
    strategy: str,
    units: int,
    arrival_days: int,
    success_probability: float,
    unit_price: float,
    cost: float,
    stockout_days: int | None,
) -> dict:
    if stockout_days is not None and arrival_days > stockout_days:
        timing_factor = 0.55
    else:
        timing_factor = 1.0
    revenue_protected = units * unit_price * success_probability * timing_factor
    net_value = revenue_protected - cost
    return {
        "strategy": strategy,
        "success_probability": round(success_probability, 2),
        "arrival_days": arrival_days,
        "units_recovered": units,
        "revenue_protected": round(revenue_protected, 2),
        "cost": round(cost, 2),
        "net_value": round(net_value, 2),
    }
