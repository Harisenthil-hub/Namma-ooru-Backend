from django.urls import path
from .views import AdminLoginAPIView, AdminLogoutAPIView


urlpatterns = [
    path('login/',AdminLoginAPIView.as_view(),name='admin-login'),
    path('logout/',AdminLogoutAPIView.as_view(),name='admin-logout'),
]
