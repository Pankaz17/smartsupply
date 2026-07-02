from decimal import Decimal
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import BusinessSettings, User
from apps.analytics.dead_stock_advisor import get_dead_stock_suggestions
from apps.analytics.models import DeadStockSnapshot
from apps.analytics.services import days_without_sale, update_dead_stock_snapshots
from apps.products.models import Product
from apps.sales.models import Sale


class SeedDeadStockDemoCommandTests(TestCase):
    def setUp(self):
        User.objects.create_user(
            email='owner@demo.com',
            password='testpass123',
            full_name='Demo Owner',
            role=User.Role.OWNER,
        )

    def test_seed_command_is_idempotent(self):
        out = StringIO()
        call_command('seed_dead_stock_demo', stdout=out)
        call_command('seed_dead_stock_demo', stdout=out)

        self.assertEqual(Product.objects.filter(name__in=['Juice', 'Cookies', 'Rice']).count(), 3)
        self.assertEqual(
            Sale.objects.filter(product__name__in=['Juice', 'Cookies', 'Rice']).count(),
            3,
        )

    def test_scenarios_produce_expected_days_and_suggestions(self):
        call_command('seed_dead_stock_demo', stdout=StringIO())
        update_dead_stock_snapshots()

        expectations = {
            'Juice': (70, ['Run a Discount Campaign']),
            'Cookies': (95, ['Bundle with a Popular Product', 'Run a Discount Campaign']),
            'Rice': (
                130,
                ['Stop Reordering', 'Bundle Remaining Stock', 'Heavy Discount Campaign'],
            ),
        }

        for name, (expected_days, expected_suggestions) in expectations.items():
            product = Product.objects.get(name=name)
            self.assertEqual(days_without_sale(product), expected_days)
            self.assertEqual(get_dead_stock_suggestions(expected_days), expected_suggestions)

            snapshot = DeadStockSnapshot.objects.get(product=product)
            self.assertEqual(snapshot.days_without_sale, expected_days)
            self.assertEqual(snapshot.current_stock, product.current_stock)

    def test_lowers_threshold_for_demo_visibility(self):
        settings = BusinessSettings.get_solo()
        settings.dead_stock_threshold_days = 90
        settings.save(update_fields=['dead_stock_threshold_days'])

        call_command('seed_dead_stock_demo', stdout=StringIO())
        settings.refresh_from_db()
        self.assertLessEqual(settings.dead_stock_threshold_days, 70)

        update_dead_stock_snapshots()
        self.assertTrue(DeadStockSnapshot.objects.filter(product__name='Juice').exists())

    def test_uses_existing_product_by_name(self):
        from apps.products.models import ProductCategory
        from apps.suppliers.models import Supplier

        supplier = Supplier.objects.create(name='Existing Supplier', promised_lead_time_days=3)
        category = ProductCategory.objects.create(name='Beverages')
        existing = Product.objects.create(
            sku='EXISTING-JUICE',
            name='Juice',
            category=category,
            supplier=supplier,
            cost_price=Decimal('1.00'),
            selling_price=Decimal('2.00'),
            current_stock=5,
        )

        call_command('seed_dead_stock_demo', stdout=StringIO())
        existing.refresh_from_db()

        self.assertEqual(Product.objects.filter(name='Juice').count(), 1)
        self.assertEqual(existing.pk, Product.objects.get(name='Juice').pk)
        self.assertEqual(existing.current_stock, 20)
