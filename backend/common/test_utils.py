from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.accounts.models import BusinessSettings
from apps.products.models import Product, ProductCategory
from apps.suppliers.models import Supplier

User = get_user_model()


def create_owner(email='owner@test.com', password='testpass123'):
    return User.objects.create_user(
        email=email,
        password=password,
        full_name='Test Owner',
        role=User.Role.OWNER,
    )


def create_staff(email='staff@test.com', password='testpass123'):
    return User.objects.create_user(
        email=email,
        password=password,
        full_name='Test Staff',
        role=User.Role.STAFF,
    )


def auth_client(user, password='testpass123'):
    client = APIClient()
    response = client.post('/api/auth/login/', {'email': user.email, 'password': password})
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {response.data["access"]}')
    return client


def ensure_business_settings():
    BusinessSettings.objects.get_or_create(
        pk=1,
        defaults={'store_name': 'Test Store', 'currency': 'USD'},
    )


def create_supplier(**kwargs):
    defaults = {
        'name': 'Test Supplier',
        'promised_lead_time_days': 5,
        'is_active': True,
    }
    defaults.update(kwargs)
    return Supplier.objects.create(**defaults)


def create_category(**kwargs):
    defaults = {'name': 'Test Category', 'is_active': True}
    defaults.update(kwargs)
    return ProductCategory.objects.create(**defaults)


def create_product(stock=10, **kwargs):
    supplier = kwargs.pop('supplier', None) or create_supplier()
    category = kwargs.pop('category', None) or create_category()
    defaults = {
        'sku': kwargs.pop('sku', f'SKU-{Product.objects.count() + 1}'),
        'name': 'Test Product',
        'category': category,
        'supplier': supplier,
        'cost_price': Decimal('5.00'),
        'selling_price': Decimal('10.00'),
        'current_stock': stock,
        'is_active': True,
    }
    defaults.update(kwargs)
    return Product.objects.create(**defaults)
