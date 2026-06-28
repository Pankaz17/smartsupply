from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='related_product.name', read_only=True, default=None)
    supplier_name = serializers.CharField(source='related_supplier.name', read_only=True, default=None)
    purchase_order_number = serializers.CharField(
        source='related_purchase_order.po_number',
        read_only=True,
        default=None,
    )

    class Meta:
        model = Notification
        fields = (
            'id',
            'title',
            'message',
            'notification_type',
            'is_read',
            'created_at',
            'read_at',
            'related_product',
            'related_supplier',
            'related_purchase_order',
            'product_name',
            'supplier_name',
            'purchase_order_number',
        )
        read_only_fields = fields
