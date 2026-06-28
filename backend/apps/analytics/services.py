from datetime import timedelta
from decimal import Decimal

from django.db.models import Max
from django.utils import timezone

from apps.accounts.models import BusinessSettings
from apps.products.models import Product
from apps.purchasing.models import PurchaseOrder
from apps.sales.models import Sale

from .models import DeadStockSnapshot, SeasonalEvent, SupplierPerformanceSnapshot


def get_active_seasonal_events_for_category(category, on_date=None):
    on_date = on_date or timezone.now().date()
    return SeasonalEvent.objects.filter(
        is_active=True,
        category=category,
        start_date__lte=on_date,
        end_date__gte=on_date,
    )


def get_seasonal_multiplier(product, on_date=None):
    events = get_active_seasonal_events_for_category(product.category, on_date)
    multiplier = Decimal('1')
    event_names = []
    for event in events:
        multiplier *= event.multiplier
        event_names.append(event.name)
    return multiplier, event_names


def count_active_seasonal_events(on_date=None):
    on_date = on_date or timezone.now().date()
    return SeasonalEvent.objects.filter(
        is_active=True,
        start_date__lte=on_date,
        end_date__gte=on_date,
    ).count()


def days_without_sale(product, today=None):
    today = today or timezone.now().date()
    latest_sale = (
        Sale.objects.filter(product=product)
        .aggregate(latest=Max('created_at'))['latest']
    )
    if latest_sale:
        return (today - latest_sale.date()).days
    created = product.created_at.date() if product.created_at else today
    return (today - created).days


def severity_for_days(days, threshold):
    if days >= threshold + 30:
        return DeadStockSnapshot.Severity.CRITICAL
    return DeadStockSnapshot.Severity.WARNING


def update_dead_stock_snapshots():
    settings = BusinessSettings.get_solo()
    threshold = settings.dead_stock_threshold_days
    today = timezone.now()
    created = 0
    removed = 0

    active_product_ids = set()
    products = Product.objects.filter(is_active=True, current_stock__gt=0).select_related(
        'category',
    )

    for product in products:
        days = days_without_sale(product, today.date())
        if days < threshold:
            continue

        inventory_value = Decimal(product.current_stock) * product.cost_price
        severity = severity_for_days(days, threshold)

        snapshot, _created = DeadStockSnapshot.objects.update_or_create(
            product=product,
            defaults={
                'days_without_sale': days,
                'current_stock': product.current_stock,
                'inventory_value': inventory_value,
                'severity': severity,
                'detected_at': today,
            },
        )
        from apps.notifications.services import notify_dead_stock
        notify_dead_stock(snapshot)
        active_product_ids.add(product.id)
        created += 1

    stale = DeadStockSnapshot.objects.exclude(product_id__in=active_product_ids)
    removed = stale.count()
    stale.delete()

    return {'flagged': created, 'cleared': removed}


def _resolve_order_date(po, promised_lead_time_days):
    """Return the order anchor date, with legacy fallback for pre-4.1 POs."""
    if po.ordered_at:
        return po.ordered_at
    if po.expected_delivery_date:
        return po.expected_delivery_date - timedelta(days=promised_lead_time_days)
    return None


def update_supplier_performance_snapshots():
    today = timezone.now().date()
    updated = 0

    from apps.suppliers.models import Supplier

    for supplier in Supplier.objects.filter(is_active=True):
        received_orders = PurchaseOrder.objects.filter(
            supplier=supplier,
            status=PurchaseOrder.Status.RECEIVED,
            actual_delivery_date__isnull=False,
            expected_delivery_date__isnull=False,
        )

        total_orders = received_orders.count()
        if total_orders == 0:
            SupplierPerformanceSnapshot.objects.update_or_create(
                supplier=supplier,
                snapshot_date=today,
                defaults={
                    'avg_promised_lead_time': Decimal(supplier.promised_lead_time_days),
                    'avg_actual_lead_time': Decimal('0'),
                    'avg_delay_days': Decimal('0'),
                    'on_time_delivery_rate': Decimal('0'),
                    'total_orders': 0,
                },
            )
            updated += 1
            continue

        promised_days_list = []
        actual_days_list = []
        delay_days_list = []
        on_time_count = 0

        for po in received_orders:
            promised = po.supplier.promised_lead_time_days
            order_date = _resolve_order_date(po, promised)
            if order_date is None or po.actual_delivery_date is None:
                continue

            actual_days = (po.actual_delivery_date - order_date).days
            delay = actual_days - promised

            promised_days_list.append(Decimal(promised))
            actual_days_list.append(Decimal(actual_days))
            delay_days_list.append(Decimal(delay))
            if po.expected_delivery_date and po.actual_delivery_date <= po.expected_delivery_date:
                on_time_count += 1

        measured_orders = len(actual_days_list)
        if measured_orders == 0:
            SupplierPerformanceSnapshot.objects.update_or_create(
                supplier=supplier,
                snapshot_date=today,
                defaults={
                    'avg_promised_lead_time': Decimal(supplier.promised_lead_time_days),
                    'avg_actual_lead_time': Decimal('0'),
                    'avg_delay_days': Decimal('0'),
                    'on_time_delivery_rate': Decimal('0'),
                    'total_orders': total_orders,
                },
            )
            updated += 1
            continue

        avg_promised = sum(promised_days_list) / measured_orders
        avg_actual = sum(actual_days_list) / measured_orders
        avg_delay = sum(delay_days_list) / measured_orders
        on_time_rate = (Decimal(on_time_count) / Decimal(measured_orders)) * 100

        SupplierPerformanceSnapshot.objects.update_or_create(
            supplier=supplier,
            snapshot_date=today,
            defaults={
                'avg_promised_lead_time': avg_promised,
                'avg_actual_lead_time': avg_actual,
                'avg_delay_days': avg_delay,
                'on_time_delivery_rate': on_time_rate,
                'total_orders': measured_orders,
            },
        )
        updated += 1

    return {'updated': updated}


def run_nightly_analytics():
    from apps.products.models import Product
    from apps.purchasing.services import generate_recommendations
    from apps.suppliers.models import Supplier

    product_count = Product.objects.filter(is_active=True).count()
    supplier_count = Supplier.objects.filter(is_active=True).count()

    supplier_results = update_supplier_performance_snapshots()
    dead_stock_results = update_dead_stock_snapshots()
    recommendation_results = generate_recommendations()

    return {
        'products_processed': product_count,
        'suppliers_processed': supplier_count,
        'recommendations_created': recommendation_results['created'],
        'recommendations_updated': recommendation_results['updated'],
        'recommendations_skipped': recommendation_results['skipped'],
        'dead_stock_flagged': dead_stock_results['flagged'],
        'dead_stock_cleared': dead_stock_results['cleared'],
        'supplier_snapshots_updated': supplier_results['updated'],
        'active_seasonal_events': count_active_seasonal_events(),
    }
