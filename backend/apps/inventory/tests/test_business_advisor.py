from datetime import datetime, timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework import status

from apps.analytics.models import DeadStockSnapshot, SupplierPerformanceSnapshot
from apps.inventory.business_advisor import get_dashboard_greeting
from apps.purchasing.models import ProfitAdvisorAnalysis, PurchaseOrder, ReorderRecommendation
from apps.sales.models import Sale
from common.test_utils import auth_client, create_category, create_owner, create_product, create_supplier


class BusinessAdvisorTests(TestCase):
    def setUp(self):
        self.owner = create_owner()
        self.client = auth_client(self.owner)
        self.supplier = create_supplier()
        self.category = create_category()

    def test_greeting_changes_by_time(self):
        self.assertEqual(
            get_dashboard_greeting(timezone.make_aware(datetime(2026, 1, 1, 8, 0))),
            'Good Morning',
        )
        self.assertEqual(
            get_dashboard_greeting(timezone.make_aware(datetime(2026, 1, 1, 14, 0))),
            'Good Afternoon',
        )
        self.assertEqual(
            get_dashboard_greeting(timezone.make_aware(datetime(2026, 1, 1, 19, 0))),
            'Good Evening',
        )
        self.assertEqual(
            get_dashboard_greeting(timezone.make_aware(datetime(2026, 1, 1, 2, 0))),
            'Working Late?',
        )

    def test_dashboard_returns_healthy_message_when_no_signals(self):
        response = self.client.get('/api/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('greeting', response.data)
        self.assertEqual(response.data['business_advisor'], ['Everything looks healthy today.'])

    def test_business_advisor_messages_from_existing_data(self):
        low_stock_product = create_product(
            supplier=self.supplier,
            category=self.category,
            stock=2,
        )
        for _ in range(30):
            Sale.objects.create(
                product=low_stock_product,
                quantity=1,
                unit_price=Decimal('10.00'),
                total_amount=Decimal('10.00'),
                discount_amount=Decimal('0.00'),
                recorded_by=self.owner,
            )

        out_of_stock_product = create_product(
            supplier=self.supplier,
            category=self.category,
            stock=0,
            sku='OOS-1',
            name='Out of Stock Product',
        )
        DeadStockSnapshot.objects.create(
            product=out_of_stock_product,
            days_without_sale=130,
            current_stock=0,
            inventory_value=Decimal('0.00'),
            severity=DeadStockSnapshot.Severity.CRITICAL,
        )

        ReorderRecommendation.objects.create(
            product=low_stock_product,
            supplier=self.supplier,
            current_stock=2,
            recommended_quantity=10,
            average_daily_sales=Decimal('1.00'),
            lead_time_days=5,
            safety_stock=Decimal('3.00'),
            calculated_reorder_point=Decimal('8.00'),
            status=ReorderRecommendation.Status.PENDING,
            reason='Test',
        )

        PurchaseOrder.objects.create(
            po_number=PurchaseOrder.generate_po_number(),
            supplier=self.supplier,
            created_by=self.owner,
            status=PurchaseOrder.Status.ORDERED,
            created_from=PurchaseOrder.Source.MANUAL,
        )
        delayed_po = PurchaseOrder.objects.create(
            po_number=PurchaseOrder.generate_po_number(),
            supplier=self.supplier,
            created_by=self.owner,
            status=PurchaseOrder.Status.RECEIVED,
            created_from=PurchaseOrder.Source.MANUAL,
            expected_delivery_date=timezone.now().date() - timedelta(days=3),
            actual_delivery_date=timezone.now().date() - timedelta(days=1),
        )
        delayed_po.save()

        SupplierPerformanceSnapshot.objects.create(
            supplier=self.supplier,
            avg_promised_lead_time=Decimal('3.00'),
            avg_actual_lead_time=Decimal('4.00'),
            avg_delay_days=Decimal('1.00'),
            on_time_delivery_rate=Decimal('80.00'),
            total_orders=5,
            snapshot_date=timezone.now().date(),
        )

        ProfitAdvisorAnalysis.objects.create(
            budget=Decimal('1000.00'),
            recommended_spending=Decimal('600.00'),
            remaining_budget=Decimal('400.00'),
            expected_profit=Decimal('1200.00'),
            recommended_count=2,
            explanation='Test',
            recommended_products=[],
            deferred_products=[],
            created_by=self.owner,
        )

        response = self.client.get('/api/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        advisor = response.data['business_advisor']
        self.assertTrue(any('running low' in message for message in advisor))
        self.assertTrue(any('out of stock' in message for message in advisor))
        self.assertTrue(any('usually delivers in' in message for message in advisor))
        self.assertTrue(any('later than promised' in message for message in advisor))
        self.assertTrue(any('awaiting delivery' in message for message in advisor))
        self.assertTrue(any('not sold for over 120 days' in message for message in advisor))
        self.assertTrue(any('Profit Advisor analysis recommends purchasing' in message for message in advisor))
        self.assertTrue(any('require restocking' in message for message in advisor))
        self.assertEqual(len(advisor), len(set(advisor)))
