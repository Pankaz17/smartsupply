from decimal import Decimal

from django.test import TestCase
from rest_framework import status

from apps.purchasing.models import ReorderRecommendation
from apps.purchasing.operational_priority import (
    calculate_urgency_score,
    update_operational_priorities,
)
from apps.purchasing.profit_advisor import run_profit_advisor_analysis
from apps.purchasing.services import generate_recommendations
from common.test_utils import auth_client, create_category, create_owner, create_product, create_supplier


class OperationalPriorityTests(TestCase):
    def setUp(self):
        self.owner = create_owner()
        self.supplier = create_supplier()
        self.category = create_category()

        self.critical = create_product(
            sku='CRIT',
            name='Critical Stock',
            supplier=self.supplier,
            category=self.category,
            cost_price=Decimal('1.00'),
            selling_price=Decimal('5.00'),
            stock=0,
        )
        self.moderate = create_product(
            sku='MOD',
            name='Moderate Stock',
            supplier=self.supplier,
            category=self.category,
            cost_price=Decimal('1.00'),
            selling_price=Decimal('5.00'),
            stock=5,
        )

        ReorderRecommendation.objects.create(
            product=self.critical,
            supplier=self.supplier,
            current_stock=0,
            recommended_quantity=20,
            average_daily_sales=Decimal('10.00'),
            lead_time_days=7,
            safety_stock=Decimal('30.00'),
            calculated_reorder_point=Decimal('100.00'),
            status=ReorderRecommendation.Status.PENDING,
            reason='Test',
        )
        ReorderRecommendation.objects.create(
            product=self.moderate,
            supplier=self.supplier,
            current_stock=5,
            recommended_quantity=5,
            average_daily_sales=Decimal('1.00'),
            lead_time_days=3,
            safety_stock=Decimal('3.00'),
            calculated_reorder_point=Decimal('10.00'),
            status=ReorderRecommendation.Status.PENDING,
            reason='Test',
        )

    def test_urgency_ignores_profit_pricing(self):
        critical_rec = ReorderRecommendation.objects.get(product=self.critical)
        moderate_rec = ReorderRecommendation.objects.get(product=self.moderate)

        critical_rec.product.cost_price = Decimal('999.00')
        critical_rec.product.selling_price = Decimal('1000.00')
        moderate_rec.product.cost_price = Decimal('0.01')
        moderate_rec.product.selling_price = Decimal('100.00')

        self.assertGreater(
            calculate_urgency_score(critical_rec),
            calculate_urgency_score(moderate_rec),
        )

    def test_pending_recommendations_receive_priority_levels(self):
        update_operational_priorities()
        levels = set(
            ReorderRecommendation.objects.filter(
                status=ReorderRecommendation.Status.PENDING,
            ).values_list('priority_level', flat=True),
        )
        self.assertTrue(levels.issubset({'HIGH', 'MEDIUM', 'LOW'}))
        self.assertIn('HIGH', levels)

    def test_api_lists_by_operational_priority(self):
        update_operational_priorities()
        client = auth_client(self.owner)
        response = client.get('/api/recommendations/?status=pending')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        self.assertEqual(results[0]['priority_level'], 'HIGH')

    def test_profit_advisor_does_not_change_operational_priority(self):
        update_operational_priorities()
        before = {
            r.product_id: r.priority_level
            for r in ReorderRecommendation.objects.filter(status='pending')
        }
        run_profit_advisor_analysis(Decimal('100.00'))
        after = {
            r.product_id: r.priority_level
            for r in ReorderRecommendation.objects.filter(status='pending')
        }
        self.assertEqual(before, after)

    def test_generate_recommendations_assigns_priority(self):
        self.critical.current_stock = 0
        self.critical.save()
        self.moderate.current_stock = 0
        self.moderate.save()
        generate_recommendations()
        pending = ReorderRecommendation.objects.filter(status='pending')
        self.assertTrue(all(r.priority_level in ('HIGH', 'MEDIUM', 'LOW') for r in pending))

    def test_dashboard_includes_top_operational_priorities(self):
        update_operational_priorities()
        client = auth_client(self.owner)
        response = client.get('/api/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('top_operational_priorities', response.data)
        self.assertGreater(len(response.data['top_operational_priorities']), 0)
