from rest_framework import generics

from common.permissions import IsOwnerOrReadOnly

from .models import Supplier
from .serializers import SupplierSerializer


class SupplierListCreateView(generics.ListCreateAPIView):
    permission_classes = (IsOwnerOrReadOnly,)
    serializer_class = SupplierSerializer
    queryset = Supplier.objects.all()

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user,
        )


class SupplierDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsOwnerOrReadOnly,)
    serializer_class = SupplierSerializer
    queryset = Supplier.objects.all()

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
