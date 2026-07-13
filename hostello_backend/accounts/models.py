from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """Custom User Model for HOSTELLO"""
    USER_TYPES = (
        ('warden', 'Warden'),
        ('student', 'Student'),
    )

    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='student')
    phone_number = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"

class WardenProfile(models.Model):
    """Warden Profile - Single warden for the hostel"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='warden_profile')
    designation = models.CharField(max_length=100, default='Hostel Warden')
    department = models.CharField(max_length=100, blank=True, null=True)
    photo = models.ImageField(upload_to='warden_photos/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Warden: {self.user.get_full_name() or self.user.username}"

    class Meta:
        verbose_name = "Warden Profile"
        verbose_name_plural = "Warden Profiles"
