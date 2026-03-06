from django.urls import path
from .views import AdminLoginAPIView, AdminLogoutAPIView, AdminRefreshAPIView, AdminCheckAPIView, APIRuncheck


urlpatterns = [
    path('login/',AdminLoginAPIView.as_view(),name='admin-login'),
    path('logout/',AdminLogoutAPIView.as_view(),name='admin-logout'),
    path('refresh/',AdminRefreshAPIView.as_view(),name='admin-refresh'),
    path('admin-check/',AdminCheckAPIView.as_view(),name='admin-check'),
    path('api-run-check/',APIRuncheck.as_view(),name='api-run-check'),
]
