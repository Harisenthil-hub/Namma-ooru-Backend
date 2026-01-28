from django.urls import path
from .views import ProductListApiView

urlpatterns = [
    path('list-products/',ProductListApiView.as_view(),name='product-list')
]
