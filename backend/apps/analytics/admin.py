from django.contrib import admin

from .models import DeadStockSnapshot, DemandForecast, SeasonalEvent, SupplierPerformanceSnapshot

admin.site.register(SeasonalEvent)
admin.site.register(DeadStockSnapshot)
admin.site.register(SupplierPerformanceSnapshot)
admin.site.register(DemandForecast)
