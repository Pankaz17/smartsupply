from django.core.management.base import BaseCommand

from apps.accounts.models import BusinessSettings
from apps.products.models import Product, ProductCategory
from apps.suppliers.models import Supplier


class Command(BaseCommand):
    help = 'Seed sample categories, suppliers, and products for development.'

    def handle(self, *args, **options):
        settings = BusinessSettings.get_solo()

        beverages, _ = ProductCategory.objects.get_or_create(
            name='Beverages',
            defaults={'description': 'Drinks and beverages', 'is_active': True},
        )
        snacks, _ = ProductCategory.objects.get_or_create(
            name='Snacks',
            defaults={'description': 'Packaged snack foods', 'is_active': True},
        )

        acme, _ = Supplier.objects.get_or_create(
            name='Acme Wholesale',
            defaults={
                'email': 'orders@acme.com',
                'phone': '555-0100',
                'address': '123 Supply Lane',
                'promised_lead_time_days': 5,
                'is_active': True,
            },
        )
        fresh, _ = Supplier.objects.get_or_create(
            name='Fresh Foods Co.',
            defaults={
                'email': 'sales@freshfoods.com',
                'phone': '555-0200',
                'promised_lead_time_days': 3,
                'is_active': True,
            },
        )

        samples = [
            {
                'sku': 'BEV-001',
                'name': 'Cola 500ml',
                'category': beverages,
                'supplier': acme,
                'cost_price': '0.80',
                'selling_price': '1.50',
                'current_stock': 48,
                'unit': Product.Unit.PCS,
            },
            {
                'sku': 'SNK-001',
                'name': 'Potato Chips 150g',
                'category': snacks,
                'supplier': acme,
                'cost_price': '1.20',
                'selling_price': '2.49',
                'current_stock': 30,
                'unit': Product.Unit.PACK,
            },
            {
                'sku': 'BEV-002',
                'name': 'Orange Juice 1L',
                'category': beverages,
                'supplier': fresh,
                'cost_price': '2.00',
                'selling_price': '3.99',
                'current_stock': 0,
                'unit': Product.Unit.LITRE,
            },
        ]

        for data in samples:
            Product.objects.update_or_create(sku=data['sku'], defaults={**data, 'is_active': True})

        self.stdout.write(self.style.SUCCESS(
            f'Seed data ready for {settings.store_name}: '
            f'{ProductCategory.objects.count()} categories, '
            f'{Supplier.objects.count()} suppliers, '
            f'{Product.objects.count()} products.',
        ))
