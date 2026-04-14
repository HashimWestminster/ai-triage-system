# accounts/urls.py - auth and user management routes

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.CustomTokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('me/', views.me, name='me'),
    path('users/', views.user_list, name='user_list'),
    path('surgery-status/', views.surgery_status, name='surgery_status'),
    path('surgery-hours/', views.surgery_hours, name='surgery_hours'),
]
