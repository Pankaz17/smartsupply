# Generated manually for Phase 10.1 demand_method on recommendations

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('purchasing', '0006_purchaseorder_created_from'),
    ]

    operations = [
        migrations.AddField(
            model_name='reorderrecommendation',
            name='demand_method',
            field=models.CharField(
                choices=[('historical_ads', 'Historical ADS'), ('arima_forecast', 'ARIMA Forecast')],
                default='historical_ads',
                help_text='Whether ROP used ARIMA forecast or historical ADS fallback.',
                max_length=20,
            ),
        ),
    ]
