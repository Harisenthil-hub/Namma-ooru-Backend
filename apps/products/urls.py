from django.urls import path
from .views import ProductListAPIView, HomeProductAPIView
from .admin_views import AdminProductCreateAPIView, AdminProductUpdateAPIView, AdminProductDeleteAPIView

urlpatterns = [
    path('home/',HomeProductAPIView.as_view(),name='home-products'),
    path('list-products/',ProductListAPIView.as_view(),name='product-list'),
    path('create-product/',AdminProductCreateAPIView.as_view(),name='create-product'),
    path('update-product/<slug:slug>/',AdminProductUpdateAPIView.as_view(),name='update-product'),
    path('delete-product/<slug:slug>/',AdminProductDeleteAPIView.as_view(),name='delete-product'),
]
