# Generated manually for Phase 10.1 DemandForecast

from decimal import Decimal

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analytics', '0001_initial'),
        ('products', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DemandForecast',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('forecast_date', models.DateField()),
                ('forecast_horizon', models.PositiveIntegerField(default=7)),
                ('predicted_daily_demand', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('predicted_horizon_total', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('model_name', models.CharField(blank=True, default='', max_length=32)),
                ('historical_observations', models.PositiveIntegerField(default=0)),
                ('historical_ads', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10)),
                ('status', models.CharField(choices=[('FORECAST_AVAILABLE', 'Forecast Available'), ('INSUFFICIENT_DATA', 'Insufficient Data')], max_length=32)),
                ('mae', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('trend', models.CharField(blank=True, default='', max_length=16)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='demand_forecasts', to='products.product')),
            ],
            options={
                'ordering': ['-forecast_date', 'product__name'],
                'unique_together': {('product', 'forecast_date')},
            },
        ),
    ]
