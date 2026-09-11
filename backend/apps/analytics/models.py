from decimal import Decimal

from django.db import models
from django.utils import timezone


class SeasonalEvent(models.Model):
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    category = models.ForeignKey(
        'products.ProductCategory',
        on_delete=models.CASCADE,
        related_name='seasonal_events',
    )
    multiplier = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=Decimal('1.00'),
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['start_date']

    def __str__(self):
        return f'{self.name} ({self.category.name})'


class DeadStockSnapshot(models.Model):
    class Severity(models.TextChoices):
        WARNING = 'warning', 'Warning'
        CRITICAL = 'critical', 'Critical'

    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='dead_stock_snapshots',
        unique=True,
    )
    days_without_sale = models.PositiveIntegerField()
    current_stock = models.PositiveIntegerField()
    inventory_value = models.DecimalField(max_digits=12, decimal_places=2)
    severity = models.CharField(max_length=10, choices=Severity.choices)
    detected_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-detected_at']
        get_latest_by = 'detected_at'

    def __str__(self):
        return f'Dead stock: {self.product.name} ({self.severity})'


class SupplierPerformanceSnapshot(models.Model):
    supplier = models.ForeignKey(
        'suppliers.Supplier',
        on_delete=models.CASCADE,
        related_name='performance_snapshots',
    )
    avg_promised_lead_time = models.DecimalField(max_digits=6, decimal_places=2)
    avg_actual_lead_time = models.DecimalField(max_digits=6, decimal_places=2)
    avg_delay_days = models.DecimalField(max_digits=6, decimal_places=2)
    on_time_delivery_rate = models.DecimalField(max_digits=5, decimal_places=2)
    total_orders = models.PositiveIntegerField()
    snapshot_date = models.DateField()

    class Meta:
        ordering = ['-snapshot_date', 'supplier__name']
        unique_together = [('supplier', 'snapshot_date')]

    def __str__(self):
        return f'{self.supplier.name} @ {self.snapshot_date}'


class DemandForecast(models.Model):
    """Persisted ARIMA (or fallback) demand forecast for dashboard/reports."""

    class Status(models.TextChoices):
        FORECAST_AVAILABLE = 'FORECAST_AVAILABLE', 'Forecast Available'
        INSUFFICIENT_DATA = 'INSUFFICIENT_DATA', 'Insufficient Data'

    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='demand_forecasts',
    )
    forecast_date = models.DateField()
    forecast_horizon = models.PositiveIntegerField(default=7)
    predicted_daily_demand = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
    )
    predicted_horizon_total = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
    )
    model_name = models.CharField(max_length=32, blank=True, default='')
    historical_observations = models.PositiveIntegerField(default=0)
    historical_ads = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=32, choices=Status.choices)
    mae = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    trend = models.CharField(max_length=16, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-forecast_date', 'product__name']
        unique_together = [('product', 'forecast_date')]

    def __str__(self):
        return f'{self.product.name} forecast @ {self.forecast_date} ({self.status})'
