from rest_framework import serializers

from .dead_stock_advisor import get_dead_stock_suggestions
from .models import DeadStockSnapshot, SeasonalEvent, SupplierPerformanceSnapshot
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
