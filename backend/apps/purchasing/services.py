import math
from datetime import timedelta
from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone

from apps.analytics.services import get_seasonal_multiplier
from apps.products.models import Product
from apps.sales.models import Sale

from .models import PurchaseOrder, PurchaseOrderItem, ReorderRecommendation

SALES_LOOKBACK_DAYS = 30
SAFETY_STOCK_MULTIPLIER = 3
DEFAULT_REASON = 'Current stock is below calculated reorder point.'


def calculate_average_daily_sales(product, days=SALES_LOOKBACK_DAYS):
    since = timezone.now() - timedelta(days=days)
    total_sold = (
        Sale.objects.filter(product=product, created_at__gte=since)
        .aggregate(total=Sum('quantity'))['total']
        or 0
    )
    return Decimal(total_sold) / Decimal(days)


def calculate_reorder_metrics(product):
    base_ads = calculate_average_daily_sales(product)
    multiplier, event_names = get_seasonal_multiplier(product)
    ads = base_ads * multiplier
    lead_time = product.supplier.promised_lead_time_days
    safety_stock = ads * SAFETY_STOCK_MULTIPLIER
    reorder_point = (ads * lead_time) + safety_stock
    return ads, lead_time, safety_stock, reorder_point, event_names


def build_recommendation_reason(event_names):
    if event_names:
        names = ', '.join(event_names)
        return (
            f'Current stock below reorder point. '
            f'{names} seasonal multiplier applied.'
        )
    return DEFAULT_REASON


def calculate_recommended_quantity(current_stock, reorder_point):
    gap = reorder_point - Decimal(current_stock)
    if gap <= 0:
        return 0
    return max(1, math.ceil(float(gap)))


def generate_recommendations():
    results = {'created': 0, 'updated': 0, 'skipped': 0}

    products = Product.objects.filter(is_active=True).select_related(
        'supplier', 'category',
    )
    for product in products:
        ads, lead_time, safety_stock, reorder_point, event_names = (
            calculate_reorder_metrics(product)
        )

        if product.current_stock > reorder_point:
            results['skipped'] += 1
            continue

        recommended_qty = calculate_recommended_quantity(
            product.current_stock,
            reorder_point,
        )
        if recommended_qty <= 0:
            results['skipped'] += 1
            continue

        pending = ReorderRecommendation.objects.filter(
            product=product,
            status=ReorderRecommendation.Status.PENDING,
        ).first()

        values = {
            'supplier': product.supplier,
            'current_stock': product.current_stock,
            'recommended_quantity': recommended_qty,
            'average_daily_sales': ads,
            'lead_time_days': lead_time,
            'safety_stock': safety_stock,
            'calculated_reorder_point': reorder_point,
            'reason': build_recommendation_reason(event_names),
            'generated_at': timezone.now(),
        }

        if pending:
            for key, val in values.items():
                setattr(pending, key, val)
            pending.save()
            results['updated'] += 1
        else:
            recommendation = ReorderRecommendation.objects.create(
                product=product,
                status=ReorderRecommendation.Status.PENDING,
                **values,
            )
            from apps.notifications.services import notify_reorder_recommendation
            notify_reorder_recommendation(recommendation)
            results['created'] += 1

    from .operational_priority import update_operational_priorities
    update_operational_priorities()

    return results


def approve_recommendation(recommendation, user):
    if recommendation.status != ReorderRecommendation.Status.PENDING:
        raise ValueError('Only pending recommendations can be approved.')

    product = recommendation.product
    po = PurchaseOrder.objects.create(
        po_number=PurchaseOrder.generate_po_number(),
        supplier=recommendation.supplier,
        status=PurchaseOrder.Status.DRAFT,
        created_from=PurchaseOrder.Source.RECOMMENDATION,
        notes=f'Created from reorder recommendation #{recommendation.pk}.',
        created_by=user,
    )

    PurchaseOrderItem.objects.create(
        purchase_order=po,
        product=product,
        quantity=recommendation.recommended_quantity,
        unit_cost=product.cost_price,
    )

    recommendation.status = ReorderRecommendation.Status.APPROVED
    recommendation.reviewed_at = timezone.now()
    recommendation.purchase_order = po
    recommendation.save()

    return po


def dismiss_recommendation(recommendation):
    if recommendation.status != ReorderRecommendation.Status.PENDING:
        raise ValueError('Only pending recommendations can be dismissed.')

    recommendation.status = ReorderRecommendation.Status.DISMISSED
    recommendation.reviewed_at = timezone.now()
    recommendation.save()
    return recommendation
