# requests/urls.py - FIXED VERSION

from django.urls import path
from . import views

app_name = 'requests'

urlpatterns = [
    # Student Request APIs
    path('requests/', views.StudentRequestListCreateView.as_view(), name='student_requests'),
    path("requests/", views.StudentRequestListCreateView.as_view(), name="studentrequests"),    
    # Admin/Warden APIs
    path('admin/requests/', views.AdminRequestListView.as_view(), name='admin_requests'),
    path('admin/requests/<int:request_id>/update/', views.AdminRequestUpdateView.as_view(), name='update_request'),
    path('admin/dashboard/', views.WardenDashboardView.as_view(), name='warden_dashboard'),
    
    # Student info and notifications
    path('student/info/', views.get_student_info, name='student_info'),
    path('student/notifications/', views.StudentNotificationListView.as_view(), name='student_notifications'),
]
