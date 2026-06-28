from django.urls import path

from .views import LoginView, MeView, PasswordChangeView, RefreshView

urlpatterns = [
    path('login/', LoginView.as_view(), name='auth-login'),
    path('refresh/', RefreshView.as_view(), name='auth-refresh'),
    path('me/', MeView.as_view(), name='auth-me'),
    path('change-password/', PasswordChangeView.as_view(), name='auth-change-password'),
]
