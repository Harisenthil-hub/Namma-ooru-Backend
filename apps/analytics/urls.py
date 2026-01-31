from django.urls import path
from .views import AdminSummaryAnalyticsAPIView, AdminPendingAnalyticsAPIView, AdminChartAnalyticsAPIView


urlpatterns = [
    path('admin/analytics/summary/',AdminSummaryAnalyticsAPIView.as_view(),name='admin-analytics-summary'),
    path('admin/analytics/pending/',AdminPendingAnalyticsAPIView.as_view(),name='admin-pending-analytics'),
    path('admin/analytics/charts/',AdminChartAnalyticsAPIView.as_view(),name='admin-chart-analytics'),
]
