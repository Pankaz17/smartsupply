"""Demand forecasting package (ARIMA-based predictive demand).

SmartSupply philosophy: forecasts advise; they never auto-purchase or approve.
"""

from .demand_forecast import (
    FORECAST_HORIZON_DAYS,
    MIN_HISTORICAL_DAYS,
    STATUS_FORECAST_AVAILABLE,
    STATUS_INSUFFICIENT_DATA,
    DemandForecastResult,
    build_daily_demand_series,
    evaluate_forecast_mae,
    forecast_product_demand,
    get_or_compute_forecast,
    update_demand_forecasts,
)

__all__ = [
    'FORECAST_HORIZON_DAYS',
    'MIN_HISTORICAL_DAYS',
    'STATUS_FORECAST_AVAILABLE',
    'STATUS_INSUFFICIENT_DATA',
    'DemandForecastResult',
    'build_daily_demand_series',
    'evaluate_forecast_mae',
    'forecast_product_demand',
    'get_or_compute_forecast',
    'update_demand_forecasts',
]
