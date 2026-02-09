from django.urls import path
from .views import AdminSummaryAnalyticsAPIView, AdminPendingAnalyticsAPIView, AdminChartAnalyticsAPIView


urlpatterns = [
    path('admin/summary/',AdminSummaryAnalyticsAPIView.as_view(),name='admin-analytics-summary'),
    path('admin/pending/',AdminPendingAnalyticsAPIView.as_view(),name='admin-pending-analytics'),
    path('admin/charts/',AdminChartAnalyticsAPIView.as_view(),name='admin-chart-analytics'),
]
