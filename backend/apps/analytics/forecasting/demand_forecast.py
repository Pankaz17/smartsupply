"""
ARIMA demand forecasting for SmartSupply.

Integration with Seasonal Intelligence
--------------------------------------
- Historical ADS fallback: base_ads × seasonal event multiplier (unchanged).
- ARIMA forecast path: predicted daily demand is used as the demand input to
  ROP *without* applying the SeasonalEvent multiplier.

Rationale: simple ARIMA already reflects patterns present in the historical
daily series (including past seasonal spikes). Multiplying again by calendar
SeasonalEvent multipliers would double-count seasonality and inflate ROP.
SeasonalEvent multipliers remain active for the Historical ADS fallback and
for UI/reporting of upcoming seasonal events.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from django.db.models import Sum
from django.db.models.functions import TruncDate
from django.utils import timezone

from apps.sales.models import Sale

# Minimum calendar days in the filled daily series before ARIMA may run.
MIN_HISTORICAL_DAYS = 30
# Default forecast horizon (days ahead).
FORECAST_HORIZON_DAYS = 7
# How far back to build the daily series (caps sparse early history).
MAX_LOOKBACK_DAYS = 90
# Hold-out days for MAE evaluation (must be < MIN_HISTORICAL_DAYS).
MAE_HOLD_OUT_DAYS = 7

STATUS_FORECAST_AVAILABLE = 'FORECAST_AVAILABLE'
STATUS_INSUFFICIENT_DATA = 'INSUFFICIENT_DATA'

MODEL_ARIMA = 'ARIMA'
TREND_INCREASING = 'increasing'
TREND_DECREASING = 'decreasing'
TREND_STABLE = 'stable'

_QUANTIZE = Decimal('0.01')
# Relative change threshold for classifying demand trend.
_TREND_THRESHOLD = Decimal('0.10')


@dataclass
class DemandForecastResult:
    product_id: int
    product_name: str
    forecast_horizon: int
    predicted_daily_demand: Optional[Decimal]
    predicted_horizon_total: Optional[Decimal]
    model_name: Optional[str]
    historical_observations: int
    status: str
    historical_ads: Decimal
    mae: Optional[Decimal] = None
    trend: Optional[str] = None
    fallback: Optional[str] = None

    def to_dict(self):
        return {
            'product_id': self.product_id,
            'product': self.product_name,
            'model': self.model_name,
            'forecast_horizon': self.forecast_horizon,
            'predicted_daily_demand': (
                str(self.predicted_daily_demand)
                if self.predicted_daily_demand is not None
                else None
            ),
            'predicted_horizon_total': (
                str(self.predicted_horizon_total)
                if self.predicted_horizon_total is not None
                else None
            ),
            'historical_observations': self.historical_observations,
            'historical_ads': str(self.historical_ads),
            'status': self.status,
            'mae': str(self.mae) if self.mae is not None else None,
            'trend': self.trend,
            'fallback': self.fallback,
        }


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANTIZE, rounding=ROUND_HALF_UP)


def _decimal(value) -> Decimal:
    return _quantize(Decimal(str(value)))


def calculate_historical_ads(product, days=30) -> Decimal:
    """Plain 30-day ADS (no seasonal multiplier) for comparison / fallback."""
    since = timezone.now() - timedelta(days=days)
    total_sold = (
        Sale.objects.filter(product=product, created_at__gte=since)
        .aggregate(total=Sum('quantity'))['total']
        or 0
    )
    return _decimal(Decimal(total_sold) / Decimal(days))


def build_daily_demand_series(product, lookback_days=MAX_LOOKBACK_DAYS):
    """
    Aggregate sales into a chronological daily demand list.

    Missing dates are filled with 0 so ARIMA sees a regular daily series.
    Returns (dates, values) where values are floats (non-negative).
    """
    today = timezone.localdate()
    start = today - timedelta(days=lookback_days - 1)

    rows = (
        Sale.objects.filter(
            product=product,
            created_at__date__gte=start,
            created_at__date__lte=today,
        )
        .annotate(day=TruncDate('created_at'))
        .values('day')
        .annotate(total=Sum('quantity'))
        .order_by('day')
    )
    by_day = {row['day']: int(row['total'] or 0) for row in rows}

    dates = []
    values = []
    cursor = start
    while cursor <= today:
        dates.append(cursor)
        values.append(float(max(0, by_day.get(cursor, 0))))
        cursor += timedelta(days=1)

    return dates, values


def _classify_trend(recent_avg: Decimal, forecast_avg: Decimal) -> str:
    if recent_avg <= 0:
        if forecast_avg > 0:
            return TREND_INCREASING
        return TREND_STABLE
    change = (forecast_avg - recent_avg) / recent_avg
    if change >= _TREND_THRESHOLD:
        return TREND_INCREASING
    if change <= -_TREND_THRESHOLD:
        return TREND_DECREASING
    return TREND_STABLE


def _fit_arima_forecast(values, horizon):
    """Fit a simple ARIMA model and forecast `horizon` steps. Returns list of floats."""
    import numpy as np
    from statsmodels.tsa.arima.model import ARIMA

    series = np.asarray(values, dtype=float)
    orders = ((1, 1, 1), (1, 0, 0), (0, 1, 1), (2, 1, 0))

    last_error = None
    for order in orders:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter('ignore')
                model = ARIMA(series, order=order)
                fitted = model.fit()
                forecast = fitted.forecast(steps=horizon)
            return [max(0.0, float(x)) for x in forecast]
        except Exception as exc:  # noqa: BLE001 — try next order
            last_error = exc
            continue

    raise RuntimeError(f'ARIMA fit failed: {last_error}')


def evaluate_forecast_mae(values, hold_out=MAE_HOLD_OUT_DAYS) -> Optional[Decimal]:
    """
    Walk-forward style MAE: fit on all but last `hold_out` days, forecast hold-out,
    compare to actuals. Returns None if not enough data for a meaningful evaluation.
    """
    if len(values) < MIN_HISTORICAL_DAYS or len(values) <= hold_out + 5:
        return None

    train = values[:-hold_out]
    actual = values[-hold_out:]
    try:
        predicted = _fit_arima_forecast(train, hold_out)
    except Exception:  # noqa: BLE001
        return None

    errors = [abs(a - p) for a, p in zip(actual, predicted)]
    return _decimal(sum(errors) / len(errors))


def _trim_leading_zeros(values):
    """Drop leading zero-demand days so observation count reflects real history span."""
    for i, value in enumerate(values):
        if value > 0:
            return values[i:]
    return []


def forecast_product_demand(product, horizon=FORECAST_HORIZON_DAYS) -> DemandForecastResult:
    """
    Generate an ARIMA demand forecast for one product, or report insufficient data.

    Does not modify inventory, sales, recommendations, or purchase orders.
    """
    historical_ads = calculate_historical_ads(product)
    _, padded_values = build_daily_demand_series(product)
    # Leading zeros are lookback padding; count/fit from first positive sale day.
    values = _trim_leading_zeros(padded_values)
    observations = len(values)

    insufficient = DemandForecastResult(
        product_id=product.pk,
        product_name=product.name,
        forecast_horizon=horizon,
        predicted_daily_demand=None,
        predicted_horizon_total=None,
        model_name=None,
        historical_observations=observations,
        status=STATUS_INSUFFICIENT_DATA,
        historical_ads=historical_ads,
        mae=None,
        trend=None,
        fallback='Historical ADS',
    )

    if observations < MIN_HISTORICAL_DAYS:
        return insufficient

    # Need some positive demand signal; all-zero series is not forecastable meaningfully.
    if sum(values) <= 0:
        return insufficient

    try:
        forecast_values = _fit_arima_forecast(values, horizon)
    except Exception:  # noqa: BLE001
        return insufficient

    daily = _decimal(sum(forecast_values) / len(forecast_values))
    if daily < 0:
        daily = Decimal('0.00')
    horizon_total = _decimal(daily * Decimal(horizon))

    recent_window = values[-horizon:] if len(values) >= horizon else values
    recent_avg = _decimal(sum(recent_window) / len(recent_window)) if recent_window else Decimal('0.00')
    trend = _classify_trend(recent_avg, daily)
    mae = evaluate_forecast_mae(values)

    return DemandForecastResult(
        product_id=product.pk,
        product_name=product.name,
        forecast_horizon=horizon,
        predicted_daily_demand=daily,
        predicted_horizon_total=horizon_total,
        model_name=MODEL_ARIMA,
        historical_observations=observations,
        status=STATUS_FORECAST_AVAILABLE,
        historical_ads=historical_ads,
        mae=mae,
        trend=trend,
        fallback=None,
    )


def persist_forecast_result(product, result: DemandForecastResult, on_date: Optional[date] = None):
    """Upsert today's DemandForecast row from a result object."""
    from apps.analytics.models import DemandForecast

    on_date = on_date or timezone.localdate()
    obj, _ = DemandForecast.objects.update_or_create(
        product=product,
        forecast_date=on_date,
        defaults={
            'forecast_horizon': result.forecast_horizon,
            'predicted_daily_demand': result.predicted_daily_demand,
            'predicted_horizon_total': result.predicted_horizon_total,
            'model_name': result.model_name or '',
            'historical_observations': result.historical_observations,
            'historical_ads': result.historical_ads,
            'status': result.status,
            'mae': result.mae,
            'trend': result.trend or '',
        },
    )
    return obj


