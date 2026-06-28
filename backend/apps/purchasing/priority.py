import math
from decimal import Decimal


def calculate_unit_profit(selling_price, cost_price):
    return selling_price - cost_price


def calculate_priority_score(unit_profit, average_daily_sales):
    return unit_profit * average_daily_sales


def calculate_expected_restock_profit(unit_profit, recommended_quantity):
    return unit_profit * Decimal(recommended_quantity)


def calculate_profit_metrics(product, average_daily_sales, recommended_quantity):
    """Return unit_profit, priority_score, expected_restock_profit for a product."""
    unit_profit = calculate_unit_profit(product.selling_price, product.cost_price)
    priority_score = calculate_priority_score(unit_profit, average_daily_sales)
    expected_restock_profit = calculate_expected_restock_profit(
        unit_profit, recommended_quantity,
    )
    return unit_profit, priority_score, expected_restock_profit


def assign_priority_levels(recommendations):
    """
    Assign HIGH / MEDIUM / LOW based on priority_score distribution among
    the provided recommendations (sorted highest score first).

    Top 25% = HIGH, middle 50% = MEDIUM, bottom 25% = LOW.
    """
    from .models import ReorderRecommendation

    if not recommendations:
        return

    sorted_recs = sorted(recommendations, key=lambda r: r.priority_score, reverse=True)
    n = len(sorted_recs)

    if n == 1:
        sorted_recs[0].priority_level = ReorderRecommendation.PriorityLevel.HIGH
        return

    high_cutoff = math.ceil(n * 0.25)
    low_cutoff = math.floor(n * 0.75)

    for index, rec in enumerate(sorted_recs):
        if index < high_cutoff:
            rec.priority_level = ReorderRecommendation.PriorityLevel.HIGH
        elif index >= low_cutoff:
            rec.priority_level = ReorderRecommendation.PriorityLevel.LOW
        else:
            rec.priority_level = ReorderRecommendation.PriorityLevel.MEDIUM
