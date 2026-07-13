from django.contrib import admin
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.html import format_html
from students.models import Student
from .models import Notice, NoticeReadStatus, SystemNotification

User = get_user_model()

@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ['title', 'audience', 'target_display', 'priority', 'publish_date', 'expiry_date', 'is_active', 'created_by']
    list_filter = ['audience', 'priority', 'is_active', 'publish_date', 'created_by']
    search_fields = ['title', 'message', 'target_room', 'target_student__full_name']
    date_hierarchy = 'publish_date'

    fieldsets = (
        ('Notice Content', {
            'fields': ('title', 'message', 'priority')
        }),
        ('Target Audience', {
            'fields': ('audience', 'target_room', 'target_student'),
            'description': 'Select audience type and specify target if needed'
        }),
        ('Timing', {
            'fields': ('publish_date', 'expiry_date', 'is_active')
        }),
        ('System Information', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'updated_at']

    actions = ['activate_notices', 'deactivate_notices', 'extend_expiry']

    def target_display(self, obj):
        """Display target information"""
        return obj.get_target_display()
    target_display.short_description = 'Target'

    def save_model(self, request, obj, form, change):
        """Set created_by to current user"""
        if not change:  # Only set on creation
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def activate_notices(self, request, queryset):
        """Activate selected notices"""
        count = queryset.update(is_active=True)
        self.message_user(request, f"Activated {count} notices.")

    activate_notices.short_description = "Activate selected notices"

    def deactivate_notices(self, request, queryset):
        """Deactivate selected notices"""
        count = queryset.update(is_active=False)
        self.message_user(request, f"Deactivated {count} notices.")

    deactivate_notices.short_description = "Deactivate selected notices"

    def extend_expiry(self, request, queryset):
        """Extend expiry date by 7 days"""
        updated_count = 0
        for notice in queryset:
            if notice.expiry_date:
                notice.expiry_date = notice.expiry_date + timezone.timedelta(days=7)
            else:
                notice.expiry_date = timezone.now() + timezone.timedelta(days=7)
            notice.save()
            updated_count += 1

        self.message_user(request, f"Extended expiry for {updated_count} notices by 7 days.")

    extend_expiry.short_description = "Extend expiry by 7 days"

    def get_queryset(self, request):
        """Optimize queryset with related objects"""
        return super().get_queryset(request).select_related('created_by', 'target_student')

@admin.register(NoticeReadStatus)
class NoticeReadStatusAdmin(admin.ModelAdmin):
    list_display = ['notice', 'student', 'read_at']
    list_filter = ['read_at', 'notice__audience', 'notice__priority']
    search_fields = ['notice__title', 'student__admission_number', 'student__full_name']
    date_hierarchy = 'read_at'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('notice', 'student')

@admin.register(SystemNotification)
class SystemNotificationAdmin(admin.ModelAdmin):
    list_display = ['student', 'notification_type', 'title', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['student__admission_number', 'student__full_name', 'title', 'message']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at']

    actions = ['mark_as_read', 'mark_as_unread']

    def mark_as_read(self, request, queryset):
        """Mark notifications as read"""
        count = queryset.update(is_read=True)
        self.message_user(request, f"Marked {count} notifications as read.")

    mark_as_read.short_description = "Mark as read"

    def mark_as_unread(self, request, queryset):
        """Mark notifications as unread"""
        count = queryset.update(is_read=False)
        self.message_user(request, f"Marked {count} notifications as unread.")

    mark_as_unread.short_description = "Mark as unread"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('student')

# Create utility functions for generating system notifications
def create_attendance_notification(student, date, attendance_type='room'):
    """Create attendance absence notification"""
    title = f"Attendance Alert - {date.strftime('%d/%m/%Y')}"
    message = f"You were marked absent for {attendance_type} attendance on {date.strftime('%d/%m/%Y')}. If this is incorrect, please contact the warden."

    SystemNotification.objects.create(
        student=student,
        notification_type='attendance_absent',
        title=title,
        message=message
    )

def create_fee_reminder_notification(student, fee):
    """Create fee reminder notification"""
    title = f"Fee Payment Reminder - {fee.month.strftime('%B %Y')}"
    message = f"Your fee payment of ₹{fee.get_pending_amount()} is due on {fee.due_date.strftime('%d/%m/%Y')}. Please pay as soon as possible."

    SystemNotification.objects.create(
        student=student,
        notification_type='fee_reminder',
        title=title,
        message=message,
        related_object_id=fee.id,
        related_object_type='fee'
    )

def create_request_status_notification(student, request_obj):
    """Create request status update notification"""
    title = f"{request_obj.get_request_type_display()} Request {request_obj.get_status_display()}"
    message = f"Your {request_obj.get_request_type_display()} request '{request_obj.title}' has been {request_obj.get_status_display().lower()}."

    if request_obj.admin_response:
        message += f"\n\nAdmin Response: {request_obj.admin_response}"

    SystemNotification.objects.create(
        student=student,
        notification_type='request_status',
        title=title,
        message=message,
        related_object_id=request_obj.id,
        related_object_type='request'
    )
