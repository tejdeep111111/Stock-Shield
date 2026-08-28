from __future__ import annotations


def detect_regional_shift(recent_7_avg: float, previous_28_avg: float) -> dict:
    if previous_28_avg <= 0:
        return {"change_percent": 0.0, "direction": "stable", "confidence": 0.5, "shift_detected": False}

    pct_change = ((recent_7_avg - previous_28_avg) / previous_28_avg) * 100.0
    abs_change = abs(pct_change)
    detected = abs_change >= 20.0
    direction = "increase" if pct_change > 0 else "decrease" if pct_change < 0 else "stable"
    confidence = min(0.99, 0.55 + (abs_change / 100.0))

    return {
        "change_percent": round(pct_change, 2),
        "direction": direction,
        "confidence": round(confidence, 2),
        "shift_detected": detected,
    }
