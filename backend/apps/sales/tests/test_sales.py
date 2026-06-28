from django.test import TestCase
from rest_framework import status

from apps.notifications.models import Notification
from apps.sales.models import Sale
from common.test_utils import auth_client, create_owner, create_product


class SalesTests(TestCase):
    def setUp(self):
        self.owner = create_owner()
        self.client = auth_client(self.owner)
        self.product = create_product(stock=10)

    def test_sale_reduces_stock(self):
        response = self.client.post('/api/sales/', {
            'product': self.product.id,
            'quantity': 3,
            'unit_price': '10.00',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, 7)
        self.assertEqual(Sale.objects.count(), 1)

    def test_insufficient_stock_rejected(self):
        response = self.client.post('/api/sales/', {
            'product': self.product.id,
            'quantity': 100,
            'unit_price': '10.00',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, 10)

    def test_out_of_stock_notification(self):
        self.client.post('/api/sales/', {
            'product': self.product.id,
            'quantity': 10,
            'unit_price': '10.00',
        })
        self.assertTrue(
            Notification.objects.filter(
                notification_type=Notification.Type.OUT_OF_STOCK,
                related_product=self.product,
            ).exists()
        )
