from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.accounts.models import BusinessSettings, User
from apps.products.models import Product, ProductCategory
from apps.sales.models import Sale
from apps.suppliers.models import Supplier

DEMO_THRESHOLD_DAYS = 60

SCENARIOS = (
    {
        'name': 'Juice',
        'sku': 'DEMO-JUICE',
        'stock': 20,
        'days_without_sale': 70,
        'category': 'Beverages',
        'cost_price': Decimal('2.00'),
        'selling_price': Decimal('3.99'),
        'unit': Product.Unit.LITRE,
    },
    {
        'name': 'Cookies',
        'sku': 'DEMO-COOKIES',
        'stock': 15,
        'days_without_sale': 95,
        'category': 'Snacks',
        'cost_price': Decimal('1.50'),
        'selling_price': Decimal('2.99'),
        'unit': Product.Unit.PACK,
    },
    {
        'name': 'Rice',
        'sku': 'DEMO-RICE',
        'stock': 30,
        'days_without_sale': 130,
        'category': 'Groceries',
        'cost_price': Decimal('1.00'),
        'selling_price': Decimal('1.79'),
        'unit': Product.Unit.KG,
    },
)


class Command(BaseCommand):
    help = (
        'Seed development demo data for dead stock scenarios. '
        'Does not modify analytics logic — run run_nightly_analytics afterward.'
    )

    def handle(self, *args, **options):
        owner = User.objects.filter(role=User.Role.OWNER).first()
        if not owner:
            raise CommandError(
                'No owner account found. Create one first: '
                'python manage.py create_owner --email owner@example.com --password ...',
            )

        supplier, _ = Supplier.objects.get_or_create(
            name='Demo Supplier',
            defaults={
                'email': 'demo@supplier.com',
                'promised_lead_time_days': 5,
                'is_active': True,
            },
        )

        settings = BusinessSettings.get_solo()
        if settings.dead_stock_threshold_days > DEMO_THRESHOLD_DAYS:
            settings.dead_stock_threshold_days = DEMO_THRESHOLD_DAYS
            settings.save(update_fields=['dead_stock_threshold_days'])
            self.stdout.write(
                f'Set dead stock threshold to {DEMO_THRESHOLD_DAYS} days for demo visibility.',
            )

        today = timezone.now()
        seeded = []

        for scenario in SCENARIOS:
            category, _ = ProductCategory.objects.get_or_create(
                name=scenario['category'],
                defaults={'is_active': True},
            )

            product = (
                Product.objects.filter(name__iexact=scenario['name']).first()
                or Product.objects.filter(sku=scenario['sku']).first()
            )

            product_defaults = {
                'name': scenario['name'],
                'category': category,
                'supplier': supplier,
                'cost_price': scenario['cost_price'],
                'selling_price': scenario['selling_price'],
                'current_stock': scenario['stock'],
                'unit': scenario['unit'],
                'is_active': True,
            }

            if product:
                for field, value in product_defaults.items():
                    setattr(product, field, value)
                product.save()
            else:
                product, _ = Product.objects.update_or_create(
                    sku=scenario['sku'],
                    defaults=product_defaults,
                )

            Sale.objects.filter(product=product).delete()

            last_sale_at = today - timedelta(days=scenario['days_without_sale'])
            sale = Sale.objects.create(
                product=product,
                quantity=1,
                unit_price=product.selling_price,
                total_amount=product.selling_price,
                recorded_by=owner,
            )
            Sale.objects.filter(pk=sale.pk).update(created_at=last_sale_at)

            seeded.append((product.name, scenario['days_without_sale']))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Created demo dead stock scenarios.'))
        self.stdout.write('')
        self.stdout.write('Products:')
        for name, days in seeded:
            self.stdout.write(self.style.SUCCESS(f'  ✓ {name} ({days} days)'))
        self.stdout.write('')
        self.stdout.write('Now run:')
        self.stdout.write('')
        self.stdout.write('  python manage.py run_nightly_analytics')
        self.stdout.write('')
        self.stdout.write('Then open:')
        self.stdout.write('  Dead Stock page')
