from django.db.models import OuterRef, Subquery
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsOwner, IsOwnerOrReadOnly

from .models import DeadStockSnapshot, SeasonalEvent, SupplierPerformanceSnapshot
from .serializers import (
    DeadStockSnapshotSerializer,
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
                f'{summary["supplier_snapshots_updated"]} Supplier Snapshots Updated.'
            ),
        })