def get_or_compute_forecast(product, persist=True) -> DemandForecastResult:
    """Return today's forecast for a product, computing if missing."""
    from apps.analytics.models import DemandForecast

    today = timezone.localdate()
    existing = (
        DemandForecast.objects.filter(product=product, forecast_date=today)
        .first()
    )
    if existing:
        return DemandForecastResult(
            product_id=product.pk,
            product_name=product.name,
            forecast_horizon=existing.forecast_horizon,
            predicted_daily_demand=existing.predicted_daily_demand,
            predicted_horizon_total=existing.predicted_horizon_total,
            model_name=existing.model_name or None,
            historical_observations=existing.historical_observations,
            status=existing.status,
            historical_ads=existing.historical_ads,
            mae=existing.mae,
            trend=existing.trend or None,
            fallback=(
                'Historical ADS'
                if existing.status == STATUS_INSUFFICIENT_DATA
                else None
            ),
        )

    result = forecast_product_demand(product)
    if persist:
        persist_forecast_result(product, result, on_date=today)
    return result


def update_demand_forecasts():
    """Refresh forecasts for all active products (nightly analytics step)."""
    from apps.products.models import Product

    created = 0
    available = 0
    insufficient = 0

    products = Product.objects.filter(is_active=True).select_related('category', 'supplier')
    for product in products:
        result = forecast_product_demand(product)
        persist_forecast_result(product, result)
        created += 1
        if result.status == STATUS_FORECAST_AVAILABLE:
            available += 1
        else:
            insufficient += 1

    return {
        'forecasts_updated': created,
        'forecasts_available': available,
        'forecasts_insufficient': insufficient,
    }


def build_forecast_advisor_messages(limit=3):
    """
    Factual dashboard messages based on available forecasts only.
    Avoids certainty claims or purchase directives.
    """
    from apps.analytics.models import DemandForecast

    today = timezone.localdate()
    qs = (
        DemandForecast.objects.filter(
            forecast_date=today,
            status=STATUS_FORECAST_AVAILABLE,
            trend__in=[TREND_INCREASING, TREND_DECREASING, TREND_STABLE],
        )
        .select_related('product')
        .order_by('-predicted_daily_demand')[:limit]
    )

    messages = []
    for row in qs:
        name = row.product.name
        if row.trend == TREND_INCREASING:
            messages.append(
                f'Forecasted demand for {name} is increasing over the next '
                f'{row.forecast_horizon} days.',
            )
        elif row.trend == TREND_DECREASING:
            messages.append(
                f'Forecasted demand for {name} is decreasing over the next '
                f'{row.forecast_horizon} days.',
            )
        else:
            messages.append(
                f'Forecast indicates relatively stable demand for {name} '
                f'over the next {row.forecast_horizon} days.',
            )
    return messages
