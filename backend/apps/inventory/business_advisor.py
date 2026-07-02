from django.db.models import F
from django.utils import timezone

from apps.analytics.models import DeadStockSnapshot, SupplierPerformanceSnapshot
from apps.products.models import Product
from apps.purchasing.profit_advisor import get_latest_profit_advisor_analysis
from apps.purchasing.models import PurchaseOrder, ReorderRecommendation
from apps.purchasing.services import calculate_reorder_metrics


def get_dashboard_greeting(now=None):
    now = now or timezone.localtime()
    hour = now.hour
    if 6 <= hour <= 11:
        return 'Good Morning'
    if 12 <= hour <= 16:
        return 'Good Afternoon'
    if 17 <= hour <= 22:
        return 'Good Evening'
    return 'Working Late?'


def _get_low_stock_count():
    count = 0
    products = Product.objects.filter(is_active=True, current_stock__gt=0).select_related(
        'supplier', 'category',
    )
    for product in products:
        _, _, _, reorder_point, _ = calculate_reorder_metrics(product)
        if product.current_stock <= reorder_point:
            count += 1
    return count


def build_business_advisor_messages():
    messages = []

    low_stock_count = _get_low_stock_count()
    if low_stock_count:
        noun = 'product is' if low_stock_count == 1 else 'products are'
        messages.append(
            f'{low_stock_count} {noun} running low. Consider reviewing today\'s recommendations.',
        )

    out_of_stock = Product.objects.filter(is_active=True, current_stock=0).count()
    if out_of_stock:
        noun = 'product is' if out_of_stock == 1 else 'products are'
        messages.append(f'{out_of_stock} {noun} currently out of stock.')

    latest_supplier_snapshot = (
        SupplierPerformanceSnapshot.objects.filter(total_orders__gt=0)
        .select_related('supplier')
        .order_by('-snapshot_date', 'supplier__name')
        .first()
    )
    if latest_supplier_snapshot:
        avg_days = float(latest_supplier_snapshot.avg_actual_lead_time)
        avg_text = f'{avg_days:.0f}' if avg_days.is_integer() else f'{avg_days:.1f}'
        messages.append(
            f'{latest_supplier_snapshot.supplier.name} usually delivers in {avg_text} days on average.',
        )

    delayed_deliveries = PurchaseOrder.objects.filter(
        status=PurchaseOrder.Status.RECEIVED,
        expected_delivery_date__isnull=False,
        actual_delivery_date__isnull=False,
        actual_delivery_date__gt=F('expected_delivery_date'),
    ).count()
    if delayed_deliveries:
        noun = 'delivery arrived' if delayed_deliveries == 1 else 'deliveries arrived'
        messages.append(f'{delayed_deliveries} recent {noun} later than promised.')

    awaiting_delivery = PurchaseOrder.objects.filter(
        status=PurchaseOrder.Status.ORDERED,
    ).count()
    if awaiting_delivery:
        noun = 'purchase order is' if awaiting_delivery == 1 else 'purchase orders are'
        messages.append(f'{awaiting_delivery} {noun} currently awaiting delivery.')

    long_unsold = DeadStockSnapshot.objects.filter(days_without_sale__gte=120).count()
    if long_unsold:
        noun = 'product has' if long_unsold == 1 else 'products have'
        messages.append(
            f'{long_unsold} {noun} not sold for over 120 days. Consider discounting or bundling them.',
        )

    profit_advisor = get_latest_profit_advisor_analysis()
    if profit_advisor:
        count = profit_advisor.get('recommended_count', 0)
        noun = 'product' if count == 1 else 'products'
        messages.append(
            f'Your last Profit Advisor analysis recommends purchasing {count} {noun} within your budget.',
        )

    pending_recommendations = ReorderRecommendation.objects.filter(
        status=ReorderRecommendation.Status.PENDING,
    ).count()
    if pending_recommendations:
        noun = 'product currently requires' if pending_recommendations == 1 else 'products currently require'
        messages.append(f'{pending_recommendations} {noun} restocking.')

    if not messages:
        return ['Everything looks healthy today.']
    return messages
