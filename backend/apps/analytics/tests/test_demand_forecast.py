from datetime import timedelta
from decimal import Decimal

from django.db import models
from django.test import TestCase
from django.utils import timezone
from rest_framework import status

from apps.analytics.forecasting import (
    MIN_HISTORICAL_DAYS,
    STATUS_FORECAST_AVAILABLE,
    STATUS_INSUFFICIENT_DATA,
    build_daily_demand_series,
    forecast_product_demand,
)
from apps.analytics.models import DemandForecast, SeasonalEvent
from apps.purchasing.models import PurchaseOrder, ReorderRecommendation
from apps.purchasing.services import calculate_reorder_metrics, generate_recommendations
from apps.sales.models import Sale
from common.test_utils import (
    auth_client,
    create_owner,
    create_product,
    ensure_business_settings,
)


def _seed_daily_sales(product, user, days, qty_per_day=3):
    """Create one sale per day going backwards from today (does not change stock)."""
    now = timezone.now()
    for i in range(days):
        sale_time = now - timedelta(days=i)
        sale = Sale(
            product=product,
            quantity=qty_per_day,
            unit_price=product.selling_price,
            discount_amount=Decimal('0.00'),
            total_amount=product.selling_price * qty_per_day,
            recorded_by=user,
        )
        # Bypass Sale.save()/full_clean — history only, no stock deduction.
        models.Model.save(sale)
        Sale.objects.filter(pk=sale.pk).update(created_at=sale_time)


class DailySeriesTests(TestCase):
    def setUp(self):
        ensure_business_settings()
        self.owner = create_owner()
        self.product = create_product(stock=100, name='Juice')

    def test_sales_aggregated_by_day_chronological(self):
        now = timezone.now()
        for day_offset, qty in [(2, 5), (0, 2), (1, 3)]:
            sale = Sale(
                product=self.product,
                quantity=qty,
                unit_price=self.product.selling_price,
                discount_amount=Decimal('0.00'),
                total_amount=self.product.selling_price * qty,
                recorded_by=self.owner,
            )
            models.Model.save(sale)
            Sale.objects.filter(pk=sale.pk).update(created_at=now - timedelta(days=day_offset))

        dates, values = build_daily_demand_series(self.product, lookback_days=5)
        self.assertEqual(len(dates), 5)
        self.assertEqual(dates, sorted(dates))
        # Last three calendar days in the 5-day window should match quantities
        self.assertEqual(values[-1], 2.0)  # today
        self.assertEqual(values[-2], 3.0)
        self.assertEqual(values[-3], 5.0)

    def test_missing_dates_filled_with_zero(self):
        sale = Sale(
            product=self.product,
            quantity=4,
            unit_price=self.product.selling_price,
            discount_amount=Decimal('0.00'),
            total_amount=self.product.selling_price * 4,
            recorded_by=self.owner,
        )
        models.Model.save(sale)
        Sale.objects.filter(pk=sale.pk).update(created_at=timezone.now() - timedelta(days=3))

        _, values = build_daily_demand_series(self.product, lookback_days=5)
        self.assertEqual(len(values), 5)
        self.assertEqual(values.count(0.0), 4)
        self.assertEqual(sum(values), 4.0)


class ForecastServiceTests(TestCase):
    def setUp(self):
        ensure_business_settings()
        self.owner = create_owner()
        self.product = create_product(stock=50, name='Juice')

    def test_insufficient_history_does_not_forecast(self):
        _seed_daily_sales(self.product, self.owner, days=8, qty_per_day=2)
        result = forecast_product_demand(self.product)
        self.assertEqual(result.status, STATUS_INSUFFICIENT_DATA)
        self.assertIsNone(result.predicted_daily_demand)
        self.assertIsNone(result.model_name)
        self.assertEqual(result.fallback, 'Historical ADS')
        self.assertLess(result.historical_observations, MIN_HISTORICAL_DAYS)

    def test_zero_sales_history_is_insufficient(self):
        result = forecast_product_demand(self.product)
        self.assertEqual(result.status, STATUS_INSUFFICIENT_DATA)
        self.assertIsNone(result.predicted_daily_demand)

    def test_forecast_generated_with_sufficient_data(self):
        _seed_daily_sales(self.product, self.owner, days=45, qty_per_day=4)
        result = forecast_product_demand(self.product)
        self.assertEqual(result.status, STATUS_FORECAST_AVAILABLE)
        self.assertEqual(result.model_name, 'ARIMA')
        self.assertIsNotNone(result.predicted_daily_demand)
        self.assertGreaterEqual(result.predicted_daily_demand, Decimal('0'))
        self.assertEqual(result.forecast_horizon, 7)

    def test_forecast_does_not_produce_negative_demand(self):
        _seed_daily_sales(self.product, self.owner, days=40, qty_per_day=1)
        result = forecast_product_demand(self.product)
        if result.predicted_daily_demand is not None:
            self.assertGreaterEqual(result.predicted_daily_demand, Decimal('0'))


