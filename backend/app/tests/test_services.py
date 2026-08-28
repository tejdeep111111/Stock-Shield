from app.services.forecasting import build_demand_forecast
from app.services.lost_revenue import predict_lost_revenue
from app.services.stockout import calculate_stockout


def test_forecast_has_horizon_and_bounds():
    history = [20, 21, 19, 22, 26, 28, 25] * 6
    forecast = build_demand_forecast(history, 14, demand_multiplier=1.2)
    assert len(forecast["daily_forecast"]) == 14
    assert forecast["confidence_lower"] <= forecast["average_daily_demand"] <= forecast["confidence_upper"]


def test_stockout_probability_range_and_level():
    result = calculate_stockout(
        on_hand_units=80,
        reserved_units=10,
        in_transit_units=0,
        forecast_daily=[35.0] * 14,
        supplier_delay_probability=0.7,
        demand_uncertainty=0.5,
        supplier_reliability=0.6,
        demand_shock_severity=0.5,
    )
    assert 0.0 <= result["stockout_probability"] <= 1.0
    assert result["risk_level"] in {"Critical", "High", "Medium", "Low"}
    assert result["stockout_date"] is not None


def test_lost_revenue_non_negative():
    revenue = predict_lost_revenue(available_inventory=40, forecast_daily=[30, 30, 30], unit_price=120)
    assert revenue["expected_lost_revenue"] >= 0
    assert revenue["high_case_lost_revenue"] >= revenue["expected_lost_revenue"]
