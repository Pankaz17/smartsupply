from django.test import TestCase
from rest_framework import status

from common.test_utils import auth_client, create_owner, create_product


class ProductStockIntegrityTests(TestCase):
    def setUp(self):
        self.owner = create_owner()
        self.client = auth_client(self.owner)
        self.product = create_product(stock=25)

    def test_cannot_update_stock_via_product_api(self):
        response = self.client.patch(
            f'/api/products/{self.product.id}/',
            {'current_stock': 999},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('current_stock', response.data)
        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, 25)

    def test_cannot_set_stock_on_create(self):
        category = self.product.category
        supplier = self.product.supplier
        response = self.client.post('/api/products/', {
            'sku': 'NEW-SKU',
            'name': 'New Product',
            'category': category.id,
            'supplier': supplier.id,
            'cost_price': '5.00',
            'selling_price': '10.00',
            'current_stock': 50,
            'unit': 'pcs',
            'is_active': True,
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
