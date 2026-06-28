from django.contrib import admin

from .models import PurchaseOrder, PurchaseOrderItem, ReorderRecommendation

admin.site.register(ReorderRecommendation)
admin.site.register(PurchaseOrder)
admin.site.register(PurchaseOrderItem)
