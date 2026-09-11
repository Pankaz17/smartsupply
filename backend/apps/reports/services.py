from collections import defaultdict
from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, F, OuterRef, Subquery, Sum
from django.db.models.expressions import ExpressionWrapper
from django.db.models.fields import DecimalField
from django.db.models.functions import Coalesce, TruncDate
from django.utils import timezone

from apps.analytics.dead_stock_advisor import (
    format_suggestions_for_export,
    get_dead_stock_suggestions,
)
from apps.analytics.models import DeadStockSnapshot, DemandForecast, SupplierPerformanceSnapshot
from apps.products.models import Product
from apps.purchasing.models import ReorderRecommendation
from apps.sales.models import Sale

from .date_utils import parse_date_range


def _decimal_str(value):
    return str(value) if value is not None else '0'


def build_reports_overview():
    """Summary cards for /reports dashboard."""
    products = Product.objects.filter(is_active=True)
    total_value = products.aggregate(
        total=Coalesce(
            Sum(
                ExpressionWrapper(
                    F('current_stock') * F('cost_price'),
                    output_field=DecimalField(max_digits=14, decimal_places=2),
                ),
            ),
            Decimal('0'),
        ),
    )['total']

    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)
    revenue_30 = Sale.objects.filter(
        created_at__date__gte=thirty_days_ago,
    ).aggregate(total=Coalesce(Sum('total_amount'), Decimal('0')))['total']

    capital_at_risk = DeadStockSnapshot.objects.aggregate(
        total=Coalesce(Sum('inventory_value'), Decimal('0')),
    )['total']

    latest_dates = (
        SupplierPerformanceSnapshot.objects
        .filter(supplier=OuterRef('supplier'))
        .order_by('-snapshot_date')
        .values('snapshot_date')[:1]
    )
    snapshots = SupplierPerformanceSnapshot.objects.filter(
        snapshot_date=Subquery(latest_dates),
        total_orders__gt=0,
    )
    on_time_rates = [s.on_time_delivery_rate for s in snapshots]
    avg_on_time = (
        sum(on_time_rates) / len(on_time_rates) if on_time_rates else Decimal('0')
    )

    pending_recs = ReorderRecommendation.objects.filter(
        status=ReorderRecommendation.Status.PENDING,
    ).count()

    return {
        'total_inventory_value': _decimal_str(total_value),
        'revenue_30_days': _decimal_str(revenue_30),
        'capital_at_risk': _decimal_str(capital_at_risk),
        'supplier_on_time_rate': _decimal_str(round(avg_on_time, 1)),
        'pending_recommendations': pending_recs,
    }


def build_inventory_report(query_params):
    """Current inventory valuation snapshot."""
    start, end, range_label = parse_date_range(query_params, default_days=30)

    products = Product.objects.filter(is_active=True).select_related(
        'category', 'supplier',
    ).order_by('name')

    rows = []
    total_value = Decimal('0')
    for p in products:
        inv_value = Decimal(p.current_stock) * p.cost_price
        total_value += inv_value
        rows.append({
            'sku': p.sku,
            'product': p.name,
            'category': p.category.name,
            'supplier': p.supplier.name,
            'current_stock': p.current_stock,
            'cost_price': _decimal_str(p.cost_price),
            'inventory_value': _decimal_str(inv_value),
        })

    out_of_stock = products.filter(current_stock=0).count()

    by_category = defaultdict(Decimal)
    for p in products:
        by_category[p.category.name] += Decimal(p.current_stock) * p.cost_price

    chart = [
        {'category': k, 'value': float(v)}
        for k, v in sorted(by_category.items(), key=lambda x: -x[1])
    ]

    return {
        'date_range': {'start': str(start), 'end': str(end), 'range': range_label},
        'summary': {
            'total_inventory_value': _decimal_str(total_value),
            'total_products': products.count(),
            'out_of_stock_count': out_of_stock,
        },
        'rows': rows,
        'chart': {'inventory_value_by_category': chart},
    }


