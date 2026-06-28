from datetime import timedelta

from django.db.models import DecimalField, F, OuterRef, Subquery, Sum
from django.db.models.expressions import ExpressionWrapper
from django.db.models.functions import Coalesce
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.analytics.models import DeadStockSnapshot, SeasonalEvent, SupplierPerformanceSnapshot
from apps.analytics.services import count_active_seasonal_events
from apps.notifications.models import Notification
from apps.notifications.serializers import NotificationSerializer
from apps.notifications.services import get_dashboard_alerts, get_unread_count
from apps.products.models import Product
from apps.purchasing.models import PurchaseOrder, ReorderRecommendation
from apps.purchasing.serializers import (
    PurchaseOrderListSerializer,
    ReorderRecommendationSerializer,
)
from apps.sales.models import Sale
from apps.sales.serializers import SaleSerializer
from apps.suppliers.models import Supplier


class DashboardView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        products = Product.objects.all()
        total_products = products.count()
        active_products = products.filter(is_active=True).count()
        total_suppliers = Supplier.objects.filter(is_active=True).count()
        out_of_stock = products.filter(current_stock=0, is_active=True).count()

        inventory_value = products.aggregate(
            total=Coalesce(
                Sum(
                    ExpressionWrapper(
                        F('current_stock') * F('cost_price'),
                        output_field=DecimalField(max_digits=14, decimal_places=2),
                    ),
                ),
                0,
                output_field=DecimalField(max_digits=14, decimal_places=2),
            ),
        )['total']

        seven_days_ago = timezone.now() - timedelta(days=7)
        recent_sales_count = Sale.objects.filter(created_at__gte=seven_days_ago).count()
        recent_sales = Sale.objects.select_related('product', 'recorded_by').order_by(
            '-created_at',
        )[:10]

        pending_recommendations = ReorderRecommendation.objects.filter(
            status=ReorderRecommendation.Status.PENDING,
        ).count()
        draft_purchase_orders = PurchaseOrder.objects.filter(
            status=PurchaseOrder.Status.DRAFT,
        ).count()
        ordered_purchase_orders = PurchaseOrder.objects.filter(
            status=PurchaseOrder.Status.ORDERED,
        ).count()

        recent_recommendations = ReorderRecommendation.objects.select_related(
            'product', 'supplier',
        ).order_by('-priority_score', '-generated_at')[:5]

        top_restock_priorities = ReorderRecommendation.objects.filter(
            status=ReorderRecommendation.Status.PENDING,
        ).select_related('product').order_by('-priority_score', '-generated_at')[:5]
        recent_purchase_orders = PurchaseOrder.objects.select_related(
            'supplier',
        ).order_by('-created_at')[:5]

        dead_stock_items = DeadStockSnapshot.objects.count()
        critical_dead_stock = DeadStockSnapshot.objects.filter(
            severity=DeadStockSnapshot.Severity.CRITICAL,
        ).count()

        latest_dates = (
            SupplierPerformanceSnapshot.objects
            .filter(supplier=OuterRef('supplier'))
            .order_by('-snapshot_date')
            .values('snapshot_date')[:1]
        )
        latest_snapshots = SupplierPerformanceSnapshot.objects.filter(
            snapshot_date=Subquery(latest_dates),
        )
        suppliers_with_delays = latest_snapshots.filter(
            avg_delay_days__gt=0,
            total_orders__gt=0,
        ).count()
        active_seasonal_events = count_active_seasonal_events()

        unread_notifications = get_unread_count()
        recent_notifications = Notification.objects.select_related(
            'related_product', 'related_supplier', 'related_purchase_order',
        ).order_by('-created_at')[:5]
        dashboard_alerts = get_dashboard_alerts()

        return Response({
            'total_products': total_products,
            'active_products': active_products,
            'total_suppliers': total_suppliers,
            'inventory_value': str(inventory_value),
            'out_of_stock_products': out_of_stock,
            'recent_sales_count': recent_sales_count,
            'recent_sales': SaleSerializer(recent_sales, many=True).data,
            'pending_recommendations': pending_recommendations,
            'draft_purchase_orders': draft_purchase_orders,
            'ordered_purchase_orders': ordered_purchase_orders,
            'recent_recommendations': ReorderRecommendationSerializer(
                recent_recommendations, many=True,
            ).data,
            'top_restock_priorities': [
                {
                    'product_name': r.product.name,
                    'priority_level': r.priority_level,
                    'priority_score': str(r.priority_score),
                }
                for r in top_restock_priorities
            ],
            'recent_purchase_orders': PurchaseOrderListSerializer(
                recent_purchase_orders, many=True,
            ).data,
            'dead_stock_items': dead_stock_items,
            'critical_dead_stock': critical_dead_stock,
            'suppliers_with_delays': suppliers_with_delays,
            'active_seasonal_events': active_seasonal_events,
            'unread_notifications': unread_notifications,
            'recent_notifications': NotificationSerializer(
                recent_notifications, many=True,
            ).data,
            'dashboard_alerts': dashboard_alerts,
        })
