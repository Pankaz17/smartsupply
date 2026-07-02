# Generated manually for Phase 9.2

from django.db import migrations, models


def backfill_operational_priorities(apps, schema_editor):
    from apps.purchasing.operational_priority import update_operational_priorities
    update_operational_priorities()


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
