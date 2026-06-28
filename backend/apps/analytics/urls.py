from django.urls import path

from .views import (
    DeadStockListView,
    RunAnalyticsView,
    SeasonalEventDetailView,
    SeasonalEventListCreateView,
    SupplierAnalyticsListView,
)

urlpatterns = [
    path('seasonal-events/', SeasonalEventListCreateView.as_view(), name='seasonal-event-list'),
    path(
        'seasonal-events/<int:pk>/',
        SeasonalEventDetailView.as_view(),
        name='seasonal-event-detail',
    ),
    path('dead-stock/', DeadStockListView.as_view(), name='dead-stock-list'),
    path(
        'supplier-analytics/',
        SupplierAnalyticsListView.as_view(),
        name='supplier-analytics-list',
    ),
    path('analytics/run/', RunAnalyticsView.as_view(), name='analytics-run'),
]
