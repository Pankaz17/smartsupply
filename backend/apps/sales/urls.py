from django.urls import path

from .views import SaleListCreateView

urlpatterns = [
    path('sales/', SaleListCreateView.as_view(), name='sale-list'),
]
