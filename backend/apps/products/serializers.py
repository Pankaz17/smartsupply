from rest_framework import serializers

from .models import Product

STOCK_READ_ONLY_MSG = (
    'Stock levels cannot be edited directly. Stock changes occur through '
    'sales and purchase order receipts.'
)


class ProductListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)

    class Meta:
        model = Product
        fields = (
            'id',
            'sku',
            'name',
            'category',
            'category_name',
            'supplier',
            'supplier_name',
            'cost_price',
            'selling_price',
            'current_stock',
            'unit',
            'is_active',
            'created_at',
            'updated_at',
        )


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)

    class Meta:
        model = Product
        fields = (
            'id',
            'sku',
            'name',
            'category',
            'category_name',
            'supplier',
            'supplier_name',
            'cost_price',
            'selling_price',
            'current_stock',
            'unit',
            'is_active',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'current_stock', 'created_at', 'updated_at')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._warnings = []

    def validate_category(self, value):
        if not value.is_active:
            raise serializers.ValidationError('Cannot assign an inactive category.')
        return value

    def validate_supplier(self, value):
        if not value.is_active:
            raise serializers.ValidationError('Cannot assign an inactive supplier.')
        return value

    def validate_cost_price(self, value):
        if value < 0:
            raise serializers.ValidationError('Cost price cannot be negative.')
        return value

    def validate_selling_price(self, value):
        if value < 0:
            raise serializers.ValidationError('Selling price cannot be negative.')
        return value

    def validate(self, attrs):
        if 'current_stock' in self.initial_data:
            raise serializers.ValidationError({
                'current_stock': STOCK_READ_ONLY_MSG,
            })

        cost = attrs.get('cost_price', getattr(self.instance, 'cost_price', None))
        selling = attrs.get('selling_price', getattr(self.instance, 'selling_price', None))
        if cost is not None and selling is not None and selling < cost:
            self._warnings.append(
                'Selling price is below cost price. Each sale may result in a loss.',
            )
        return attrs
