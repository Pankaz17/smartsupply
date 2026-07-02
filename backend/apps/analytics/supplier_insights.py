from decimal import Decimal

from apps.purchasing.models import PurchaseOrder


def _format_days(value):
    numeric = float(value or 0)
    text = f'{numeric:.0f}' if numeric.is_integer() else f'{numeric:.1f}'
    return text


def _reliability_label(on_time_rate):
    rate = float(on_time_rate or 0)
    if rate >= 95:
        return 'Excellent'
    if rate >= 85:
        return 'Good'
    if rate >= 70:
        return 'Fair'
    return 'Needs Attention'


def _recent_received_orders_for_supplier(supplier):
    return list(
        PurchaseOrder.objects.filter(
            supplier=supplier,
            status=PurchaseOrder.Status.RECEIVED,
            expected_delivery_date__isnull=False,
            actual_delivery_date__isnull=False,
        ).order_by('-actual_delivery_date', '-id'),
    )


def build_supplier_insights(snapshot):
    """
    Build human-friendly insights using existing supplier analytics and PO history only.
    """
    supplier = snapshot.supplier
    insights = []

    received_orders = _recent_received_orders_for_supplier(supplier)
    completed_count = len(received_orders)
    if completed_count < 3:
        return ['Not enough purchase history to evaluate this supplier.']

    insights.append(
        f'{supplier.name} usually delivers in {_format_days(snapshot.avg_actual_lead_time)} days.',
    )

    avg_delay = Decimal(snapshot.avg_delay_days or 0)
    if avg_delay > 0:
        days_value = float(avg_delay)
        noun = 'day' if days_value <= 1 else 'days'
        insights.append(f'Average delivery delay is {_format_days(avg_delay)} {noun}.')
    else:
        insights.append('Deliveries usually arrive on or before schedule.')

    insights.append(f'Reliability: {_reliability_label(snapshot.on_time_delivery_rate)}.')

    on_time_streak = 0
    for po in received_orders:
        if po.actual_delivery_date <= po.expected_delivery_date:
            on_time_streak += 1
        else:
            break
    if on_time_streak >= 5:
        insights.append(
            f'{supplier.name} has delivered on time for the last {on_time_streak} purchase orders.',
        )

    recent_window = received_orders[:5]
    recent_delays = sum(
        1 for po in recent_window
        if po.actual_delivery_date and po.expected_delivery_date and po.actual_delivery_date > po.expected_delivery_date
    )
    if recent_delays >= 2:
        insights.append('This supplier has recently delivered later than promised.')

    return insights
