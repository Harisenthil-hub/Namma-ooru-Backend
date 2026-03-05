from django.urls import path
from .views import CreateOrderAPIView
from .admin_views import AdminOrderListAPIView, AdminOrderStatusUpdateAPIView, AdminCustomerListAPIView
from .exports import AdminOrderExportAPIView, AdminCustomerExportAPIView

urlpatterns = [
    path('create/',CreateOrderAPIView.as_view(), name='create-order'),
    path('admin/orders-list/',AdminOrderListAPIView.as_view(),name='admin-orders-list'),
    path('admin/<str:order_number>/status/',AdminOrderStatusUpdateAPIView.as_view(),name='admin-order-upadate'),
    path('admin/customers/',AdminCustomerListAPIView.as_view(),name='admin-customer-list'),
    path('admin/order-export/',AdminOrderExportAPIView.as_view(),name='admin-order-export'),
    path('admin/customer-export/',AdminCustomerExportAPIView.as_view(),name='admin-customer-export'),
]
