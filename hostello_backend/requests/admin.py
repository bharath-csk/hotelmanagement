
# requests/admin.py - REQUEST MANAGEMENT LIKE ATTENDANCE DESIGN

from django.contrib import admin
from django.contrib import messages
from django.utils.html import format_html
from django.utils import timezone
from django.db import models
from django import forms
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import path, reverse
from django.db.models import Q, Count
from datetime import datetime, date
from .models import StudentRequest

class RequestManagementAdmin(admin.ModelAdmin):
    """Main request management interface - Like Attendance Design"""
    change_list_template = 'admin/request_management.html'

    def changelist_view(self, request, extra_context=None):
        # Get selected date (default to today)
        selected_date = request.GET.get('date', timezone.now().date().isoformat())
        try:
            selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
        except:
            selected_date = timezone.now().date()

        # Get all student requests
        requests_queryset = StudentRequest.objects.all().order_by('-created_at').select_related('student', 'processed_by')

        # Filter by date if specified
        if selected_date:
            requests_queryset = requests_queryset.filter(created_at__date=selected_date)

        # Prepare request data with status info
        request_data = []
        for req in requests_queryset:
            request_info = {
                'request': req,
                'can_update': req.status == 'pending',  # Only pending requests can be updated
                'time_since_creation': (timezone.now() - req.created_at).days,
                'type_icon': self.get_type_icon(req.request_type),
                'priority_color': self.get_priority_color(req.priority),
                'status_color': self.get_status_color(req.status),
            }
            request_data.append(request_info)

        # Get request statistics
        total_requests = requests_queryset.count()
        pending_requests = requests_queryset.filter(status='pending').count()
        approved_requests = requests_queryset.filter(status='approved').count()
        rejected_requests = requests_queryset.filter(status='rejected').count()
        completed_requests = requests_queryset.filter(status='completed').count()

        extra_context = extra_context or {}
        extra_context.update({
            'request_data': request_data,
            'selected_date': selected_date,
            'total_requests': total_requests,
            'pending_requests': pending_requests,
            'approved_requests': approved_requests,
            'rejected_requests': rejected_requests,
            'completed_requests': completed_requests,
            'title': 'Student Request Management',
        })

        return super().changelist_view(request, extra_context=extra_context)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('update-status/', self.admin_site.admin_view(self.update_status_view), 
                 name='update_request_status'),
            path('bulk-status/', self.admin_site.admin_view(self.bulk_status_view), 
                 name='bulk_request_status'),
        ]
        return custom_urls + urls

    def update_status_view(self, request):
        """Handle individual request status update via AJAX"""
        if request.method == 'POST':
            request_id = request.POST.get('request_id')
            new_status = request.POST.get('status')
            warden_response = request.POST.get('warden_response', '')

            try:
                student_request = StudentRequest.objects.get(id=request_id)
                old_status = student_request.status

                # Update status
                student_request.status = new_status
                student_request.processed_by = request.user
                student_request.processed_at = timezone.now()

                if warden_response:
                    student_request.warden_response = warden_response

                student_request.save()

                # Send notification to student
                self.send_status_notification(student_request, old_status, new_status, request.user)

                return JsonResponse({
                    'success': True, 
                    'message': f'Request #{request_id} status updated to {new_status.upper()}!'
                })

            except StudentRequest.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Request not found'})
            except Exception as e:
                return JsonResponse({'success': False, 'message': str(e)})

        return JsonResponse({'success': False, 'message': 'Invalid request method'})

    def bulk_status_view(self, request):
        """Handle bulk status updates"""
        if request.method == 'POST':
            action = request.POST.get('action')
            selected_date = request.POST.get('date')

            try:
                if selected_date:
                    date_obj = datetime.strptime(selected_date, '%Y-%m-%d').date()
                    requests = StudentRequest.objects.filter(
                        created_at__date=date_obj, 
                        status='pending'
                    )
                else:
                    requests = StudentRequest.objects.filter(status='pending')

                count = 0
                for req in requests:
                    old_status = req.status

                    if action == 'approve_all':
                        req.status = 'approved'
                    elif action == 'reject_all':
                        req.status = 'rejected'
                    elif action == 'complete_all':
                        req.status = 'completed'

                    req.processed_by = request.user
                    req.processed_at = timezone.now()
                    req.save()

                    # Send notification
                    self.send_status_notification(req, old_status, req.status, request.user)
                    count += 1

                messages.success(request, f'✅ {count} requests updated successfully!')
                return redirect(request.META.get('HTTP_REFERER', '/admin/'))

            except Exception as e:
                messages.error(request, f'❌ Error: {str(e)}')
                return redirect(request.META.get('HTTP_REFERER', '/admin/'))

        return redirect('/admin/')

    def send_status_notification(self, student_request, old_status, new_status, processed_by):
        """Send notification to student when status changes"""
        try:
            status_messages = {
                'approved': f'✅ Your {student_request.get_request_type_display()} request "{student_request.title}" has been APPROVED by the warden.',
                'rejected': f'❌ Your {student_request.get_request_type_display()} request "{student_request.title}" has been REJECTED by the warden.',
                'completed': f'🎉 Your {student_request.get_request_type_display()} request "{student_request.title}" has been COMPLETED successfully.',
                'in_progress': f'🔄 Your {student_request.get_request_type_display()} request "{student_request.title}" is now IN PROGRESS.'
            }

            message = status_messages.get(new_status, f'Status updated to {new_status.upper()}')
            print(f"📧 NOTIFICATION: {message} (Request ID: {student_request.id})")

            # Here you would save to notification table or send actual notification
            # Example: Notification.objects.create(student=student_request.student, message=message)

        except Exception as e:
            print(f"❌ Notification error: {e}")

    def get_type_icon(self, request_type):
        """Get icon for request type"""
        icons = {
            'complaint': '❌',
            'cleaning': '🧹', 
            'leave': '📝',
            'maintenance': '🛠',
            'other': '📋'
        }
        return icons.get(request_type, '📋')

    def get_priority_color(self, priority):
        """Get color for priority"""
        colors = {
            'urgent': '#dc3545',
            'high': '#fd7e14',
            'medium': '#ffc107',
            'low': '#28a745'
        }
        return colors.get(priority, '#6c757d')

    def get_status_color(self, status):
        """Get color for status"""
        colors = {
            'pending': '#ffc107',
            'approved': '#28a745',
            'rejected': '#dc3545', 
            'completed': '#17a2b8',
            'in_progress': '#6610f2'
        }
        return colors.get(status, '#6c757d')

# Register the request management
from django.apps import apps

# Get the model dynamically to avoid circular imports
try:
    StudentRequest = apps.get_model('requests', 'StudentRequest')
    admin.site.register(StudentRequest, RequestManagementAdmin)
except:
    # Fallback registration
    pass

# Customize admin site
admin.site.site_header = "HOSTELLO Request Management"
admin.site.site_title = "HOSTELLO Admin"
admin.site.index_title = "Student Request Management System"
