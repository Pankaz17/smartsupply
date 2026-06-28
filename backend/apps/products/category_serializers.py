from rest_framework import serializers

from .models import ProductCategory


class ProductCategorySerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = ProductCategory
        fields = (
            'id',
            'name',
            'description',
            'is_active',
            'product_count',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at', 'product_count')

    def get_product_count(self, obj):
        return obj.products.count()
