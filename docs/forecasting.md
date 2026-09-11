# Phase 10.1 – Predictive Demand Forecasting (ARIMA)

## Why forecasting was added

Historical ADS uses a fixed 30-day average. ARIMA improves demand estimation for products with enough daily sales history by projecting near-term demand, while remaining advisory only.

## Why ARIMA

ARIMA is a classical, explainable time-series method suitable for a final-year project. It does not require a large ML stack or external SaaS APIs. SmartSupply uses `statsmodels` ARIMA with simple order fallbacks.

## Historical data used

- Source: `Sale.quantity` grouped by `created_at` date per product
- Missing calendar days filled with `0`
- Lookback capped at 90 days when building the series

## Minimum data requirement

- At least **30** daily observations from the **first positive sale day** through today
  (leading zero padding from the lookback window is trimmed before counting)
- Total quantity sold in that series must be **> 0**
- Otherwise status = `INSUFFICIENT_DATA` (no misleading forecast)

## Forecast horizon

- Default: **7 days**
- API/UI report predicted daily demand and next-7-day total

## Interaction with Seasonal Intelligence

| Path | SeasonalEvent multiplier |
|------|--------------------------|
| ARIMA forecast available | **Not applied** (avoids double-counting seasonality already present in history) |
| Insufficient data / ADS fallback | **Applied** (existing behaviour: `base_ads × multiplier`) |

Seasonal events remain available for UI and for the ADS fallback path.

## Interaction with reorder recommendations

```
IF FORECAST_AVAILABLE:
    ads = predicted_daily_demand
    demand_method = arima_forecast
ELSE:
    ads = historical_ADS × seasonal_multiplier
    demand_method = historical_ads

ROP = ads × lead_time + ads × 3
```

Recommendations stay `pending`. No auto PO, no auto approve.

## Fallback

`INSUFFICIENT_DATA` → Historical ADS (+ seasonal multiplier when events are active).

## Accuracy evaluation

Hold-out MAE: fit on all but last 7 days, forecast those 7 days, mean absolute error vs actuals. Reported when enough history exists; otherwise `mae` is null.

## Concept separation

| Concept | What it is |
|---------|------------|
| Historical ADS | Fixed-window average daily sales |
| Seasonal Intelligence | Calendar multipliers for known events |
| ARIMA Forecast | Predictive daily demand from time series |
| Operational Priority | Urgency ranking of pending recommendations |
| Profit Advisor | Budget-aware purchase suggestion helper |
