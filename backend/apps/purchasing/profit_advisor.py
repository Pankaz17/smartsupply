from decimal import Decimal

from apps.accounts.models import BusinessSettings

from .models import ReorderRecommendation


def _decimal_str(value):
    return str(value) if value is not None else '0'


def _analyze_item(recommendation):
    product = recommendation.product
    unit_profit = product.selling_price - product.cost_price
    purchase_cost = Decimal(recommendation.recommended_quantity) * product.cost_price
    expected_restock_profit = Decimal(recommendation.recommended_quantity) * unit_profit
    priority_score = unit_profit * recommendation.average_daily_sales

    return {
        'recommendation_id': recommendation.id,
        'product': product.name,
        'product_sku': product.sku,
        'unit_profit': _decimal_str(unit_profit),
        'purchase_cost': _decimal_str(purchase_cost),
        'expected_profit': _decimal_str(expected_restock_profit),
        'priority_score': _decimal_str(priority_score),
        '_purchase_cost': purchase_cost,
        '_expected_profit': expected_restock_profit,
        '_priority_score': priority_score,
    }


def _build_explanation(currency, budget, recommended_names):
    budget_str = f'{currency} {budget:,.2f}'
    if not recommended_names:
        return (
            f'Based on your purchasing budget of {budget_str}, SmartSupply could not '
            f'recommend any pending restocks within your available budget.'
        )
    if len(recommended_names) == 1:
        products_text = recommended_names[0]
    elif len(recommended_names) == 2:
        products_text = f'{recommended_names[0]} and {recommended_names[1]}'
    else:
        products_text = ', '.join(recommended_names[:-1]) + f', and {recommended_names[-1]}'

    return (
        f'Based on your purchasing budget of {budget_str}, SmartSupply recommends '
        f'purchasing {products_text} first because they provide the highest expected '
        f'return while remaining within your available budget.'
    )


def run_profit_advisor_analysis(budget):
    """
    Analyze pending recommendations against a purchasing budget.

    Returns analysis dict without persisting. Use save_profit_advisor_analysis to store.
    """
    pending = ReorderRecommendation.objects.filter(
        status=ReorderRecommendation.Status.PENDING,
    ).select_related('product').order_by('-generated_at')

    items = [_analyze_item(rec) for rec in pending]
    items.sort(key=lambda x: x['_priority_score'], reverse=True)

    remaining = Decimal(budget)
    recommended_products = []
    deferred_products = []

    for item in items:
        public_item = {k: v for k, v in item.items() if not k.startswith('_')}
        if item['_purchase_cost'] <= remaining:
            public_item['decision'] = 'recommended'
            recommended_products.append(public_item)
            remaining -= item['_purchase_cost']
        else:
            public_item['decision'] = 'deferred'
            deferred_products.append(public_item)

    recommended_spending = Decimal(budget) - remaining
    expected_profit = sum(
        (Decimal(p['expected_profit']) for p in recommended_products),
        Decimal('0'),
    )
    deferred_spending = sum(
        (Decimal(p['purchase_cost']) for p in deferred_products),
        Decimal('0'),
    )

    settings = BusinessSettings.get_solo()
    recommended_names = [p['product'] for p in recommended_products]
    explanation = _build_explanation(settings.currency, Decimal(budget), recommended_names)

    return {
        'budget': _decimal_str(budget),
        'recommended_spending': _decimal_str(recommended_spending),
        'remaining_budget': _decimal_str(remaining),
        'deferred_spending': _decimal_str(deferred_spending),
        'expected_profit': _decimal_str(expected_profit),
        'recommended_count': len(recommended_products),
        'recommended_products': recommended_products,
        'deferred_products': deferred_products,
        'explanation': explanation,
        'currency': settings.currency,
    }


def save_profit_advisor_analysis(user, analysis_data):
    from .models import ProfitAdvisorAnalysis
    return ProfitAdvisorAnalysis.save_analysis(user, analysis_data)


def get_latest_profit_advisor_analysis():
    from .models import ProfitAdvisorAnalysis
    latest = ProfitAdvisorAnalysis.get_latest()
    if not latest:
        return None
    return {
        'budget': str(latest.budget),
        'recommended_spending': str(latest.recommended_spending),
        'remaining_budget': str(latest.remaining_budget),
        'deferred_spending': str(
            sum(
                (Decimal(p['purchase_cost']) for p in latest.deferred_products),
                Decimal('0'),
            ),
        ),
        'expected_profit': str(latest.expected_profit),
        'recommended_count': latest.recommended_count,
        'recommended_products': latest.recommended_products,
        'deferred_products': latest.deferred_products,
        'explanation': latest.explanation,
        'analyzed_at': latest.created_at.isoformat(),
        'currency': BusinessSettings.get_solo().currency,
    }