def build_sales_report(query_params):
    start, end, range_label = parse_date_range(query_params, default_days=30)

    sales_qs = Sale.objects.filter(
        created_at__date__gte=start,
        created_at__date__lte=end,
    )

    agg = sales_qs.aggregate(
        gross_sales=Coalesce(
            Sum(
                ExpressionWrapper(
                    F('quantity') * F('unit_price'),
                    output_field=DecimalField(max_digits=14, decimal_places=2),
                ),
            ),
            Decimal('0'),
        ),
        total_discounts=Coalesce(Sum('discount_amount'), Decimal('0')),
        net_sales=Coalesce(Sum('total_amount'), Decimal('0')),
        units_sold=Coalesce(Sum('quantity'), 0),
        transactions=Count('id'),
    )
    gross_sales = agg['gross_sales']
    total_discounts = agg['total_discounts']
    net_sales = agg['net_sales']
    units = agg['units_sold']
    transactions = agg['transactions']
    avg_sale = net_sales / transactions if transactions else Decimal('0')

    product_rows = (
        sales_qs.values('product__name', 'product__sku')
        .annotate(
            units_sold=Sum('quantity'),
            gross_total=Sum(
                ExpressionWrapper(
                    F('quantity') * F('unit_price'),
                    output_field=DecimalField(max_digits=14, decimal_places=2),
                ),
            ),
            discount_amount=Sum('discount_amount'),
            net_total=Sum('total_amount'),
        )
        .order_by('-net_total')
    )
    rows = [
        {
            'product': r['product__name'],
            'sku': r['product__sku'],
            'units_sold': r['units_sold'],
            'gross_total': _decimal_str(r['gross_total']),
            'discount_amount': _decimal_str(r['discount_amount']),
            'net_total': _decimal_str(r['net_total']),
        }
        for r in product_rows
    ]

    daily = (
        sales_qs.annotate(day=TruncDate('created_at'))
        .values('day')
        .annotate(net_sales=Sum('total_amount'))
        .order_by('day')
    )
    chart = [
        {'date': r['day'].isoformat(), 'net_sales': float(r['net_sales'] or 0)}
        for r in daily
    ]

    return {
        'date_range': {'start': str(start), 'end': str(end), 'range': range_label},
        'summary': {
            'gross_sales': _decimal_str(gross_sales),
            'total_discounts': _decimal_str(total_discounts),
            'net_sales': _decimal_str(net_sales),
            'units_sold': units,
            'transactions': transactions,
            'average_sale_value': _decimal_str(round(avg_sale, 2)),
        },
        'rows': rows,
        'chart': {'revenue_trend': chart},
    }


def build_dead_stock_report(query_params):
    start, end, range_label = parse_date_range(query_params, default_days=30)

    snapshots = DeadStockSnapshot.objects.filter(
        detected_at__date__gte=start,
        detected_at__date__lte=end,
    ).select_related('product', 'product__category').order_by('-inventory_value')

    rows = []
    for s in snapshots:
        suggestions = get_dead_stock_suggestions(s.days_without_sale)
        rows.append({
            'product': s.product.name,
            'sku': s.product.sku,
            'category': s.product.category.name,
            'days_without_sale': s.days_without_sale,
            'current_stock': s.current_stock,
            'inventory_value': _decimal_str(s.inventory_value),
            'severity': s.severity,
            'suggestions': suggestions,
            'suggested_action': format_suggestions_for_export(suggestions),
        })

    total_capital = snapshots.aggregate(
        total=Coalesce(Sum('inventory_value'), Decimal('0')),
    )['total']

    return {
        'date_range': {'start': str(start), 'end': str(end), 'range': range_label},
        'summary': {
            'dead_stock_count': snapshots.count(),
            'total_capital_at_risk': _decimal_str(total_capital),
        },
        'rows': rows,
        'chart': {},
    }


def build_supplier_report(query_params):
    start, end, range_label = parse_date_range(query_params, default_days=30)

    snapshots_in_range = (
        SupplierPerformanceSnapshot.objects.filter(
            snapshot_date__gte=start,
            snapshot_date__lte=end,
        )
        .select_related('supplier')
        .order_by('supplier_id', '-snapshot_date')
    )

    seen = set()
    snapshots = []
    for snapshot in snapshots_in_range:
        if snapshot.supplier_id in seen:
            continue
        seen.add(snapshot.supplier_id)
        snapshots.append(snapshot)
    snapshots.sort(key=lambda s: s.supplier.name)

    rows = []
    delays = []
    for s in snapshots:
        rows.append({
            'supplier': s.supplier.name,
            'promised_lead_time': _decimal_str(s.avg_promised_lead_time),
            'actual_lead_time': _decimal_str(s.avg_actual_lead_time),
            'average_delay': _decimal_str(s.avg_delay_days),
            'on_time_rate': _decimal_str(s.on_time_delivery_rate),
            'total_orders': s.total_orders,
        })
        if s.total_orders > 0:
            delays.append(s)

    best = worst = None
    if delays:
        best = max(delays, key=lambda x: x.on_time_delivery_rate)
        worst = min(delays, key=lambda x: x.on_time_delivery_rate)

    avg_delay = (
        sum(d.avg_delay_days for d in delays) / len(delays) if delays else Decimal('0')
    )

    chart = [
        {
            'supplier': s.supplier.name,
            'on_time_rate': float(s.on_time_delivery_rate),
        }
        for s in snapshots if s.total_orders > 0
    ]

    return {
        'date_range': {'start': str(start), 'end': str(end), 'range': range_label},
        'summary': {
            'best_supplier': best.supplier.name if best else None,
            'worst_supplier': worst.supplier.name if worst else None,
            'average_delay_across_suppliers': _decimal_str(round(avg_delay, 2)),
            'supplier_count': len(snapshots),
        },
        'rows': rows,
        'chart': {'on_time_rate_by_supplier': chart},
    }


