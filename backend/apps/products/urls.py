from django.urls import path

from .category_views import ProductCategoryDetailView, ProductCategoryListCreateView
from .views import ProductDetailView, ProductListCreateView

urlpatterns = [
    path('categories/', ProductCategoryListCreateView.as_view(), name='category-list'),
    path('categories/<int:pk>/', ProductCategoryDetailView.as_view(), name='category-detail'),
    path('products/', ProductListCreateView.as_view(), name='product-list'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
]
