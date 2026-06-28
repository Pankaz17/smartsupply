from django.test import TestCase
from rest_framework import status

from common.test_utils import auth_client, create_owner, create_product, ensure_business_settings


class ReportsTests(TestCase):
    def setUp(self):
        ensure_business_settings()
        self.owner = create_owner()
        self.client = auth_client(self.owner)
        create_product(stock=10)

    def test_inventory_report(self):
        response = self.client.get('/api/reports/inventory/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('summary', response.data)
        self.assertIn('rows', response.data)
        self.assertGreater(response.data['summary']['total_products'], 0)

    def test_inventory_csv_export(self):
        response = self.client.get('/api/reports/inventory/export/?export_format=csv')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('text/csv', response['Content-Type'])

    def test_inventory_xlsx_export(self):
        response = self.client.get('/api/reports/inventory/export/?export_format=xlsx')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('spreadsheetml', response['Content-Type'])

    def test_invalid_date_range_returns_400(self):
        response = self.client.get('/api/reports/sales/?start_date=not-a-date&end_date=2026-01-01')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_range_preset_returns_400(self):
        response = self.client.get('/api/reports/sales/?range=365d')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
