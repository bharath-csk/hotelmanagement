# attendance/models.py - FIXED AUTH_USER_MODEL

from django.db import models
from django.utils import timezone
from django.conf import settings
from students.models import Student

class RoomAttendance(models.Model):
    ATTENDANCE_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='room_attendance')
    date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=10, choices=ATTENDANCE_CHOICES, default='present')
    marked_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    marked_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ['student', 'date']
        ordering = ['-date']
        verbose_name = 'Room Attendance'
        verbose_name_plural = 'Room Attendance Records'

    def __str__(self):
        return f"{self.student.full_name} - {self.date} - {self.status}"

class MessAttendance(models.Model):
    ATTENDANCE_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
    ]

    MEAL_CHOICES = [
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'), 
        ('dinner', 'Dinner'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='mess_attendance')
    date = models.DateField(default=timezone.now)
    meal_type = models.CharField(max_length=10, choices=MEAL_CHOICES, default='lunch')
    status = models.CharField(max_length=10, choices=ATTENDANCE_CHOICES, default='present')
    marked_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    marked_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['student', 'date', 'meal_type']
        ordering = ['-date', 'meal_type']
        verbose_name = 'Mess Attendance'
        verbose_name_plural = 'Mess Attendance Records'

    def __str__(self):
        return f"{self.student.full_name} - {self.date} - {self.meal_type} - {self.status}"

class AttendanceNotification(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_notifications')
    attendance_type = models.CharField(max_length=10, choices=[('room', 'Room'), ('mess', 'Mess')])
    date = models.DateField()
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    email_sent = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Attendance Notification'
        verbose_name_plural = 'Attendance Notifications'

    def __str__(self):
        return f"{self.student.full_name} - {self.attendance_type} - {self.date}"

class AttendanceStats(models.Model):
    """Model to store attendance statistics for quick access"""
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='attendance_stats')
    room_present_count = models.IntegerField(default=0)
    room_absent_count = models.IntegerField(default=0)
    mess_present_count = models.IntegerField(default=0)
    mess_absent_count = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Attendance Statistics'
        verbose_name_plural = 'Attendance Statistics'

    def __str__(self):
        return f"{self.student.full_name} - Stats"

    def total_days(self):
        return self.room_present_count + self.room_absent_count

    def room_attendance_percentage(self):
        total = self.total_days()
        if total == 0:
            return 0
        return round((self.room_present_count / total) * 100, 2)
    
    def mess_attendance_percentage(self):
        total = self.total_days()
        if total == 0:
            return 0
        return round((self.mess_present_count / total) * 100, 2)

    def update_stats(self):
        """Update attendance statistics"""
        self.room_present_count = RoomAttendance.objects.filter(student=self.student, status='present').count()
        self.room_absent_count = RoomAttendance.objects.filter(student=self.student, status='absent').count()
        self.mess_present_count = MessAttendance.objects.filter(student=self.student, status='present').count()
        self.mess_absent_count = MessAttendance.objects.filter(student=self.student, status='absent').count()
        self.save()