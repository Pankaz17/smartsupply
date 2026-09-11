from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsOwnerOrStaff

from .exports import build_export_response
from .services import (
    build_dead_stock_report,
    build_demand_forecast_report,
    build_inventory_report,
    build_recommendations_report,
    build_reports_overview,
    build_sales_report,
    build_supplier_report,
)

REPORT_CONFIG = {
    'inventory': {
        'builder': build_inventory_report,
        'filename': 'inventory_report',
        'columns': [
            {'key': 'sku', 'label': 'SKU'},
            {'key': 'product', 'label': 'Product'},
            {'key': 'category', 'label': 'Category'},
            {'key': 'supplier', 'label': 'Supplier'},
            {'key': 'current_stock', 'label': 'Current Stock'},
            {'key': 'cost_price', 'label': 'Cost Price'},
            {'key': 'inventory_value', 'label': 'Inventory Value'},
        ],
        'summary_keys': [
            'total_inventory_value', 'total_products', 'out_of_stock_count',
        ],
    },
    'sales': {
        'builder': build_sales_report,
        'filename': 'sales_report',
        'columns': [
            {'key': 'product', 'label': 'Product'},
            {'key': 'sku', 'label': 'SKU'},
            {'key': 'units_sold', 'label': 'Units Sold'},
            {'key': 'gross_total', 'label': 'Gross Total'},
            {'key': 'discount_amount', 'label': 'Discount Amount'},
            {'key': 'net_total', 'label': 'Net Total'},
        ],
        'summary_keys': [
            'gross_sales', 'total_discounts', 'net_sales',
            'units_sold', 'transactions', 'average_sale_value',
        ],
    },
    'dead-stock': {
        'builder': build_dead_stock_report,
        'filename': 'dead_stock_report',
        'columns': [
            {'key': 'product', 'label': 'Product'},
            {'key': 'sku', 'label': 'SKU'},
            {'key': 'days_without_sale', 'label': 'Days Without Sale'},
            {'key': 'current_stock', 'label': 'Current Stock'},
            {'key': 'inventory_value', 'label': 'Inventory Value'},
            {'key': 'severity', 'label': 'Severity'},
            {'key': 'suggested_action', 'label': 'Suggested Action'},
        ],
        'summary_keys': ['dead_stock_count', 'total_capital_at_risk'],
    },
    'suppliers': {
        'builder': build_supplier_report,
        'filename': 'supplier_report',
        'columns': [
            {'key': 'supplier', 'label': 'Supplier'},
            {'key': 'promised_lead_time', 'label': 'Promised Lead Time'},
            {'key': 'actual_lead_time', 'label': 'Actual Lead Time'},
            {'key': 'average_delay', 'label': 'Average Delay'},
            {'key': 'on_time_rate', 'label': 'On-Time Rate'},
            {'key': 'total_orders', 'label': 'Total Orders'},
        ],
        'summary_keys': [
            'best_supplier', 'worst_supplier',
            'average_delay_across_suppliers', 'supplier_count',
        ],
    },
    'recommendations': {
        'builder': build_recommendations_report,
        'filename': 'recommendations_report',
        'columns': [
            {'key': 'product', 'label': 'Product'},
            {'key': 'sku', 'label': 'SKU'},
            {'key': 'recommended_quantity', 'label': 'Recommended Quantity'},
            {'key': 'operational_priority', 'label': 'Operational Priority'},
            {'key': 'generated_date', 'label': 'Generated Date'},
            {'key': 'status', 'label': 'Status'},
            {'key': 'approved_date', 'label': 'Approved Date'},
        ],
        'summary_keys': [
            'total_recommendations', 'approved', 'dismissed', 'pending',
        ],
    },
    'demand-forecast': {
        'builder': build_demand_forecast_report,
        'filename': 'demand_forecast_report',
        'columns': [
            {'key': 'product', 'label': 'Product'},
            {'key': 'sku', 'label': 'SKU'},
            {'key': 'historical_ads', 'label': 'Historical ADS'},
            {'key': 'predicted_daily_demand', 'label': 'Predicted Daily Demand'},
            {'key': 'forecast_horizon', 'label': 'Forecast Horizon'},
            {'key': 'model', 'label': 'Model'},
            {'key': 'status', 'label': 'Status'},
            {'key': 'historical_observations', 'label': 'Historical Observations'},
            {'key': 'mae', 'label': 'MAE'},
        ],
        'summary_keys': [
            'products_with_forecast', 'products_insufficient_data', 'forecast_as_of',
        ],
    },
}


class ReportsOverviewView(APIView):
    permission_classes = (IsOwnerOrStaff,)

    def get(self, request):
        return Response(build_reports_overview())


class BaseReportView(APIView):
    permission_classes = (IsOwnerOrStaff,)
    report_key = None

    def get_config(self):
        return REPORT_CONFIG[self.report_key]

    def get(self, request):
        try:
            data = self.get_config()['builder'](request.query_params)
        except ValidationError as exc:
            return Response(exc.detail, status=400)
        return Response(data)


class BaseReportExportView(APIView):
    permission_classes = (IsOwnerOrStaff,)
    report_key = None

    def get(self, request):
        config = REPORT_CONFIG[self.report_key]
        fmt = request.query_params.get('export_format', 'csv')
        if fmt not in ('csv', 'xlsx'):
            return Response({'detail': 'export_format must be csv or xlsx.'}, status=400)

        try:
            data = config['builder'](request.query_params)
        except ValidationError as exc:
            return Response(exc.detail, status=400)
        summary = {k: data['summary'].get(k) for k in config['summary_keys']}

        return build_export_response(
            fmt,
            config['filename'],
            config['columns'],
            data['rows'],
            summary,
        )


class InventoryReportView(BaseReportView):
    report_key = 'inventory'


class InventoryReportExportView(BaseReportExportView):
    report_key = 'inventory'


class SalesReportView(BaseReportView):
    report_key = 'sales'


class SalesReportExportView(BaseReportExportView):
    report_key = 'sales'


class DeadStockReportView(BaseReportView):
    report_key = 'dead-stock'


class DeadStockReportExportView(BaseReportExportView):
    report_key = 'dead-stock'


class SupplierReportView(BaseReportView):
    report_key = 'suppliers'


class SupplierReportExportView(BaseReportExportView):
    report_key = 'suppliers'


class RecommendationsReportView(BaseReportView):
    report_key = 'recommendations'


class RecommendationsReportExportView(BaseReportExportView):
    report_key = 'recommendations'


class DemandForecastReportView(BaseReportView):
    report_key = 'demand-forecast'


class DemandForecastReportExportView(BaseReportExportView):
    report_key = 'demand-forecast'
