from django_filters import rest_framework as filters

from .models import Product


class ProductFilter(filters.FilterSet):
    search = filters.CharFilter(method='filter_search')
    category = filters.NumberFilter(field_name='category_id')
    supplier = filters.NumberFilter(field_name='supplier_id')
    is_active = filters.BooleanFilter()

    class Meta:
        model = Product
        fields = ['category', 'supplier', 'is_active']

    def filter_search(self, queryset, name, value):
        from django.db.models import Q
        return queryset.filter(Q(name__icontains=value) | Q(sku__icontains=value))
