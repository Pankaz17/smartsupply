from django.urls import path

from .views import (
    ApproveRecommendationView,
    DismissRecommendationView,
    GenerateRecommendationsView,
    PurchaseOrderDetailView,
    PurchaseOrderListView,
    PurchaseOrderStatusView,
    ReorderRecommendationListView,
)

urlpatterns = [
    path('recommendations/', ReorderRecommendationListView.as_view(), name='recommendation-list'),
    path(
        'recommendations/generate/',
        GenerateRecommendationsView.as_view(),
        name='recommendation-generate',
    ),
    path(
        'recommendations/<int:pk>/approve/',
        ApproveRecommendationView.as_view(),
        name='recommendation-approve',
    ),
    path(
        'recommendations/<int:pk>/dismiss/',
        DismissRecommendationView.as_view(),
        name='recommendation-dismiss',
    ),
    path('purchase-orders/', PurchaseOrderListView.as_view(), name='purchase-order-list'),
    path(
        'purchase-orders/<int:pk>/',
        PurchaseOrderDetailView.as_view(),
        name='purchase-order-detail',
    ),
    path(
        'purchase-orders/<int:pk>/status/',
        PurchaseOrderStatusView.as_view(),
        name='purchase-order-status',
    ),
]
