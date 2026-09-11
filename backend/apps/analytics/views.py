from django.db.models import OuterRef, Subquery
from django.utils import timezone
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsOwner, IsOwnerOrReadOnly, IsOwnerOrStaff

from apps.analytics.forecasting import get_or_compute_forecast, update_demand_forecasts
from apps.products.models import Product

from .models import DeadStockSnapshot, DemandForecast, SeasonalEvent, SupplierPerformanceSnapshot
from .serializers import (
    DeadStockSnapshotSerializer,
    DemandForecastSerializer,
    SeasonalEventSerializer,
    SupplierPerformanceSnapshotSerializer,
)
from .services import run_nightly_analytics


class SeasonalEventListCreateView(generics.ListCreateAPIView):
    permission_classes = (IsOwnerOrReadOnly,)
    serializer_class = SeasonalEventSerializer
    queryset = SeasonalEvent.objects.select_related('category').all()


class SeasonalEventDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsOwnerOrReadOnly,)
    serializer_class = SeasonalEventSerializer
    queryset = SeasonalEvent.objects.select_related('category').all()


class DeadStockListView(generics.ListAPIView):
    permission_classes = (IsOwnerOrReadOnly,)
    serializer_class = DeadStockSnapshotSerializer

    def get_queryset(self):
        qs = DeadStockSnapshot.objects.select_related(
            'product', 'product__category',
        ).all()
        severity = self.request.query_params.get('severity')
        if severity:
            qs = qs.filter(severity=severity)
        return qs


class SupplierAnalyticsListView(generics.ListAPIView):
    permission_classes = (IsOwnerOrReadOnly,)
    serializer_class = SupplierPerformanceSnapshotSerializer

    def get_queryset(self):
        latest_dates = (
            SupplierPerformanceSnapshot.objects
            .filter(supplier=OuterRef('supplier'))
            .order_by('-snapshot_date')
            .values('snapshot_date')[:1]
        )
        return SupplierPerformanceSnapshot.objects.filter(
            snapshot_date=Subquery(latest_dates),
        ).select_related('supplier').order_by('supplier__name')


class RunAnalyticsView(APIView):
    permission_classes = (IsOwner,)

    def post(self, request):
        summary = run_nightly_analytics()
        rec_total = (
            summary['recommendations_created'] + summary['recommendations_updated']
        )
        return Response({
            'detail': 'Analytics run completed.',
            'summary': summary,
            'message': (
                f'Processed: {summary["products_processed"]} Products, '
                f'{summary["suppliers_processed"]} Suppliers, '
                f'{rec_total} Recommendations Generated, '
                f'{summary["dead_stock_flagged"]} Dead Stock Items, '
                f'{summary["supplier_snapshots_updated"]} Supplier Snapshots Updated, '
                f'{summary.get("forecasts_available", 0)} Forecasts Available.'
            ),
        })


class DemandForecastListView(APIView):
    """Read-only demand forecasts. Does not modify inventory or recommendations."""

    permission_classes = (IsOwnerOrStaff,)

    def get(self, request):
        product_id = request.query_params.get('product')
        refresh = request.query_params.get('refresh', '').lower() in ('1', 'true', 'yes')

        products = Product.objects.filter(is_active=True).select_related(
            'category', 'supplier',
        )
        if product_id:
            products = products.filter(pk=product_id)

        today = timezone.localdate()
        results = []
        for product in products.order_by('name'):
            if refresh:
                result = get_or_compute_forecast(product, persist=True)
                results.append({
                    'product_id': result.product_id,
                    'product': result.product_name,
                    'product_sku': product.sku,
                    'forecast_date': str(today),
                    'forecast_horizon': result.forecast_horizon,
                    'predicted_daily_demand': (
                        str(result.predicted_daily_demand)
                        if result.predicted_daily_demand is not None
                        else None
                    ),
                    'predicted_horizon_total': (
                        str(result.predicted_horizon_total)
                        if result.predicted_horizon_total is not None
                        else None
                    ),
                    'model': result.model_name,
                    'historical_observations': result.historical_observations,
                    'historical_ads': str(result.historical_ads),
                    'status': result.status,
                    'mae': str(result.mae) if result.mae is not None else None,
                    'trend': result.trend,
                    'fallback': result.fallback,
                })
            else:
                existing = DemandForecast.objects.filter(
                    product=product, forecast_date=today,
                ).first()
                if existing:
                    results.append(DemandForecastSerializer(existing).data)
                else:
                    result = get_or_compute_forecast(product, persist=True)
                    existing = DemandForecast.objects.get(
                        product=product, forecast_date=today,
                    )
                    results.append(DemandForecastSerializer(existing).data)

        return Response(results)


class DemandForecastRefreshView(APIView):
    permission_classes = (IsOwner,)

    def post(self, request):
        summary = update_demand_forecasts()
        return Response({
            'detail': 'Demand forecasts refreshed.',
            'summary': summary,
        })
