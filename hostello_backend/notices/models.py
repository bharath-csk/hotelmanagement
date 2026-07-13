from django.db import models
from django.contrib.auth import get_user_model
from students.models import Student
from django.utils import timezone

User = get_user_model()

class Notice(models.Model):
    """Notice/Notification Management"""
    AUDIENCE_CHOICES = (
        ('all', 'All Students'),
        ('specific_room', 'Specific Room'),
        ('individual', 'Individual Student'),
    )

    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )

    title = models.CharField(max_length=200)
    message = models.TextField()
    audience = models.CharField(max_length=20, choices=AUDIENCE_CHOICES, default='all')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')

    # Specific targeting
    target_room = models.CharField(max_length=10, blank=True, null=True, help_text="Room number for specific room notices")
    target_student = models.ForeignKey(Student, on_delete=models.CASCADE, blank=True, null=True, help_text="Specific student for individual notices")

    # Timing
    publish_date = models.DateTimeField(default=timezone.now)
    expiry_date = models.DateTimeField(blank=True, null=True, help_text="Notice will be hidden after this date")

    # Status
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_notices')

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-publish_date']
        verbose_name = "Notice"
        verbose_name_plural = "Notices"

    def __str__(self):
        return f"{self.title} - {self.get_audience_display()}"

    def is_expired(self):
        """Check if notice has expired"""
        if self.expiry_date:
            return timezone.now() > self.expiry_date
        return False

    def get_target_display(self):
        """Get human-readable target information"""
        if self.audience == 'all':
            return "All Students"
        elif self.audience == 'specific_room':
            return f"Room {self.target_room}"
        elif self.audience == 'individual':
            return f"{self.target_student.full_name} ({self.target_student.admission_number})"
        return "Unknown"

class NoticeReadStatus(models.Model):
    """Track which students have read which notices"""
    notice = models.ForeignKey(Notice, on_delete=models.CASCADE, related_name='read_status')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='notice_reads')
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['notice', 'student']
        ordering = ['-read_at']
        verbose_name = "Notice Read Status"
        verbose_name_plural = "Notice Read Statuses"

    def __str__(self):
        return f"{self.student.admission_number} read '{self.notice.title}'"

class SystemNotification(models.Model):
    """System-generated notifications (attendance alerts, fee reminders, etc.)"""
    NOTIFICATION_TYPES = (
        ('attendance_absent', 'Attendance Absent'),
        ('fee_reminder', 'Fee Reminder'),
        ('fee_overdue', 'Fee Overdue'),
        ('request_status', 'Request Status Update'),
        ('general', 'General Notification'),
    )

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()

    # Related objects (optional)
    related_object_id = models.PositiveIntegerField(blank=True, null=True)
    related_object_type = models.CharField(max_length=50, blank=True, null=True)  # 'fee', 'attendance', 'request'

    # Status
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "System Notification"
        verbose_name_plural = "System Notifications"

    def __str__(self):
        return f"{self.student.admission_number} - {self.title}"
