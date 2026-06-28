from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework import status

from apps.purchasing.models import PurchaseOrder, ReorderRecommendation
from apps.purchasing.services import approve_recommendation, generate_recommendations
from apps.sales.models import Sale
from common.test_utils import auth_client, create_owner, create_product


class RecommendationTests(TestCase):
    def setUp(self):
        self.owner = create_owner()
        self.client = auth_client(self.owner)
        self.product = create_product(stock=100)
        for _ in range(10):
            Sale.record_sale(self.product, 2, Decimal('10.00'), self.owner)
        self.product.refresh_from_db()
        # Simulate depleted stock without using the product API.
        type(self.product).objects.filter(pk=self.product.pk).update(current_stock=0)
        self.product.refresh_from_db()

    def test_generate_recommendation_for_low_stock(self):
        results = generate_recommendations()
        self.assertGreaterEqual(results['created'], 1)
        rec = ReorderRecommendation.objects.get(
            product=self.product,
            status=ReorderRecommendation.Status.PENDING,
        )
        self.assertEqual(rec.unit_profit, Decimal('5.00'))
        self.assertGreater(rec.priority_score, Decimal('0'))
        self.assertEqual(
            rec.expected_restock_profit,
            rec.unit_profit * rec.recommended_quantity,
        )
        self.assertIn(rec.priority_level, ReorderRecommendation.PriorityLevel.values)

    def test_recommendations_api_ordered_by_priority_score(self):
        generate_recommendations()
        response = self.client.get('/api/recommendations/?status=pending')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        if len(results) >= 2:
            self.assertGreaterEqual(
                Decimal(results[0]['priority_score']),
                Decimal(results[1]['priority_score']),
            )

    def test_approve_recommendation_creates_draft_po(self):
        rec = ReorderRecommendation.objects.create(
            product=self.product,
            supplier=self.product.supplier,
            current_stock=0,
            recommended_quantity=10,
            average_daily_sales=Decimal('1.00'),
            lead_time_days=5,
            safety_stock=Decimal('3.00'),
            calculated_reorder_point=Decimal('8.00'),
            reason='Test',
        )
        response = self.client.post(f'/api/recommendations/{rec.id}/approve/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        rec.refresh_from_db()
        self.assertEqual(rec.status, ReorderRecommendation.Status.APPROVED)
        self.assertIsNotNone(rec.purchase_order)
        self.assertEqual(rec.purchase_order.status, PurchaseOrder.Status.DRAFT)


class PurchaseOrderWorkflowTests(TestCase):
    def setUp(self):
        self.owner = create_owner()
        self.client = auth_client(self.owner)
        self.product = create_product(stock=5)
        self.rec = ReorderRecommendation.objects.create(
            product=self.product,
            supplier=self.product.supplier,
            current_stock=5,
            recommended_quantity=10,
            average_daily_sales=Decimal('2.00'),
            lead_time_days=5,
            safety_stock=Decimal('6.00'),
            calculated_reorder_point=Decimal('16.00'),
            reason='Test',
        )
        self.po = approve_recommendation(self.rec, self.owner)

    def test_draft_to_ordered_to_received_updates_stock(self):
        response = self.client.patch(
            f'/api/purchase-orders/{self.po.id}/status/',
            {'status': 'ordered'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.po.refresh_from_db()
        self.assertEqual(self.po.status, PurchaseOrder.Status.ORDERED)
        self.assertIsNotNone(self.po.ordered_at)
        self.assertIsNotNone(self.po.expected_delivery_date)
        self.assertGreaterEqual(self.po.expected_delivery_date, self.po.ordered_at)

        response = self.client.patch(
            f'/api/purchase-orders/{self.po.id}/status/',
            {
                'status': 'received',
                'actual_delivery_date': str(timezone.now().date()),
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, 15)

    def test_actual_delivery_before_order_date_rejected(self):
        self.client.patch(
            f'/api/purchase-orders/{self.po.id}/status/',
            {'status': 'ordered'},
            format='json',
        )
        self.po.refresh_from_db()
        early_date = self.po.ordered_at - timedelta(days=1)
        response = self.client.patch(
            f'/api/purchase-orders/{self.po.id}/status/',
            {
                'status': 'received',
                'actual_delivery_date': str(early_date),
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
