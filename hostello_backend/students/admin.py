from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.utils.html import format_html
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.contrib import messages
from django.db import models
from .models import Student, Room
import random
import string

User = get_user_model()

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['admission_number', 'full_name', 'email', 'status', 'room_number', 'created_at', 'action_buttons']
    list_filter = ['status', 'program', 'room_type', 'ac_type', 'gender', 'created_at']
    search_fields = ['admission_number', 'full_name', 'email', 'mobile']
    readonly_fields = ['password', 'created_at', 'updated_at']

    fieldsets = (
        ('Personal Information', {
            'fields': ('admission_number', 'full_name', 'email', 'mobile', 
                      'date_of_birth', 'gender', 'city', 'address')
        }),
        ('Guardian Information', {
            'fields': ('guardian_name', 'guardian_email')
        }),
        ('Academic Information', {
            'fields': ('program', 'discipline')
        }),
        ('Hostel Information', {
            'fields': ('room_type', 'ac_type', 'status', 'room_number')
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['approve_students_bulk', 'reject_students_bulk', 'send_login_details']

    def action_buttons(self, obj):
        """Custom action buttons for each student"""
        if obj.status == 'Pending':
            return format_html(
                '<a class="button" href="{}" style="background: #28a745; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px;">🏠 Assign Room</a>',
                reverse('admin:assign_room', args=[obj.pk])
            )
        elif obj.status == 'Approved':
            return format_html(
                '<span style="color: green; font-weight: bold;">✅ Room: {}</span> '
                '<a href="{}" style="background: #007cba; color: white; padding: 3px 8px; text-decoration: none; border-radius: 3px; font-size: 11px;">📧 Resend Email</a>',
                obj.room_number or 'Not assigned',
                reverse('admin:resend_login_email', args=[obj.pk])
            )
        else:
            return format_html('<span style="color: red; font-weight: bold;">❌ Rejected</span>')

    action_buttons.short_description = 'Actions'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('assign-room/<int:student_id>/', 
                 self.admin_site.admin_view(self.assign_room_view),
                 name='assign_room'),
            path('resend-email/<int:student_id>/', 
                 self.admin_site.admin_view(self.resend_login_email_view),
                 name='resend_login_email'),
        ]
        return custom_urls + urls

    def assign_room_view(self, request, student_id):
        """Custom view for room assignment"""
        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            messages.error(request, 'Student not found.')
            return HttpResponseRedirect(reverse('admin:students_student_changelist'))

        if request.method == 'POST':
            room_number = request.POST.get('room_number')
            if room_number:
                # Assign room and approve student
                student.room_number = room_number
                student.status = 'Approved'
                student.save()

                # Update or create room
                self.update_room_occupancy(room_number, student)

                # Send approval email with login details
                email_sent = self.send_approval_email(student)

                if email_sent:
                    messages.success(request, 
                        f'Room {room_number} assigned to {student.full_name} successfully! '
                        f'Login details sent to {student.email}')
                else:
                    messages.warning(request, 
                        f'Room assigned but email failed to send. Please resend manually.')

                return HttpResponseRedirect(reverse('admin:students_student_changelist'))

        # Get available rooms based on student preferences
        available_rooms = self.get_available_rooms(student)

        context = {
            'student': student,
            'available_rooms': available_rooms,
            'title': f'Assign Room to {student.full_name}',
        }

        return render(request, 'admin/assign_room.html', context)

    def resend_login_email_view(self, request, student_id):
        """Resend login email to student"""
        try:
            student = Student.objects.get(id=student_id)
            if student.status == 'Approved':
                email_sent = self.send_approval_email(student)
                if email_sent:
                    messages.success(request, f'Login details sent to {student.email} successfully!')
                else:
                    messages.error(request, 'Failed to send email. Please check email settings.')
            else:
                messages.warning(request, 'Student must be approved first.')
        except Student.DoesNotExist:
            messages.error(request, 'Student not found.')

        return HttpResponseRedirect(reverse('admin:students_student_changelist'))

    def get_available_rooms(self, student):
        """Get available rooms matching student preferences"""
        # Try to find rooms matching student preferences
        rooms = Room.objects.filter(
            room_type=student.room_type,
            ac_type=student.ac_type,
            is_available=True
        ).annotate(
            available_spots=models.F('capacity') - models.F('occupied')
        ).filter(available_spots__gt=0)

        # If no exact match, suggest any available rooms
        if not rooms.exists():
            rooms = Room.objects.filter(
                is_available=True
            ).annotate(
                available_spots=models.F('capacity') - models.F('occupied')
            ).filter(available_spots__gt=0)

        return rooms[:10]

    def update_room_occupancy(self, room_number, student):
        """Update or create room and manage occupancy"""
        room, created = Room.objects.get_or_create(
            room_number=room_number,
            defaults={
                'room_type': student.room_type,
                'ac_type': student.ac_type,
                'capacity': self.get_room_capacity(student.room_type),
                'occupied': 1,
                'is_available': True
            }
        )

        if not created:
            room.occupied += 1
            if room.occupied >= room.capacity:
                room.is_available = False
            room.save()

    def get_room_capacity(self, room_type):
        """Get capacity based on room type"""
        capacity_map = {
            '1 Seater': 1,
            '2 Seater': 2,
            '3 Seater': 3,
            '4 Seater': 4,
        }
        return capacity_map.get(room_type, 1)

    def send_approval_email(self, student):
        """Send comprehensive approval email with all details"""
        try:
            # Email subject
            subject = "🏠 HOSTELLO - Room Assigned! Your Complete Login Details"

            # Get current site URL (configure in settings.py)
            login_url = getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000') + '/login/'
            dashboard_url = getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000') + '/dashboard/'

            # Comprehensive email content
            message = f"""
Dear {student.full_name},

🎉 CONGRATULATIONS! Your hostel application has been APPROVED!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏠 ROOM ASSIGNMENT DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏷️  Room Number: {student.room_number}
🛏️  Room Type: {student.room_type}
❄️  AC Type: {student.ac_type}
🏢  Hostel: HOSTELLO Main Block

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔐 YOUR LOGIN CREDENTIALS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👤 Username: {student.admission_number}
🔑 Password: [Use the password you set during registration]
🌐 Login URL: {login_url}
📱 Dashboard: {dashboard_url}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 STUDENT INFORMATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 Admission Number: {student.admission_number}
📧 Email: {student.email}
📱 Mobile: {student.mobile}
🎓 Program: {student.program}
📚 Discipline: {student.discipline}
🏙️ City: {student.city}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👨‍👩‍👧‍👦 GUARDIAN INFORMATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👤 Guardian Name: {student.guardian_name}
📧 Guardian Email: {student.guardian_email}
🏠 Address: {student.address}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 NEXT STEPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 🌐 Visit: {login_url}
2. 👤 Enter your Admission Number: {student.admission_number}
3. 🔑 Enter your registration password
4. 📊 Access your dashboard and room details
5. 🏢 Report to hostel office for key collection

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📞 CONTACT INFORMATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📧 Email: hostel@hostello.com
📱 Phone: +91 9876543210
🏢 Office: HOSTELLO Administration Office
⏰ Office Hours: 9:00 AM - 6:00 PM

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ IMPORTANT NOTES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• Keep your login credentials secure
• If you forgot your password, contact the warden
• Room keys will be provided at the hostel office
• Follow all hostel rules and regulations

🏠 Welcome to HOSTELLO Family!

Best regards,
Hostel Warden
HOSTELLO Management Team

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This is an automated email. Please do not reply directly.
For queries, contact: hostel@hostello.com
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            """

            # Send email to both student and guardian
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [student.email, student.guardian_email],
                fail_silently=False,
            )

            return True

        except Exception as e:
            print(f"❌ Error sending email to {student.email}: {str(e)}")
            return False

    def approve_students_bulk(self, request, queryset):
        """Bulk approve students without room assignment"""
        approved_count = 0
        for student in queryset.filter(status='Pending'):
            student.status = 'Approved'
            student.save()
            approved_count += 1

        self.message_user(request, f'✅ Approved {approved_count} students. Remember to assign rooms!')

    approve_students_bulk.short_description = "✅ Approve selected students"

    def reject_students_bulk(self, request, queryset):
        """Bulk reject students"""
        rejected_count = queryset.filter(status='Pending').update(status='Rejected')
        self.message_user(request, f'❌ Rejected {rejected_count} students.')

    reject_students_bulk.short_description = "❌ Reject selected students"

    def send_login_details(self, request, queryset):
        """Send login details to approved students"""
        sent_count = 0
        for student in queryset.filter(status='Approved'):
            if self.send_approval_email(student):
                sent_count += 1

        self.message_user(request, f'📧 Sent login details to {sent_count} students.')

    send_login_details.short_description = "📧 Send login details"

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['room_number', 'room_type', 'ac_type', 'capacity', 'occupied', 'available_spots', 'is_available']
    list_filter = ['room_type', 'ac_type', 'is_available']
    search_fields = ['room_number']
    list_editable = ['capacity', 'occupied', 'is_available']

    def available_spots(self, obj):
        spots = max(0, obj.capacity - obj.occupied)
        if spots > 0:
            return format_html('<span style="color: green; font-weight: bold;">{}</span>', spots)
        else:
            return format_html('<span style="color: red; font-weight: bold;">Full</span>')
    available_spots.short_description = 'Available'

# Customize admin site
admin.site.site_header = "HOSTELLO Administration"
admin.site.site_title = "HOSTELLO Admin"
admin.site.index_title = "Hostel Management System"