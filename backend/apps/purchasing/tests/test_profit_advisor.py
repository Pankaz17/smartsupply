from decimal import Decimal

from django.test import TestCase
from rest_framework import status

from apps.purchasing.models import ReorderRecommendation
from apps.purchasing.profit_advisor import run_profit_advisor_analysis
from common.test_utils import auth_client, create_category, create_owner, create_product, create_supplier


class ProfitAdvisorCalculationTests(TestCase):
    def setUp(self):
        self.owner = create_owner()
        self.supplier = create_supplier()
        self.category = create_category()

        self.high = create_product(
            sku='HIGH',
            name='Premium Juice',
            supplier=self.supplier,
            category=self.category,
            cost_price=Decimal('2.00'),
            selling_price=Decimal('10.00'),
            stock=0,
        )
        self.low = create_product(
            sku='LOW',
            name='Basic Water',
            supplier=self.supplier,
            category=self.category,
            cost_price=Decimal('0.90'),
            selling_price=Decimal('1.00'),
            stock=0,
        )

        for product, qty, ads in [
            (self.high, 10, Decimal('5.00')),
            (self.low, 10, Decimal('5.00')),
        ]:
            ReorderRecommendation.objects.create(
                product=product,
                supplier=self.supplier,
                current_stock=0,
                recommended_quantity=qty,
                average_daily_sales=ads,
                lead_time_days=5,
                safety_stock=Decimal('15.00'),
                calculated_reorder_point=Decimal('40.00'),
                status=ReorderRecommendation.Status.PENDING,
                reason='Test',
            )

    def test_unit_profit_and_priority_score(self):
        analysis = run_profit_advisor_analysis(Decimal('1000.00'))
        high = next(p for p in analysis['recommended_products'] + analysis['deferred_products']
                    if p['product'] == 'Premium Juice')
        self.assertEqual(Decimal(high['unit_profit']), Decimal('8.00'))
        self.assertEqual(Decimal(high['priority_score']), Decimal('40.00'))
        self.assertEqual(Decimal(high['expected_profit']), Decimal('80.00'))

    def test_budget_allocation(self):
        # Premium cost 20, Water cost 9 — budget 25 fits premium only
        analysis = run_profit_advisor_analysis(Decimal('25.00'))
        recommended = [p['product'] for p in analysis['recommended_products']]
        deferred = [p['product'] for p in analysis['deferred_products']]
        self.assertIn('Premium Juice', recommended)
        self.assertIn('Basic Water', deferred)
        self.assertLessEqual(Decimal(analysis['recommended_spending']), Decimal('25.00'))

    def test_large_budget_recommends_all(self):
        analysis = run_profit_advisor_analysis(Decimal('100000.00'))
        self.assertEqual(analysis['recommended_count'], 2)
        self.assertEqual(len(analysis['deferred_products']), 0)

    def test_api_owner_can_run_analysis(self):
        client = auth_client(self.owner)
        response = client.post(
            '/api/recommendations/profit-advisor/',
            {'budget': '30.00'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('recommended_products', response.data)
        self.assertIn('explanation', response.data)

    def test_api_rejects_zero_budget(self):
        client = auth_client(self.owner)
        response = client.post(
            '/api/recommendations/profit-advisor/',
            {'budget': '0'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_staff_cannot_run_analysis(self):
        from common.test_utils import create_staff
        staff = create_staff()
        client = auth_client(staff)
        response = client.post(
            '/api/recommendations/profit-advisor/',
            {'budget': '30.00'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_can_view_last_analysis(self):
        owner_client = auth_client(self.owner)
        owner_client.post(
            '/api/recommendations/profit-advisor/',
            {'budget': '30.00'},
            format='json',
        )
        from common.test_utils import create_staff
        staff_client = auth_client(create_staff())
        response = staff_client.get('/api/recommendations/profit-advisor/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['has_analysis'])
