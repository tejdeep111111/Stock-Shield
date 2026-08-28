from __future__ import annotations

from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str


class ProductOut(BaseModel):
    id: int
    sku: str
    name: str
    category: str
    unit_price: float
    unit_cost: float
    criticality: str


class SupplierOut(BaseModel):
    id: int
    name: str
    reliability_score: float
    default_lead_time_days: int
    capacity_units: int
    expedited_available: bool


class DisruptionCreate(BaseModel):
    type: Literal["demand_shock", "supplier_delay"]
    name: str
    product_id: int | None = None
    supplier_id: int | None = None
    region_id: int | None = None
    severity: float = 0.0
    start_date: date
    duration_days: int = 7
    demand_multiplier: float = 1.0
    delay_days: int = 0


class DisruptionOut(DisruptionCreate):
    id: int
    active: bool


class ForecastPoint(BaseModel):
    day: int
    demand: float


class ForecastResponse(BaseModel):
    product_id: int
    region_id: int
    forecast_horizon_days: int
    daily_forecast: list[float]
    average_daily_demand: float
    confidence_lower: float
    confidence_upper: float


class ProductRiskOut(BaseModel):
    product_id: int
    product_name: str
    region_id: int
    region_name: str
    current_inventory: int
    daily_demand: float
    stockout_date: date | None
    days_to_stockout: int | None
    stockout_probability: float
    risk_level: str
    expected_lost_revenue: float
    recommended_action: str


class SupplierRiskOut(BaseModel):
    supplier_id: int
    delay_probability: float
    expected_delay_days: int
    risk_level: str
    explanation: list[str]


class StrategyOut(BaseModel):
    strategy: str
    success_probability: float
    arrival_days: int
    units_recovered: int
    revenue_protected: float
    cost: float
    net_value: float


class RecoveryRunRequest(BaseModel):
    scenario_id: str = "default"
    product_ids: list[int] | None = None
    region_ids: list[int] | None = None
    budget: float = 10000


class RecoveryRecommendation(BaseModel):
    recommended_action: str
    expected_revenue_protected: float
    intervention_cost: float
    net_value: float
    confidence: float
    reasoning: list[str]


class RecoveryRunResponse(BaseModel):
    run_id: str
    status: str
    at_risk_products: list[ProductRiskOut]
    strategies: list[StrategyOut]
    recommendation: RecoveryRecommendation
    explanations: list[str]


class RecoveryRunRecord(BaseModel):
    run_id: str
    created_at: datetime
    status: str
    recommendation: str
    expected_revenue_protected: float


class DashboardSummary(BaseModel):
    products_at_risk: int
    expected_lost_revenue: float
    revenue_protected: float
    critical_supplier_risks: int
    average_days_to_stockout: float
    last_analysis_timestamp: datetime


class RiskMatrixResponse(BaseModel):
    risks: list[ProductRiskOut]


class ForecastChartResponse(BaseModel):
    product_id: int
    region_id: int
    history: list[ForecastPoint]
    forecast: list[ForecastPoint]
    lower_band: list[ForecastPoint]
    upper_band: list[ForecastPoint]
