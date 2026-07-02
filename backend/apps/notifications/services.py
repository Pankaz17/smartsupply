from django.utils import timezone

from .models import Notification


def create_notification(notification_type, title, message, product=None, supplier=None, purchase_order=None):
    """Create a notification unless an identical unread one already exists."""
    dedup = {
        'notification_type': notification_type,
        'is_read': False,
    }
    if product is not None:
        dedup['related_product'] = product
    if supplier is not None:
        dedup['related_supplier'] = supplier
    if purchase_order is not None:
        dedup['related_purchase_order'] = purchase_order

    if Notification.objects.filter(**dedup).exists():
        return None

    return Notification.objects.create(
        notification_type=notification_type,
        title=title,
        message=message,
        related_product=product,
        related_supplier=supplier,
        related_purchase_order=purchase_order,
    )


def notify_out_of_stock(product):
    return create_notification(
        Notification.Type.OUT_OF_STOCK,
        title=f'Out of stock: {product.name}',
        message=(
            f'{product.name} ({product.sku}) has reached zero stock. '
            f'Restocking may be required.'
        ),
        product=product,
    )


def notify_low_stock(product, reorder_point):
    return create_notification(
        Notification.Type.LOW_STOCK,
        title=f'Low stock: {product.name}',
        message=(
            f'{product.name} ({product.sku}) has {product.current_stock} units remaining, '
            f'below the reorder point of {reorder_point:.1f}.'
        ),
        product=product,
    )


def notify_dead_stock(snapshot):
    product = snapshot.product
    return create_notification(
        Notification.Type.DEAD_STOCK,
        title=f'Dead stock: {product.name}',
        message=(
            f'{product.name} ({product.sku}) has had no sales for '
            f'{snapshot.days_without_sale} days with {snapshot.current_stock} units on hand.'
        ),
        product=product,
    )


def notify_supplier_delay(purchase_order):
    delay_days = (
        purchase_order.actual_delivery_date - purchase_order.expected_delivery_date
    ).days
    return create_notification(
        Notification.Type.SUPPLIER_DELAY,
        title=f'Delayed delivery: {purchase_order.po_number}',
        message=(
            f'Purchase order {purchase_order.po_number} from '
            f'{purchase_order.supplier.name} was received {delay_days} day(s) '
            f'after the expected delivery date.'
        ),
        supplier=purchase_order.supplier,
        purchase_order=purchase_order,
    )


def notify_reorder_recommendation(recommendation):
    product = recommendation.product
    return create_notification(
        Notification.Type.REORDER_RECOMMENDATION,
        title=f'Reorder recommended: {product.name}',
        message=(
            f'A reorder recommendation is available for {product.name} ({product.sku}). '
            f'Suggested quantity: {recommendation.recommended_quantity}.'
        ),
        product=product,
    )


def check_stock_notifications(product):
    """Evaluate low-stock and out-of-stock alerts after a stock change."""
    from apps.purchasing.services import calculate_reorder_metrics

    if not product.is_active:
        return

    product.refresh_from_db()

    if product.current_stock == 0:
        notify_out_of_stock(product)
        return

    _, _, _, reorder_point, _ = calculate_reorder_metrics(product)
    if product.current_stock <= reorder_point:
        notify_low_stock(product, reorder_point)


def mark_all_read():
    now = timezone.now()
    return Notification.objects.filter(is_read=False).update(is_read=True, read_at=now)


def get_unread_count():
    return Notification.objects.filter(is_read=False).count()


def get_dashboard_alerts():
    """Build summary alert messages for the dashboard warning section."""
    from apps.analytics.models import DeadStockSnapshot
    from apps.products.models import Product

    alerts = []

    out_of_stock = Product.objects.filter(is_active=True, current_stock=0).count()
    if out_of_stock:
        noun = 'product is' if out_of_stock == 1 else 'products are'
        alerts.append(f'{out_of_stock} {noun} out of stock')

    delayed = Notification.objects.filter(
        notification_type=Notification.Type.SUPPLIER_DELAY,
        is_read=False,
    ).count()
    if delayed:
        alerts.append(f'{delayed} supplier deliver{"y was" if delayed == 1 else "ies were"} delayed')

    dead_stock = DeadStockSnapshot.objects.count()
    if dead_stock:
        alerts.append(f'{dead_stock} dead stock item{"s require" if dead_stock != 1 else " requires"} attention')

    long_unsold = DeadStockSnapshot.objects.filter(days_without_sale__gte=120).count()
    if long_unsold:
        alerts.append(
            f'{long_unsold} product{"s have" if long_unsold != 1 else " has"} been unsold '
            'for over 120 days. Consider stopping future reorders.'
        )

    pending_recs = Notification.objects.filter(
        notification_type=Notification.Type.REORDER_RECOMMENDATION,
        is_read=False,
    ).count()
    if pending_recs:
        alerts.append(f'{pending_recs} reorder recommendation{"s are" if pending_recs != 1 else " is"} pending review')

    low_stock = Notification.objects.filter(
        notification_type=Notification.Type.LOW_STOCK,
        is_read=False,
    ).count()
    if low_stock and not out_of_stock:
        alerts.append(f'{low_stock} product{"s are" if low_stock != 1 else " is"} below reorder point')

    return alerts
