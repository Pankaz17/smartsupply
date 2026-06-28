from rest_framework import serializers

from .models import Supplier


class SupplierSerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Supplier
        fields = (
            'id',
            'name',
            'phone',
            'email',
            'address',
            'promised_lead_time_days',
            'is_active',
            'notes',
            'product_count',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at', 'product_count')

    def validate_promised_lead_time_days(self, value):
        if value < 1:
            raise serializers.ValidationError(
                'Promised lead time must be at least 1 day.',
            )
        return value

    def get_product_count(self, obj):
        return obj.products.count()
