
# students/urls.py - UPDATED WITH API ENDPOINTS

from django.urls import path
from . import views

urlpatterns = [
    # Main pages
    path('', views.home_view, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),

    # ✅ NEW: API endpoints for attendance data
    path('api/attendance/', views.get_attendance_data, name='get_attendance_data'),
    path('api/notifications/', views.get_notifications, name='get_notifications'),
    path('api/mark-read/', views.mark_notification_read, name='mark_notification_read'),
    
    path('api/notices/', views.get_notices, name='get_notices'),
    path('api/notices/mark-read/', views.mark_notice_read, name='mark_notice_read'),
    path('api/notifications/combined/', views.get_combined_notifications, name='combined_notifications'),
]