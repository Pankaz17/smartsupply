from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework import status

from apps.analytics.models import SupplierPerformanceSnapshot
from apps.analytics.supplier_insights import build_supplier_insights
from apps.purchasing.models import PurchaseOrder
from common.test_utils import auth_client, create_owner, create_supplier


class SupplierInsightsTests(TestCase):
    def setUp(self):
        self.owner = create_owner()
        self.client = auth_client(self.owner)
        self.supplier = create_supplier(name='ABC Supplier')

    def _snapshot(self, **kwargs):
        defaults = {
            'supplier': self.supplier,
            'avg_promised_lead_time': Decimal('3.00'),
            'avg_actual_lead_time': Decimal('4.00'),
            'avg_delay_days': Decimal('1.00'),
            'on_time_delivery_rate': Decimal('88.00'),
            'total_orders': 6,
            'snapshot_date': timezone.now().date(),
        }
        defaults.update(kwargs)
        return SupplierPerformanceSnapshot.objects.create(**defaults)

    def _received_po(self, expected_offset_days=0, actual_offset_days=0):
        today = timezone.now().date()
        return PurchaseOrder.objects.create(
            po_number=PurchaseOrder.generate_po_number(),
            supplier=self.supplier,
            created_by=self.owner,
            status=PurchaseOrder.Status.RECEIVED,
            created_from=PurchaseOrder.Source.MANUAL,
            expected_delivery_date=today + timedelta(days=expected_offset_days),
            actual_delivery_date=today + timedelta(days=actual_offset_days),
        )

    def test_new_supplier_message_when_fewer_than_three_completed_orders(self):
        self._snapshot(total_orders=2)
        self._received_po(0, 0)
        self._received_po(0, 1)
        response = self.client.get('/api/supplier-analytics/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.data.get('results', response.data)[0]
        self.assertEqual(
            payload['supplier_insights'],
            ['Not enough purchase history to evaluate this supplier.'],
        )

    def test_supplier_insights_messages_match_metrics(self):
        self._snapshot(avg_actual_lead_time=Decimal('4.00'), avg_delay_days=Decimal('1.00'), on_time_delivery_rate=Decimal('88.00'))
        # 5 on-time recent orders for consistency insight
        for _ in range(5):
            self._received_po(0, 0)
        insights = build_supplier_insights(SupplierPerformanceSnapshot.objects.get(supplier=self.supplier))
        self.assertTrue(any('usually delivers in 4 days' in msg for msg in insights))
        self.assertTrue(any('Average delivery delay is 1 day.' in msg for msg in insights))
        self.assertTrue(any('Reliability: Good.' in msg for msg in insights))
        self.assertTrue(any('delivered on time for the last 5 purchase orders' in msg for msg in insights))

    def test_delay_trend_appears_for_multiple_recent_delays(self):
        self._snapshot(avg_delay_days=Decimal('2.00'), on_time_delivery_rate=Decimal('60.00'))
        # recent five: 2 delays
        self._received_po(0, 1)
        self._received_po(0, 2)
        self._received_po(0, 0)
        self._received_po(0, 0)
        self._received_po(0, 0)
        insights = build_supplier_insights(SupplierPerformanceSnapshot.objects.get(supplier=self.supplier))
        self.assertTrue(any('recently delivered later than promised' in msg for msg in insights))
