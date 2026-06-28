from django.urls import path

from .settings_views import BusinessSettingsView
from .views import StaffDetailView, StaffListCreateView

urlpatterns = [
    path('settings/', BusinessSettingsView.as_view(), name='business-settings'),
    path('staff/', StaffListCreateView.as_view(), name='staff-list-create'),
    path('staff/<int:pk>/', StaffDetailView.as_view(), name='staff-detail'),
]