class RecommendationForecastIntegrationTests(TestCase):
    def setUp(self):
        ensure_business_settings()
        self.owner = create_owner()
        self.product = create_product(stock=2, name='Juice')

    def test_existing_recommendation_generation_still_works(self):
        _seed_daily_sales(self.product, self.owner, days=10, qty_per_day=5)
        results = generate_recommendations()
        self.assertIn('created', results)
        self.assertGreaterEqual(results['created'] + results['updated'] + results['skipped'], 1)

    def test_ads_fallback_when_forecast_unavailable(self):
        _seed_daily_sales(self.product, self.owner, days=5, qty_per_day=6)
        ads, _, _, rop, _, demand_method = calculate_reorder_metrics(self.product)
        self.assertEqual(demand_method, ReorderRecommendation.DemandMethod.HISTORICAL_ADS)
        self.assertGreater(rop, Decimal('0'))
        self.assertGreater(ads, Decimal('0'))

    def test_forecasted_demand_used_when_available(self):
        _seed_daily_sales(self.product, self.owner, days=45, qty_per_day=5)
        ads, _, _, rop, event_names, demand_method = calculate_reorder_metrics(self.product)
        self.assertEqual(demand_method, ReorderRecommendation.DemandMethod.ARIMA_FORECAST)
        self.assertEqual(event_names, [])
        self.assertGreater(rop, Decimal('0'))
        self.assertGreater(ads, Decimal('0'))

    def test_seasonal_multiplier_not_applied_on_arima_path(self):
        SeasonalEvent.objects.create(
            name='Festival',
            start_date=timezone.localdate() - timedelta(days=1),
            end_date=timezone.localdate() + timedelta(days=10),
            category=self.product.category,
            multiplier=Decimal('2.00'),
            is_active=True,
        )
        _seed_daily_sales(self.product, self.owner, days=45, qty_per_day=4)
        _, _, _, _, event_names, demand_method = calculate_reorder_metrics(self.product)
        self.assertEqual(demand_method, ReorderRecommendation.DemandMethod.ARIMA_FORECAST)
        self.assertEqual(event_names, [])

    def test_generate_does_not_auto_create_purchase_orders(self):
        _seed_daily_sales(self.product, self.owner, days=45, qty_per_day=5)
        before = PurchaseOrder.objects.count()
        generate_recommendations()
        self.assertEqual(PurchaseOrder.objects.count(), before)
        rec = ReorderRecommendation.objects.filter(product=self.product).first()
        if rec:
            self.assertEqual(rec.status, ReorderRecommendation.Status.PENDING)

    def test_forecasting_does_not_modify_inventory_or_sales(self):
        _seed_daily_sales(self.product, self.owner, days=40, qty_per_day=3)
        stock_before = self.product.current_stock
        sales_before = Sale.objects.count()
        forecast_product_demand(self.product)
        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, stock_before)
        self.assertEqual(Sale.objects.count(), sales_before)


class DemandForecastAPITests(TestCase):
    def setUp(self):
        ensure_business_settings()
        self.owner = create_owner()
        self.client = auth_client(self.owner)
        self.product = create_product(stock=20, name='Sikhar Ice')

    def test_forecast_api_insufficient_data(self):
        _seed_daily_sales(self.product, self.owner, days=5, qty_per_day=1)
        response = self.client.get('/api/analytics/forecast/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 1)
        row = next(r for r in response.data if r['product_name'] == 'Sikhar Ice' or r.get('product') == 'Sikhar Ice')
        self.assertEqual(row['status'], STATUS_INSUFFICIENT_DATA)
        self.assertIsNone(row['predicted_daily_demand'])

    def test_forecast_api_available(self):
        _seed_daily_sales(self.product, self.owner, days=40, qty_per_day=3)
        response = self.client.get('/api/analytics/forecast/?refresh=true')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        row = response.data[0]
        self.assertEqual(row['status'], STATUS_FORECAST_AVAILABLE)
        self.assertIsNotNone(row['predicted_daily_demand'])

    def test_demand_forecast_report(self):
        DemandForecast.objects.create(
            product=self.product,
            forecast_date=timezone.localdate(),
            forecast_horizon=7,
            predicted_daily_demand=None,
            status=DemandForecast.Status.INSUFFICIENT_DATA,
            historical_observations=8,
            historical_ads=Decimal('0.50'),
        )
        response = self.client.get('/api/reports/demand-forecast/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('rows', response.data)
        self.assertIn('summary', response.data)

    def test_demand_forecast_csv_export(self):
        response = self.client.get('/api/reports/demand-forecast/export/?export_format=csv')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('text/csv', response['Content-Type'])