def build_recommendations_report(query_params):
    start, end, range_label = parse_date_range(query_params, default_days=30)

    base_qs = ReorderRecommendation.objects.filter(
        generated_at__date__gte=start,
        generated_at__date__lte=end,
    )
    status_counts = base_qs.values('status').annotate(count=Count('id'))
    counts = {item['status']: item['count'] for item in status_counts}

    recs = base_qs.select_related('product').order_by('-generated_at')

    rows = [
        {
            'product': r.product.name,
            'sku': r.product.sku,
            'recommended_quantity': r.recommended_quantity,
            'operational_priority': r.priority_level,
            'generated_date': r.generated_at.date().isoformat(),
            'status': r.status,
            'approved_date': r.reviewed_at.date().isoformat() if r.reviewed_at else None,
        }
        for r in recs
    ]

    return {
        'date_range': {'start': str(start), 'end': str(end), 'range': range_label},
        'summary': {
            'total_recommendations': base_qs.count(),
            'approved': counts.get('approved', 0),
            'dismissed': counts.get('dismissed', 0),
            'pending': counts.get('pending', 0),
        },
        'rows': rows,
        'chart': {},
    }


def build_demand_forecast_report(query_params):
    """Latest demand forecasts per active product (advisory; no inventory changes)."""
    start, end, range_label = parse_date_range(query_params, default_days=30)
    today = timezone.now().date()

    latest = (
        DemandForecast.objects.filter(product=OuterRef('pk'))
        .order_by('-forecast_date')
        .values('id')[:1]
    )
    products = Product.objects.filter(is_active=True).annotate(
        latest_forecast_id=Subquery(latest),
    ).order_by('name')

    forecast_ids = [p.latest_forecast_id for p in products if p.latest_forecast_id]
    forecasts_by_id = {
        f.id: f
        for f in DemandForecast.objects.filter(id__in=forecast_ids).select_related('product')
    }

    rows = []
    available = 0
    insufficient = 0
    for product in products:
        forecast = forecasts_by_id.get(product.latest_forecast_id)
        if forecast is None:
            rows.append({
                'product': product.name,
                'sku': product.sku,
                'historical_ads': '0.00',
                'predicted_daily_demand': None,
                'forecast_horizon': 7,
                'model': None,
                'status': 'INSUFFICIENT_DATA',
                'historical_observations': 0,
                'mae': None,
            })
            insufficient += 1
            continue

        if forecast.status == DemandForecast.Status.FORECAST_AVAILABLE:
            available += 1
        else:
            insufficient += 1

        rows.append({
            'product': product.name,
            'sku': product.sku,
            'historical_ads': _decimal_str(forecast.historical_ads),
            'predicted_daily_demand': (
                _decimal_str(forecast.predicted_daily_demand)
                if forecast.predicted_daily_demand is not None
                else None
            ),
            'forecast_horizon': forecast.forecast_horizon,
            'model': forecast.model_name or None,
            'status': forecast.status,
            'historical_observations': forecast.historical_observations,
            'mae': _decimal_str(forecast.mae) if forecast.mae is not None else None,
        })

    chart = [
        {
            'product': row['product'],
            'predicted_daily_demand': float(row['predicted_daily_demand'] or 0),
        }
        for row in rows
        if row['status'] == 'FORECAST_AVAILABLE'
    ][:15]

    return {
        'date_range': {'start': str(start), 'end': str(end), 'range': range_label},
        'summary': {
            'products_with_forecast': available,
            'products_insufficient_data': insufficient,
            'forecast_as_of': str(today),
        },
        'rows': rows,
        'chart': {'predicted_demand_by_product': chart},
    }
