from rest_framework import generics, status
from rest_framework.response import Response

from common.permissions import IsOwnerOrReadOnly

from .filters import ProductFilter
from .models import Product
from .serializers import ProductListSerializer, ProductSerializer


def _response_with_warnings(serializer, data, status_code):
    warnings = getattr(serializer, '_warnings', [])
    if warnings:
        return Response({**data, 'warnings': warnings}, status=status_code)
    return Response(data, status=status_code)


class ProductListCreateView(generics.ListCreateAPIView):
    permission_classes = (IsOwnerOrReadOnly,)
    filterset_class = ProductFilter

    def get_queryset(self):
        return Product.objects.select_related('category', 'supplier').all()

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ProductListSerializer
        return ProductSerializer

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user,
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return _response_with_warnings(serializer, serializer.data, status.HTTP_201_CREATED)


class ProductDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsOwnerOrReadOnly,)
    serializer_class = ProductSerializer

    def get_queryset(self):
        return Product.objects.select_related('category', 'supplier').all()

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return _response_with_warnings(serializer, serializer.data, status.HTTP_200_OK)
