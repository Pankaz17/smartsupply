from django.core.exceptions import ValidationError as DjangoValidationError
from decimal import Decimal
from django.utils import timezone
from rest_framework import serializers

from apps.products.models import Product
from apps.suppliers.models import Supplier

from .models import PurchaseOrder, PurchaseOrderItem, ReorderRecommendation


class ReorderRecommendationSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    purchase_order_number = serializers.CharField(
        source='purchase_order.po_number',
        read_only=True,
        default=None,
    )

    class Meta:
        model = ReorderRecommendation
        fields = (
            'id',
            'product',
            'product_name',
            'product_sku',
            'supplier',
            'supplier_name',
            'current_stock',
            'recommended_quantity',
            'average_daily_sales',
            'lead_time_days',
            'safety_stock',
            'calculated_reorder_point',
            'priority_level',
            'status',
            'reason',
            'generated_at',
            'reviewed_at',
            'purchase_order',
            'purchase_order_number',
        )
        read_only_fields = fields


class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)

    class Meta:
        model = PurchaseOrderItem
        fields = (
            'id',
            'product',
            'product_name',
            'product_sku',
            'quantity',
            'unit_cost',
            'total_cost',
        )
        read_only_fields = fields


class PurchaseOrderListSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = PurchaseOrder
        fields = (
            'id',
            'po_number',
            'supplier',
            'supplier_name',
            'created_from',
            'status',
            'ordered_at',
            'expected_delivery_date',
            'actual_delivery_date',
            'item_count',
            'created_by_name',
            'created_at',
            'updated_at',
        )

    def get_item_count(self, obj):
        return obj.items.count()


class PurchaseOrderDetailSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    approved_by_name = serializers.CharField(
        source='approved_by.full_name',
        read_only=True,
        default=None,
    )
    items = PurchaseOrderItemSerializer(many=True, read_only=True)
    total_cost = serializers.SerializerMethodField()

    class Meta:
        model = PurchaseOrder
        fields = (
            'id',
            'po_number',
            'supplier',
            'supplier_name',
            'created_from',
            'status',
            'ordered_at',
            'expected_delivery_date',
            'actual_delivery_date',
            'notes',
            'created_by',
            'created_by_name',
            'approved_by',
            'approved_by_name',
            'stock_applied',
            'items',
            'total_cost',
            'created_at',
            'updated_at',
        )
        read_only_fields = fields

    def get_total_cost(self, obj):
        return str(sum(item.total_cost for item in obj.items.all()))


class PurchaseOrderStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=PurchaseOrder.Status.choices)
    actual_delivery_date = serializers.DateField(required=False, allow_null=True)

    def validate(self, attrs):
        po = self.context.get('purchase_order')

        if attrs['status'] == PurchaseOrder.Status.RECEIVED:
            if not attrs.get('actual_delivery_date'):
                attrs['actual_delivery_date'] = timezone.now().date()

            actual = attrs['actual_delivery_date']
            if po and po.ordered_at and actual < po.ordered_at:
                raise serializers.ValidationError({
                    'actual_delivery_date': (
                        'Actual delivery date cannot be before the order date.'
                    ),
                })

        return attrs


class PurchaseOrderCreateSerializer(serializers.Serializer):
    supplier = serializers.PrimaryKeyRelatedField(queryset=Supplier.objects.filter(is_active=True))
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.filter(is_active=True))
    quantity = serializers.IntegerField(min_value=1)
    unit_cost = serializers.DecimalField(
        max_digits=10, decimal_places=2, min_value=Decimal('0.00'), required=False,
    )
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        supplier = attrs['supplier']
        product = attrs['product']
        if product.supplier_id != supplier.id:
            raise serializers.ValidationError({
                'product': 'Selected product does not belong to the selected supplier.',
            })
        return attrs

    def create(self, validated_data):
        supplier = validated_data['supplier']
        product = validated_data['product']
        quantity = validated_data['quantity']
        unit_cost = validated_data.get('unit_cost', product.cost_price)
        notes = validated_data.get('notes', '')
        user = self.context['request'].user

        po = PurchaseOrder.objects.create(
            po_number=PurchaseOrder.generate_po_number(),
            supplier=supplier,
            status=PurchaseOrder.Status.DRAFT,
            created_from=PurchaseOrder.Source.MANUAL,
            notes=notes,
            created_by=user,
        )
        PurchaseOrderItem.objects.create(
            purchase_order=po,
            product=product,
            quantity=quantity,
            unit_cost=unit_cost,
        )
        return po
