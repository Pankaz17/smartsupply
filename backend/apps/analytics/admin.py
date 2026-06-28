from django.contrib import admin

from .models import DeadStockSnapshot, SeasonalEvent, SupplierPerformanceSnapshot

admin.site.register(SeasonalEvent)
admin.site.register(DeadStockSnapshot)
admin.site.register(SupplierPerformanceSnapshot)
