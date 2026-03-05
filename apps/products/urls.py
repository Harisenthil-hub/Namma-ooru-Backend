from django.urls import path
from .views import ProductListAPIView, HomeProductAPIView, CategoryListAPIView, ProductSearchSuggestionAPIView, DealsProductListAPIView
from .admin_views import AdminProductListAPIView, AdminProductCreateAPIView, AdminProductUpdateAPIView, AdminProductDeleteAPIView
from .admin_views import AdminProductVariantCreateAPIView, AdminProductVariantUpdateAPIView, AdminProductVariantDeleteAPIView
from .admin_views import AdminCategoryListAPIView, AdminCreatCategoryAPIView, AdminUpdateCategoryAPIView, AdminProductExportAPIView


urlpatterns = [
    path('home/',HomeProductAPIView.as_view(),name='home-products'),
    path('list-products/',ProductListAPIView.as_view(),name='product-list'),
    path('deals-products/',DealsProductListAPIView.as_view(),name='deals-list'),
    path('categories/',CategoryListAPIView.as_view(),name='category-list'),
    path('search-suggestions/',ProductSearchSuggestionAPIView.as_view(),name='product-search-suggestions'),
    path('admin-products/',AdminProductListAPIView.as_view(),name='admin-products-list'),
    path('create-product/',AdminProductCreateAPIView.as_view(),name='create-product'),
    path('update-product/<int:id>/',AdminProductUpdateAPIView.as_view(),name='update-product'),
    path('delete-product/<int:id>/',AdminProductDeleteAPIView.as_view(),name='delete-product'),
    path('variants/',AdminProductVariantCreateAPIView.as_view(),name='create-variant'),
    path('update-variants/<int:product_id>/',AdminProductVariantUpdateAPIView.as_view(),name='update-variant'),
    path('variants/<int:id>/',AdminProductVariantDeleteAPIView.as_view(),name='delete-variant'),
    path('admin-categories/',AdminCategoryListAPIView.as_view(),name='admin-category'),
    path('create-category/',AdminCreatCategoryAPIView.as_view(),name='create-category'),
    path('update-category/<int:pk>/',AdminUpdateCategoryAPIView.as_view(),name='update-category'),
    path('admin/products-export/',AdminProductExportAPIView.as_view(),name='product-export'),
]
