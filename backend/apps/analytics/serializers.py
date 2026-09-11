from rest_framework import serializers

from .dead_stock_advisor import get_dead_stock_suggestions
from .models import DeadStockSnapshot, DemandForecast, SeasonalEvent, SupplierPerformanceSnapshot
from .supplier_insights import build_supplier_insights


class SeasonalEventSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = SeasonalEvent
        fields = (
            'id',
            'name',
            'start_date',
            'end_date',
            'category',
            'category_name',
            'multiplier',
            'is_active',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at', 'category_name')

    def validate_multiplier(self, value):
        if value <= 0:
            raise serializers.ValidationError('Multiplier must be greater than zero.')
        return value

    def validate(self, attrs):
        start = attrs.get('start_date', getattr(self.instance, 'start_date', None))
        end = attrs.get('end_date', getattr(self.instance, 'end_date', None))
        if start and end and start > end:
            raise serializers.ValidationError({
                'end_date': 'End date must be on or after the start date.',
            })
        return attrs


class DeadStockSnapshotSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    category_name = serializers.CharField(source='product.category.name', read_only=True)
    suggestions = serializers.SerializerMethodField()

    class Meta:
        model = DeadStockSnapshot
        fields = (
            'id',
            'product',
            'product_name',
            'product_sku',
            'category_name',
            'days_without_sale',
            'current_stock',
            'inventory_value',
            'severity',
            'suggestions',
            'detected_at',
        )
        read_only_fields = fields

    def get_suggestions(self, obj):
        return get_dead_stock_suggestions(obj.days_without_sale)


class SupplierPerformanceSnapshotSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    supplier_insights = serializers.SerializerMethodField()

    class Meta:
        model = SupplierPerformanceSnapshot
        fields = (
            'id',
            'supplier',
            'supplier_name',
            'avg_promised_lead_time',
            'avg_actual_lead_time',
            'avg_delay_days',
            'on_time_delivery_rate',
            'total_orders',
            'snapshot_date',
            'supplier_insights',
        )
        read_only_fields = fields

    def get_supplier_insights(self, obj):
        return build_supplier_insights(obj)


class DemandForecastSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    model = serializers.SerializerMethodField()
    predicted_daily_demand = serializers.SerializerMethodField()
    predicted_horizon_total = serializers.SerializerMethodField()
    historical_ads = serializers.SerializerMethodField()
    mae = serializers.SerializerMethodField()
    fallback = serializers.SerializerMethodField()

    class Meta:
        model = DemandForecast
        fields = (
            'id',
            'product',
            'product_name',
            'product_sku',
            'forecast_date',
            'forecast_horizon',
            'predicted_daily_demand',
            'predicted_horizon_total',
            'model',
            'historical_observations',
            'historical_ads',
            'status',
            'mae',
            'trend',
            'fallback',
            'created_at',
            'updated_at',
        )
        read_only_fields = fields

    def get_model(self, obj):
        return obj.model_name or None

    def _dec(self, value):
        return str(value) if value is not None else None

    def get_predicted_daily_demand(self, obj):
        return self._dec(obj.predicted_daily_demand)

    def get_predicted_horizon_total(self, obj):
        return self._dec(obj.predicted_horizon_total)

    def get_historical_ads(self, obj):
        return self._dec(obj.historical_ads)

    def get_mae(self, obj):
        return self._dec(obj.mae)

    def get_fallback(self, obj):
        if obj.status == DemandForecast.Status.INSUFFICIENT_DATA:
            return 'Historical ADS'
        return None
