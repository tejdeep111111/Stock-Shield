from __future__ import annotations


def predict_lost_revenue(available_inventory: int, forecast_daily: list[float], unit_price: float) -> dict:
    total_demand = sum(forecast_daily)
    lost_units = max(0.0, total_demand - available_inventory)
    expected = round(lost_units * unit_price, 2)
    return {
        "lost_units": round(lost_units, 2),
        "low_case_lost_revenue": round(expected * 0.85, 2),
        "expected_lost_revenue": expected,
        "high_case_lost_revenue": round(expected * 1.15, 2),
    }
