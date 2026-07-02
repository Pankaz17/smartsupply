from django.test import TestCase
from rest_framework import status

from apps.analytics.dead_stock_advisor import get_dead_stock_suggestions
from apps.analytics.models import DeadStockSnapshot
from common.test_utils import auth_client, create_category, create_owner, create_product, create_supplier


class DeadStockAdvisorTests(TestCase):
    def test_suggestions_60_to_89_days(self):
        self.assertEqual(
            get_dead_stock_suggestions(70),
            ['Run a Discount Campaign'],
        )

    def test_suggestions_90_to_119_days(self):
        self.assertEqual(
            get_dead_stock_suggestions(95),
            [
                'Bundle with a Popular Product',
                'Run a Discount Campaign',
            ],
        )

    def test_suggestions_120_plus_days(self):
        self.assertEqual(
            get_dead_stock_suggestions(130),
            [
                'Stop Reordering',
                'Bundle Remaining Stock',
                'Heavy Discount Campaign',
            ],
        )

    def test_suggestions_below_60_days(self):
        self.assertEqual(get_dead_stock_suggestions(45), [])

    def test_api_includes_suggestions(self):
        owner = create_owner()
        supplier = create_supplier()
        category = create_category()
        product = create_product(
            sku='DEAD1',
            name='Orange Juice',
            supplier=supplier,
            category=category,
            stock=50,
        )
        DeadStockSnapshot.objects.create(
            product=product,
            days_without_sale=95,
            current_stock=50,
            inventory_value='10000.00',
            severity=DeadStockSnapshot.Severity.CRITICAL,
        )

        response = auth_client(owner).get('/api/dead-stock/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 1)
        self.assertIn('Bundle with a Popular Product', results[0]['suggestions'])
        self.assertIn('Run a Discount Campaign', results[0]['suggestions'])

    def test_dead_stock_report_includes_suggested_action(self):
        owner = create_owner()
        supplier = create_supplier()
        category = create_category()
        product = create_product(
            sku='DEAD2',
            name='Stale Bread',
            supplier=supplier,
            category=category,
            stock=10,
        )
        DeadStockSnapshot.objects.create(
            product=product,
            days_without_sale=130,
            current_stock=10,
            inventory_value='500.00',
            severity=DeadStockSnapshot.Severity.CRITICAL,
        )

        response = auth_client(owner).get('/api/reports/dead-stock/?range=30d')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['rows']), 0)
        row = response.data['rows'][0]
        self.assertIn('Stop Reordering', row['suggested_action'])
        self.assertIn('Heavy Discount Campaign', row['suggestions'])

    def test_dashboard_advisory_for_120_plus_days(self):
        from apps.notifications.services import get_dashboard_alerts

        owner = create_owner()
        supplier = create_supplier()
        category = create_category()
        product = create_product(
            sku='DEAD3',
            name='Old Stock',
            supplier=supplier,
            category=category,
            stock=5,
        )
        DeadStockSnapshot.objects.create(
            product=product,
            days_without_sale=125,
            current_stock=5,
            inventory_value='250.00',
            severity=DeadStockSnapshot.Severity.CRITICAL,
        )

        alerts = get_dashboard_alerts()
        self.assertTrue(
            any('unsold for over 120 days' in alert for alert in alerts),
        )

        response = auth_client(owner).get('/api/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            any('unsold for over 120 days' in alert
                for alert in response.data['dashboard_alerts']),
        )
