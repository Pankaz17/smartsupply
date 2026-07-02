import math
from decimal import Decimal

from django.db.models import Case, IntegerField, Value, When

from .models import ReorderRecommendation


def calculate_urgency_score(recommendation):
    """
    Operational urgency from inventory intelligence only.

    Uses stock shortage, ADS (includes seasonal multiplier), lead time, and
    safety stock relative to reorder point. Does not use cost, price, or profit.
    """
    stock = Decimal(recommendation.current_stock)
    reorder_point = recommendation.calculated_reorder_point
    ads = recommendation.average_daily_sales
    lead_time = recommendation.lead_time_days
    safety_stock = recommendation.safety_stock

    rop_safe = max(reorder_point, Decimal('1'))
    shortage = max(Decimal('0'), reorder_point - stock)
    shortage_ratio = float(shortage / rop_safe)

    stock_shortage_weight = shortage_ratio * 40.0
    ads_weight = float(ads) * 8.0
    lead_time_weight = float(lead_time) * 3.0
    safety_weight = float(safety_stock / rop_safe) * 10.0

    return stock_shortage_weight + ads_weight + lead_time_weight + safety_weight


def _assign_levels(scored_items):
    """Assign HIGH / MEDIUM / LOW by percentile rank (top 25% / middle 50% / bottom 25%)."""
    n = len(scored_items)
    if n == 0:
        return

    if n == 1:
        levels = [ReorderRecommendation.PriorityLevel.HIGH]
    elif n == 2:
        levels = [
            ReorderRecommendation.PriorityLevel.HIGH,
            ReorderRecommendation.PriorityLevel.LOW,
        ]
    else:
        high_count = math.ceil(n * 0.25)
        low_count = math.ceil(n * 0.25)
        medium_count = n - high_count - low_count
        levels = (
            [ReorderRecommendation.PriorityLevel.HIGH] * high_count
            + [ReorderRecommendation.PriorityLevel.MEDIUM] * medium_count
            + [ReorderRecommendation.PriorityLevel.LOW] * low_count
        )

    for (recommendation, _), level in zip(scored_items, levels):
        recommendation.priority_level = level


def update_operational_priorities():
    """Recalculate priority_level for all pending recommendations."""
    pending = list(
        ReorderRecommendation.objects.filter(
            status=ReorderRecommendation.Status.PENDING,
        ).select_related('product'),
    )

    scored = [(rec, calculate_urgency_score(rec)) for rec in pending]
    scored.sort(key=lambda item: item[1], reverse=True)

    _assign_levels(scored)

    if pending:
        ReorderRecommendation.objects.bulk_update(pending, ['priority_level'])


def order_by_operational_priority(queryset):
    """Order HIGH → MEDIUM → LOW → newest within each tier."""
    return queryset.annotate(
        _priority_rank=Case(
            When(priority_level=ReorderRecommendation.PriorityLevel.HIGH, then=Value(0)),
            When(priority_level=ReorderRecommendation.PriorityLevel.MEDIUM, then=Value(1)),
            When(priority_level=ReorderRecommendation.PriorityLevel.LOW, then=Value(2)),
            default=Value(3),
            output_field=IntegerField(),
        ),
    ).order_by('_priority_rank', '-generated_at')
