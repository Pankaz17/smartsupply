from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction


class Sale(models.Model):
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.PROTECT,
        related_name='sales',
    )
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='sales_recorded',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Sale #{self.pk} — {self.product.name} x{self.quantity}'

    def clean(self):
        if self.product_id and self.quantity > self.product.current_stock:
            raise ValidationError(
                f'Insufficient stock. Available: {self.product.current_stock}, '
                f'requested: {self.quantity}.'
            )
        if self.discount_amount < 0:
            raise ValidationError('Discount amount cannot be negative.')
        if self.discount_amount > self.gross_total:
            raise ValidationError('Discount amount cannot exceed gross total.')

    @property
    def gross_total(self):
        return Decimal(self.quantity) * self.unit_price

    def save(self, *args, **kwargs):
        if not self.total_amount:
            self.total_amount = self.gross_total - self.discount_amount
        self.full_clean()
        super().save(*args, **kwargs)

    @classmethod
    @transaction.atomic
    def record_sale(cls, product, quantity, unit_price, recorded_by, discount_amount=Decimal('0.00')):
        product = type(product).objects.select_for_update().get(pk=product.pk)

        if quantity > product.current_stock:
            raise ValidationError(
                f'Insufficient stock. Available: {product.current_stock}, '
                f'requested: {quantity}.'
            )

        gross_total = Decimal(quantity) * unit_price
        discount_amount = Decimal(discount_amount or 0)
        if discount_amount < 0:
            raise ValidationError('Discount amount cannot be negative.')
        if discount_amount > gross_total:
            raise ValidationError('Discount amount cannot exceed gross total.')
        total_amount = gross_total - discount_amount
        sale = cls.objects.create(
            product=product,
            quantity=quantity,
            unit_price=unit_price,
            discount_amount=discount_amount,
            total_amount=total_amount,
            recorded_by=recorded_by,
        )

        product.current_stock -= quantity
        product.save(update_fields=['current_stock', 'updated_at'])

        from apps.notifications.services import check_stock_notifications
        check_stock_notifications(product)

        return sale
