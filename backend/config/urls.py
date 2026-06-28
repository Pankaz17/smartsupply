"""
URL configuration for SmartSupply.
"""
from django.contrib import admin
from django.urls import include, path

from .health import HealthCheckView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', HealthCheckView.as_view(), name='health-check'),
    path('api/auth/', include('apps.accounts.urls')),
    path('api/', include('apps.accounts.api_urls')),
    path('api/', include('apps.suppliers.urls')),
    path('api/', include('apps.products.urls')),
    path('api/', include('apps.sales.urls')),
    path('api/', include('apps.inventory.urls')),
    path('api/', include('apps.purchasing.urls')),
    path('api/', include('apps.analytics.urls')),
    path('api/', include('apps.notifications.urls')),
    path('api/', include('apps.reports.urls')),
]
