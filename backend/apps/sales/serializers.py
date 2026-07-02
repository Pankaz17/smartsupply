from django.core.exceptions import ValidationError as DjangoValidationError
from decimal import Decimal
from rest_framework import serializers

from apps.products.models import Product

from .models import Sale


class SaleSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    recorded_by_name = serializers.CharField(source='recorded_by.full_name', read_only=True)
    gross_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Sale
        fields = (
            'id',
            'product',
            'product_name',
            'product_sku',
            'quantity',
            'unit_price',
            'gross_total',
            'discount_amount',
            'total_amount',
            'recorded_by',
            'recorded_by_name',
            'created_at',
        )
        read_only_fields = (
            'id',
            'total_amount',
            'recorded_by',
            'recorded_by_name',
            'created_at',
            'product_name',
            'product_sku',
        )


class SaleCreateSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(is_active=True),
    )
    quantity = serializers.IntegerField(min_value=1)
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)
    discount_amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, min_value=0, required=False, default=Decimal('0.00'),
    )

    def validate_product(self, value):
        if not value.is_active:
            raise serializers.ValidationError('Cannot sell an inactive product.')
        return value

    def validate(self, attrs):
        product = attrs['product']
        quantity = attrs['quantity']
        unit_price = attrs['unit_price']
        discount_amount = attrs.get('discount_amount', Decimal('0.00'))
        if quantity > product.current_stock:
            raise serializers.ValidationError({
                'quantity': (
                    f'Insufficient stock. Available: {product.current_stock}, '
                    f'requested: {quantity}.'
                ),
            })
        gross_total = Decimal(quantity) * unit_price
        if discount_amount > gross_total:
            raise serializers.ValidationError({
                'discount_amount': 'Discount amount cannot exceed gross total.',
            })
        return attrs

    def create(self, validated_data):
        try:
            return Sale.record_sale(
                product=validated_data['product'],
                quantity=validated_data['quantity'],
                unit_price=validated_data['unit_price'],
                discount_amount=validated_data.get('discount_amount', Decimal('0.00')),
                recorded_by=self.context['request'].user,
            )
        except DjangoValidationError as exc:
            message = exc.messages[0] if getattr(exc, 'messages', None) else str(exc)
            if 'stock' in message.lower() or 'insufficient' in message.lower():
                raise serializers.ValidationError({'quantity': message})
            if 'discount' in message.lower():
                raise serializers.ValidationError({'discount_amount': message})
            raise serializers.ValidationError({'detail': message})
