from django.urls import path

from .views import (
    DeadStockReportExportView,
    DeadStockReportView,
    InventoryReportExportView,
    InventoryReportView,
    RecommendationsReportExportView,
    RecommendationsReportView,
    ReportsOverviewView,
    SalesReportExportView,
    SalesReportView,
    SupplierReportExportView,
    SupplierReportView,
)

urlpatterns = [
    path('reports/', ReportsOverviewView.as_view(), name='reports-overview'),
    path(
        'reports/inventory/export/',
        InventoryReportExportView.as_view(),
        name='report-inventory-export',
    ),
    path('reports/inventory/', InventoryReportView.as_view(), name='report-inventory'),
    path(
        'reports/sales/export/',
        SalesReportExportView.as_view(),
        name='report-sales-export',
    ),
    path('reports/sales/', SalesReportView.as_view(), name='report-sales'),
    path(
        'reports/dead-stock/export/',
        DeadStockReportExportView.as_view(),
        name='report-dead-stock-export',
    ),
    path('reports/dead-stock/', DeadStockReportView.as_view(), name='report-dead-stock'),
    path(
        'reports/suppliers/export/',
        SupplierReportExportView.as_view(),
        name='report-suppliers-export',
    ),
    path('reports/suppliers/', SupplierReportView.as_view(), name='report-suppliers'),
    path(
        'reports/recommendations/export/',
        RecommendationsReportExportView.as_view(),
        name='report-recommendations-export',
    ),
    path(
        'reports/recommendations/',
        RecommendationsReportView.as_view(),
        name='report-recommendations',
    ),
]
