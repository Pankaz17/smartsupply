# Generated manually for Phase 9.2

import math
from decimal import Decimal

from django.db import migrations, models


def backfill_operational_priorities(apps, schema_editor):
    """Backfill using historical models so later fields (e.g. demand_method) are not required."""
    ReorderRecommendation = apps.get_model('purchasing', 'ReorderRecommendation')
    pending = list(
        ReorderRecommendation.objects.filter(status='PENDING').select_related('product'),
    )
    if not pending:
        return

    def urgency_score(recommendation):
        stock = Decimal(recommendation.current_stock)
        reorder_point = recommendation.calculated_reorder_point
        ads = recommendation.average_daily_sales
        lead_time = recommendation.lead_time_days
        safety_stock = recommendation.safety_stock
        rop_safe = max(reorder_point, Decimal('1'))
        shortage = max(Decimal('0'), reorder_point - stock)
        shortage_ratio = float(shortage / rop_safe)
        return (
            shortage_ratio * 40.0
            + float(ads) * 8.0
            + float(lead_time) * 3.0
            + float(safety_stock / rop_safe) * 10.0
        )

    scored = [(rec, urgency_score(rec)) for rec in pending]
    scored.sort(key=lambda item: item[1], reverse=True)

    n = len(scored)
    if n == 1:
        levels = ['HIGH']
    elif n == 2:
        levels = ['HIGH', 'LOW']
    else:
        high_count = math.ceil(n * 0.25)
        low_count = math.ceil(n * 0.25)
        medium_count = n - high_count - low_count
        levels = (
            ['HIGH'] * high_count
            + ['MEDIUM'] * medium_count
            + ['LOW'] * low_count
        )

    for (recommendation, _), level in zip(scored, levels):
        recommendation.priority_level = level

    ReorderRecommendation.objects.bulk_update(pending, ['priority_level'])


class Migration(migrations.Migration):

    dependencies = [
        ('purchasing', '0004_profit_advisor_and_remove_priority'),
    ]

    operations = [
        migrations.AddField(
            model_name='reorderrecommendation',
            name='priority_level',
            field=models.CharField(
                choices=[('HIGH', 'High'), ('MEDIUM', 'Medium'), ('LOW', 'Low')],
                default='LOW',
                max_length=10,
            ),
        ),
        migrations.RunPython(backfill_operational_priorities, migrations.RunPython.noop),
    ]
