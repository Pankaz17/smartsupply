from rest_framework import generics

from common.permissions import IsOwnerOrReadOnly

from .category_serializers import ProductCategorySerializer
from .models import ProductCategory


class ProductCategoryListCreateView(generics.ListCreateAPIView):
    permission_classes = (IsOwnerOrReadOnly,)
    serializer_class = ProductCategorySerializer
    queryset = ProductCategory.objects.all()

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user,
        )


class ProductCategoryDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsOwnerOrReadOnly,)
    serializer_class = ProductCategorySerializer
    queryset = ProductCategory.objects.all()

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
