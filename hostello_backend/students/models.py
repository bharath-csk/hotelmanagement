from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Student(models.Model):
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]

    ROOM_CHOICES = [
        ('1 Seater', '1 Seater'),
        ('2 Seater', '2 Seater'),
        ('3 Seater', '3 Seater'),
        ('4 Seater', '4 Seater'),
    ]

    AC_CHOICES = [
        ('AC', 'AC'),
        ('Non-AC', 'Non-AC'),
    ]

    PROGRAM_CHOICES = [
        ('BTech', 'B.Tech'),
        ('MTech', 'M.Tech'),
        ('BSc', 'B.Sc'),
        ('MSc', 'M.Sc'),
        ('MBA', 'MBA'),
    ]

    DISCIPLINE_CHOICES = [
        ('Computer Science', 'Computer Science'),
        ('Electronics', 'Electronics'),
        ('Mechanical', 'Mechanical'),
        ('Civil', 'Civil'),
        ('Chemical', 'Chemical'),
        ('Others', 'Others'),
    ]

    STATUS_CHOICES = [
        ('Pending', 'Pending Approval'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    # Personal Information
    admission_number = models.CharField(max_length=50, unique=True)
    full_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    mobile = models.CharField(max_length=15)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    city = models.CharField(max_length=50)
    address = models.TextField()

    # Guardian Information
    guardian_name = models.CharField(max_length=100)
    guardian_email = models.EmailField()

    # Academic Information
    program = models.CharField(max_length=20, choices=PROGRAM_CHOICES)
    discipline = models.CharField(max_length=50, choices=DISCIPLINE_CHOICES)

    # Hostel Information
    room_type = models.CharField(max_length=20, choices=ROOM_CHOICES)
    ac_type = models.CharField(max_length=10, choices=AC_CHOICES)

    # Status and Assignment
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    room_number = models.CharField(max_length=20, blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.admission_number} - {self.full_name}"

    class Meta:
        ordering = ['-created_at']
        
        

class Room(models.Model):
    room_number = models.CharField(max_length=20, unique=True)
    room_type = models.CharField(max_length=20, choices=Student.ROOM_CHOICES, default='1 Seater')
    ac_type = models.CharField(max_length=10, choices=Student.AC_CHOICES, default='Non-AC')  # ← Add default
    capacity = models.IntegerField(default=1)
    occupied = models.IntegerField(default=0)
    is_available = models.BooleanField(default=True)


    def __str__(self):
        return f"Room {self.room_number} - {self.room_type} ({self.ac_type})"

@property
def available_spots(self):
    return max(0, self.capacity - self.occupied)

class Meta:
    ordering = ['room_number']

