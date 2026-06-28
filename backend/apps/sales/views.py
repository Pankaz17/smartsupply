from rest_framework import generics

from common.permissions import IsOwnerOrStaff

from .models import Sale
from .serializers import SaleCreateSerializer, SaleSerializer


class SaleListCreateView(generics.ListCreateAPIView):
    permission_classes = (IsOwnerOrStaff,)

    def get_queryset(self):
        return Sale.objects.select_related('product', 'recorded_by').all()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return SaleCreateSerializer
        return SaleSerializer
