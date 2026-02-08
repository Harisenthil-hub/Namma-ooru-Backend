from django.urls import path
from .views import ProductListAPIView, HomeProductAPIView, CategoryListAPIView
from .admin_views import AdminProductListAPIView, AdminProductCreateAPIView, AdminProductUpdateAPIView, AdminProductDeleteAPIView

urlpatterns = [
    path('home/',HomeProductAPIView.as_view(),name='home-products'),
    path('list-products/',ProductListAPIView.as_view(),name='product-list'),
    path('categories/',CategoryListAPIView.as_view(),name='category-list'),
    path('admin-products/',AdminProductListAPIView.as_view(),name='admin-products-list'),
    path('create-product/',AdminProductCreateAPIView.as_view(),name='create-product'),
    path('update-product/<int:id>/',AdminProductUpdateAPIView.as_view(),name='update-product'),
    path('delete-product/<int:id>/',AdminProductDeleteAPIView.as_view(),name='delete-product'),
]
