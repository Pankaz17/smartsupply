from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework import status

from apps.purchasing.models import PurchaseOrder, ReorderRecommendation
from apps.purchasing.services import approve_recommendation, generate_recommendations
from apps.sales.models import Sale
from common.test_utils import auth_client, create_owner, create_product, create_staff


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
        self.assertTrue(
            ReorderRecommendation.objects.filter(
                product=self.product,
                status=ReorderRecommendation.Status.PENDING,
            ).exists()
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
        self.assertEqual(rec.purchase_order.created_from, PurchaseOrder.Source.RECOMMENDATION)

    def test_owner_can_create_manual_draft_purchase_order(self):
        response = self.client.post(
            '/api/purchase-orders/',
            {
                'supplier': self.product.supplier_id,
                'product': self.product.id,
                'quantity': 4,
                'notes': 'Initial stock buy',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        po = PurchaseOrder.objects.get(pk=response.data['id'])
        self.assertEqual(po.status, PurchaseOrder.Status.DRAFT)
        self.assertEqual(po.created_from, PurchaseOrder.Source.MANUAL)
        item = po.items.get()
        self.assertEqual(item.quantity, 4)
        self.assertEqual(item.product_id, self.product.id)
        self.assertEqual(item.unit_cost, self.product.cost_price)

    def test_manual_po_validates_product_supplier_match(self):
        other = create_product(stock=3)
        response = self.client.post(
            '/api/purchase-orders/',
            {
                'supplier': self.product.supplier_id,
                'product': other.id,
                'quantity': 2,
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('product', response.data)

    def test_staff_cannot_create_manual_po(self):
        staff_client = auth_client(create_staff())
        response = staff_client.post(
            '/api/purchase-orders/',
            {
                'supplier': self.product.supplier_id,
                'product': self.product.id,
                'quantity': 1,
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


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

    def test_manual_po_uses_same_status_workflow_and_updates_stock_once(self):
        create_response = self.client.post(
            '/api/purchase-orders/',
            {
                'supplier': self.product.supplier_id,
                'product': self.product.id,
                'quantity': 5,
                'unit_cost': '4.50',
            },
            format='json',
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        po_id = create_response.data['id']
        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, 5)

        ordered = self.client.patch(
            f'/api/purchase-orders/{po_id}/status/',
            {'status': 'ordered'},
            format='json',
        )
        self.assertEqual(ordered.status_code, status.HTTP_200_OK)

        received = self.client.patch(
            f'/api/purchase-orders/{po_id}/status/',
            {'status': 'received', 'actual_delivery_date': str(timezone.now().date())},
            format='json',
        )
        self.assertEqual(received.status_code, status.HTTP_200_OK)

        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, 10)

        second_receive = self.client.patch(
            f'/api/purchase-orders/{po_id}/status/',
            {'status': 'received', 'actual_delivery_date': str(timezone.now().date())},
            format='json',
        )
        self.assertEqual(second_receive.status_code, status.HTTP_400_BAD_REQUEST)
