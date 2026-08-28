from __future__ import annotations


def predict_supplier_delay(
    *,
    historical_delay_rate: float,
    disruption_factor: float,
    capacity_pressure: float,
    route_risk: float,
) -> dict:
    delay_probability = (
        0.5 * historical_delay_rate
        + 0.25 * disruption_factor
        + 0.15 * capacity_pressure
        + 0.1 * route_risk
    )
    delay_probability = max(0.0, min(1.0, delay_probability))

    if delay_probability >= 0.75:
        risk = "Critical"
    elif delay_probability >= 0.5:
        risk = "High"
    elif delay_probability >= 0.25:
        risk = "Medium"
    else:
        risk = "Low"

    return {
        "delay_probability": round(delay_probability, 2),
        "expected_delay_days": max(1, int(round(delay_probability * 8))),
        "risk_level": risk,
    }
