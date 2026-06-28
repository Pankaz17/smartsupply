from datetime import timedelta

from django.db import migrations, models


def backfill_ordered_at(apps, schema_editor):
    PurchaseOrder = apps.get_model('purchasing', 'PurchaseOrder')
    Supplier = apps.get_model('suppliers', 'Supplier')

    for po in PurchaseOrder.objects.filter(
        ordered_at__isnull=True,
        status__in=('ordered', 'received'),
    ):
        if po.expected_delivery_date:
            try:
                supplier = Supplier.objects.get(pk=po.supplier_id)
                po.ordered_at = po.expected_delivery_date - timedelta(
                    days=supplier.promised_lead_time_days,
                )
            except Supplier.DoesNotExist:
                po.ordered_at = po.updated_at.date()
        else:
            po.ordered_at = po.updated_at.date()
        po.save(update_fields=['ordered_at'])


class Migration(migrations.Migration):

    dependencies = [
        ('purchasing', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchaseorder',
            name='ordered_at',
            field=models.DateField(
                blank=True,
                help_text='Date the PO was marked as ordered. Set once on DRAFT → ORDERED.',
                null=True,
            ),
        ),
        migrations.RunPython(backfill_ordered_at, migrations.RunPython.noop),
    ]
