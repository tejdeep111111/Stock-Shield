from __future__ import annotations

from statistics import mean, pstdev


def build_demand_forecast(history: list[int], horizon_days: int, demand_multiplier: float = 1.0) -> dict:
    if not history:
        history = [10] * 30

    recent_7 = mean(history[-7:]) if len(history) >= 7 else mean(history)
    recent_28 = mean(history[-28:]) if len(history) >= 28 else mean(history)

    weekday_groups: dict[int, list[int]] = {i: [] for i in range(7)}
    for i, value in enumerate(history):
        weekday_groups[i % 7].append(value)

    avg_weekday = mean([mean(vals) for vals in weekday_groups.values() if vals])
    baseline = 0.5 * recent_7 + 0.3 * recent_28 + 0.2 * avg_weekday

    daily = []
    for i in range(horizon_days):
        seasonal = 1.08 if i % 7 in {4, 5} else 0.96
        daily.append(round(baseline * seasonal * demand_multiplier, 2))

    sigma = pstdev(history[-28:] if len(history) >= 28 else history) if len(history) > 1 else 1.0
    avg = round(mean(daily), 2)
    lower = round(max(0.0, avg - sigma * 0.6), 2)
    upper = round(avg + sigma * 0.6, 2)

    return {
        "daily_forecast": daily,
        "average_daily_demand": avg,
        "confidence_lower": lower,
        "confidence_upper": upper,
    }
