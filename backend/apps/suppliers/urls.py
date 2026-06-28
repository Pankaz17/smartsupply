from django.urls import path

from .views import SupplierDetailView, SupplierListCreateView

urlpatterns = [
    path('suppliers/', SupplierListCreateView.as_view(), name='supplier-list'),
    path('suppliers/<int:pk>/', SupplierDetailView.as_view(), name='supplier-detail'),
]
