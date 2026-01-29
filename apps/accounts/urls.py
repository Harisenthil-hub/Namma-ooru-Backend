from django.urls import path
from .views import AdminLoginAPIView, AdminLogoutAPIView, AdminRefreshAPIView


urlpatterns = [
    path('login/',AdminLoginAPIView.as_view(),name='admin-login'),
    path('logout/',AdminLogoutAPIView.as_view(),name='admin-logout'),
    path('refresh/',AdminRefreshAPIView.as_view(),name='admin-refresh'),
]
