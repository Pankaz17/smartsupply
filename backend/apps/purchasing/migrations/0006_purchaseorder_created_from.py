from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('purchasing', '0005_operational_priority'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchaseorder',
            name='created_from',
            field=models.CharField(
                choices=[('recommendation', 'Recommendation'), ('manual', 'Manual')],
                default='manual',
                max_length=20,
            ),
        ),
    ]
