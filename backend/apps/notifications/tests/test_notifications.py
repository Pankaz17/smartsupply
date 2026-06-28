from decimal import Decimal

from django.test import TestCase

from apps.notifications.models import Notification
from apps.notifications.services import check_stock_notifications
from apps.purchasing.services import calculate_reorder_metrics
from apps.sales.models import Sale
from common.test_utils import create_owner, create_product


class NotificationTests(TestCase):
    def setUp(self):
        self.owner = create_owner()
        self.product = create_product(stock=100)
        for _ in range(15):
            Sale.record_sale(self.product, 2, Decimal('10.00'), self.owner)
        self.product.refresh_from_db()

    def test_low_stock_notification(self):
        _, _, _, reorder_point, _ = calculate_reorder_metrics(self.product)
        low_stock = max(1, int(reorder_point))
        type(self.product).objects.filter(pk=self.product.pk).update(current_stock=low_stock)
        self.product.refresh_from_db()
        check_stock_notifications(self.product)
        self.assertTrue(
            Notification.objects.filter(
                notification_type=Notification.Type.LOW_STOCK,
                related_product=self.product,
            ).exists()
        )

    def test_out_of_stock_notification(self):
        type(self.product).objects.filter(pk=self.product.pk).update(current_stock=0)
        self.product.refresh_from_db()
        check_stock_notifications(self.product)
        self.assertTrue(
            Notification.objects.filter(
                notification_type=Notification.Type.OUT_OF_STOCK,
                related_product=self.product,
            ).exists()
        )

    def test_duplicate_notifications_not_created(self):
        type(self.product).objects.filter(pk=self.product.pk).update(current_stock=0)
        self.product.refresh_from_db()
        check_stock_notifications(self.product)
        check_stock_notifications(self.product)
        count = Notification.objects.filter(
            notification_type=Notification.Type.OUT_OF_STOCK,
            related_product=self.product,
            is_read=False,
        ).count()
        self.assertEqual(count, 1)
