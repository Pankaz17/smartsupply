from decimal import Decimal
import math
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone

from common.models import TimeStampedModel


class ReorderRecommendation(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        DISMISSED = 'dismissed', 'Dismissed'

    class PriorityLevel(models.TextChoices):
        HIGH = 'HIGH', 'High'
        MEDIUM = 'MEDIUM', 'Medium'
        LOW = 'LOW', 'Low'

    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='reorder_recommendations',
    )
    supplier = models.ForeignKey(
        'suppliers.Supplier',
        on_delete=models.PROTECT,
        related_name='reorder_recommendations',
    )
    current_stock = models.PositiveIntegerField()
    recommended_quantity = models.PositiveIntegerField()
    average_daily_sales = models.DecimalField(max_digits=10, decimal_places=2)
    lead_time_days = models.PositiveIntegerField()
    safety_stock = models.DecimalField(max_digits=10, decimal_places=2)
    calculated_reorder_point = models.DecimalField(max_digits=10, decimal_places=2)
    unit_profit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    priority_score = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    expected_restock_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    priority_level = models.CharField(
        max_length=10,
        choices=PriorityLevel.choices,
        default=PriorityLevel.LOW,
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )
    reason = models.TextField()
    generated_at = models.DateTimeField(default=timezone.now)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    purchase_order = models.ForeignKey(
        'purchasing.PurchaseOrder',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='source_recommendations',
    )

    class Meta:
        ordering = ['-priority_score', '-generated_at']

    def __str__(self):
        return f'Recommendation for {self.product.name} ({self.status})'


class PurchaseOrder(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        ORDERED = 'ordered', 'Ordered'
        RECEIVED = 'received', 'Received'
        CANCELLED = 'cancelled', 'Cancelled'

    po_number = models.CharField(max_length=20, unique=True)
    supplier = models.ForeignKey(
        'suppliers.Supplier',
        on_delete=models.PROTECT,
        related_name='purchase_orders',
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    expected_delivery_date = models.DateField(null=True, blank=True)
    actual_delivery_date = models.DateField(null=True, blank=True)
    ordered_at = models.DateField(
        null=True,
        blank=True,
        help_text='Date the PO was marked as ordered. Set once on DRAFT → ORDERED.',
    )
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='purchase_orders_created',
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='purchase_orders_approved',
    )
    stock_applied = models.BooleanField(
        default=False,
        help_text='Prevents double stock updates when receiving.',
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.po_number

    @classmethod
    def generate_po_number(cls):
        prefix = timezone.now().strftime('PO-%Y')
        last = (
            cls.objects.filter(po_number__startswith=prefix)
            .order_by('-po_number')
            .first()
        )
        if last:
            try:
                seq = int(last.po_number.split('-')[-1]) + 1
            except ValueError:
                seq = cls.objects.filter(po_number__startswith=prefix).count() + 1
        else:
            seq = 1
        return f'{prefix}-{seq:04d}'

    @transaction.atomic
    def transition_status(self, new_status, user, actual_delivery_date=None):
        if new_status not in dict(self.Status.choices):
            raise ValidationError('Invalid status.')

        allowed = {
            self.Status.DRAFT: {self.Status.ORDERED, self.Status.CANCELLED},
            self.Status.ORDERED: {self.Status.RECEIVED, self.Status.CANCELLED},
            self.Status.RECEIVED: set(),
            self.Status.CANCELLED: set(),
        }

        if new_status not in allowed.get(self.status, set()):
            raise ValidationError(
                f'Cannot transition from {self.status} to {new_status}.',
            )

        if new_status == self.Status.ORDERED:
            self.approved_by = user
            if not self.ordered_at:
                self.ordered_at = timezone.now().date()
            self.expected_delivery_date = (
                self.ordered_at + timedelta(days=self.supplier.promised_lead_time_days)
            )
            if self.expected_delivery_date < self.ordered_at:
                raise ValidationError(
                    'Expected delivery date cannot be before the order date.',
                )

        if new_status == self.Status.RECEIVED:
            if self.stock_applied:
                raise ValidationError('Stock has already been applied for this order.')
            delivery_date = actual_delivery_date or timezone.now().date()
            if self.ordered_at and delivery_date < self.ordered_at:
                raise ValidationError(
                    'Actual delivery date cannot be before the order date.',
                )
            self._apply_stock()
            self.actual_delivery_date = delivery_date
            self.stock_applied = True

            if (
                self.expected_delivery_date
                and self.actual_delivery_date > self.expected_delivery_date
            ):
                from apps.notifications.services import notify_supplier_delay
                notify_supplier_delay(self)

        self.status = new_status
        self.save()
        return self

    def _apply_stock(self):
        from apps.products.models import Product

        for item in self.items.select_related('product'):
            product = Product.objects.select_for_update().get(pk=item.product_id)
            product.current_stock += item.quantity
            product.save(update_fields=['current_stock', 'updated_at'])


class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name='items',
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.PROTECT,
        related_name='purchase_order_items',
    )
    quantity = models.PositiveIntegerField()
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f'{self.product.name} x{self.quantity}'

    def save(self, *args, **kwargs):
        self.total_cost = Decimal(self.quantity) * self.unit_cost
        super().save(*args, **kwargs)
