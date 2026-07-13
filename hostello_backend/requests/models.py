# requests/models.py - COMPLETELY FIXED VERSION

from django.db import models
from django.conf import settings
from students.models import Student
from django.utils import timezone

class StudentRequest(models.Model):
    REQUEST_TYPES = [
        ('complaint', 'Complaint'),
        ('cleaning', 'Room Cleaning'),
        ('leave', 'Leave Request'),
        ('maintenance', 'Maintenance'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
        ('in_progress', 'In Progress'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    # Basic fields
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='student_requests')
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')

    # Leave request specific fields
    from_date = models.DateField(null=True, blank=True, help_text="For leave requests")
    to_date = models.DateField(null=True, blank=True, help_text="For leave requests")
    leave_reason = models.TextField(blank=True, help_text="For leave requests")
    emergency_contact = models.CharField(max_length=15, blank=True, help_text="Emergency contact for leave")

    # Cleaning request specific fields
    cleaning_type = models.CharField(max_length=50, blank=True, help_text="Type of cleaning")
    preferred_date = models.DateField(null=True, blank=True, help_text="For cleaning requests")
    preferred_time = models.CharField(max_length=20, blank=True, help_text="morning/afternoon/evening")

    # Complaint specific fields
    complaint_category = models.CharField(max_length=50, blank=True, help_text="Category of complaint")
    urgency_level = models.CharField(max_length=20, blank=True, help_text="Urgency level")
    room_number = models.CharField(max_length=10, blank=True, help_text="Room number if applicable")

    # Warden response
    warden_response = models.TextField(blank=True, help_text="Warden's response or notes")
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_requests',
        help_text="Warden who processed this request"
    )
    processed_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Student Request'
        verbose_name_plural = 'Student Requests'
        db_table = 'student_requests'

    def __str__(self):
        return f"{self.get_request_type_display()} - {self.student.full_name} ({self.status})"

    @property
    def is_leave_request(self):
        return self.request_type == 'leave'

    @property
    def is_cleaning_request(self):
        return self.request_type == 'cleaning'

    @property
    def is_complaint(self):
        return self.request_type == 'complaint'

    def can_be_processed(self):
        return self.status == 'pending'

    def approve(self, processed_by, response=""):
        old_status = self.status
        self.status = 'approved'
        self.processed_by = processed_by
        self.warden_response = response
        self.processed_at = timezone.now()
        self.save()
        
        # Create notification
        self.create_notification(f"Your {self.get_request_type_display()} request has been approved.", old_status)

    def reject(self, processed_by, response=""):
        old_status = self.status
        self.status = 'rejected'
        self.processed_by = processed_by
        self.warden_response = response
        self.processed_at = timezone.now()
        self.save()
        
        # Create notification
        self.create_notification(f"Your {self.get_request_type_display()} request has been rejected.", old_status)

    def complete(self, processed_by, response=""):
        old_status = self.status
        self.status = 'completed'
        self.processed_by = processed_by
        self.warden_response = response
        self.processed_at = timezone.now()
        self.save()
        
        # Create notification
        self.create_notification(f"Your {self.get_request_type_display()} request has been completed.", old_status)

    def create_notification(self, message, old_status):
        """Create notification for student when status changes"""
        try:
            notification = RequestNotification.objects.create(
                student=self.student,
                title=f"Request {self.status.title()}",
                message=message,
                request=self,
                notification_type='request_update'
            )
            print(f"✅ Notification created: {notification.id}")
        except Exception as e:
            print(f"❌ Error creating notification: {e}")


class RequestNotification(models.Model):
    """
    RENAMED from StudentNotification to RequestNotification to avoid conflicts
    """
    NOTIFICATION_TYPES = [
        ('request_update', 'Request Update'),
        ('general', 'General'),
        ('urgent', 'Urgent'),
        ('announcement', 'Announcement'),
    ]

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='request_notifications'  # UNIQUE related_name
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='general')
    request = models.ForeignKey(
        StudentRequest,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Request Notification'
        verbose_name_plural = 'Request Notifications'
        db_table = 'request_notifications'

    def __str__(self):
        return f"{self.student.full_name} - {self.title}"

    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()
