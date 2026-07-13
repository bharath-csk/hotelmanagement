# attendance/admin.py - COMPLETE VERSION WITH EMAIL NOTIFICATIONS

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.utils.html import format_html
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import path, reverse
from django.contrib import messages
from django.db.models import Q, Count
from students.models import Student
from .models import RoomAttendance, MessAttendance, AttendanceNotification, AttendanceStats
import datetime
from django.utils.dateparse import parse_date

User = get_user_model()


class AttendanceManagementAdmin(admin.ModelAdmin):
    """Enhanced attendance management interface with email notifications"""
    change_list_template = 'admin/attendance_management.html'

    def changelist_view(self, request, extra_context=None):
        print("🔍 DEBUG: changelist_view called")
        print(f"🔍 DEBUG: request.GET = {request.GET}")
        
        # Get all approved students
        students = Student.objects.filter(status='Approved').order_by('room_number', 'full_name')

        # Date parameter handling
        selected_date = None
        selected_date_str = request.GET.get('date', '')
        
        print(f"🔍 DEBUG: Raw date parameter = '{selected_date_str}'")
        
        if selected_date_str:
            try:
                selected_date = datetime.datetime.strptime(selected_date_str, '%Y-%m-%d').date()
                print(f"✅ DEBUG: Successfully parsed date = {selected_date}")
            except ValueError as e:
                print(f"❌ DEBUG: Date parsing failed: {e}")
                selected_date = timezone.now().date()
                messages.warning(request, f"Invalid date format '{selected_date_str}'. Using today's date.")
        else:
            selected_date = timezone.now().date()
            print(f"📅 DEBUG: No date parameter, using today = {selected_date}")

        print(f"🎯 DEBUG: FINAL selected_date = {selected_date}")

        # Prepare student data with attendance for selected date
        student_data = []
        mess_present_count = 0
        mess_absent_count = 0
        
        print(f"🔍 DEBUG: Querying attendance for date: {selected_date}")
        
        for student in students:
            # Get room attendance for selected date
            room_attendance = RoomAttendance.objects.filter(
                student=student, 
                date=selected_date
            ).first()
            
            print(f"🔍 DEBUG: Student {student.full_name} - Room attendance: {room_attendance}")

            # Get mess attendance for selected date
            mess_breakfast = MessAttendance.objects.filter(
                student=student, 
                date=selected_date,
                meal_type='breakfast'
            ).first()
            
            mess_lunch = MessAttendance.objects.filter(
                student=student, 
                date=selected_date,
                meal_type='lunch'
            ).first()
            
            mess_dinner = MessAttendance.objects.filter(
                student=student, 
                date=selected_date,
                meal_type='dinner'
            ).first()

            # Calculate mess overall status
            mess_status = self.calculate_mess_status_new_logic(mess_breakfast, mess_lunch, mess_dinner)
            
            # Count for statistics
            if mess_status == 'present':
                mess_present_count += 1
            elif mess_status == 'absent':
                mess_absent_count += 1
                
            # Per-date mess counters
            if mess_status == 'present':
                per_date_present = 1
                per_date_absent = 0
            elif mess_status == 'absent':
                per_date_present = 0
                per_date_absent = 1
            else:
                per_date_present = 0
                per_date_absent = 0

            per_date_total = per_date_present + per_date_absent
            per_date_rate = round((per_date_present / per_date_total) * 100, 2) if per_date_total else 0

            # Get or create attendance stats
            stats, created = AttendanceStats.objects.get_or_create(student=student)
            if created:
                stats.update_stats()

            student_info = {
                'student': student,
                'room_attendance': room_attendance,
                'mess_breakfast': mess_breakfast,
                'mess_lunch': mess_lunch,
                'mess_dinner': mess_dinner,
                'mess_status': mess_status,
                'stats': stats,
                'mess_present_days': per_date_present,
                'mess_absent_days': per_date_absent,
                'mess_total_days': per_date_total,
                'mess_attendance_rate': per_date_rate,
            }
            student_data.append(student_info)

        # Get attendance summary for the selected date
        total_students = students.count()
        room_present = RoomAttendance.objects.filter(
            date=selected_date,
            status='present'
        ).count()
        room_absent = RoomAttendance.objects.filter(
            date=selected_date,
            status='absent'
        ).count()
        room_not_marked = total_students - room_present - room_absent
        
        print(f"📊 DEBUG: Statistics for {selected_date}:")
        print(f"   Room Present: {room_present}")
        print(f"   Room Absent: {room_absent}")
        print(f"   Room Not Marked: {room_not_marked}")
        
        # Mess statistics
        mess_not_marked = total_students - mess_present_count - mess_absent_count

        # Add comprehensive date information
        today = timezone.now().date()
        date_info = {
            'selected_date_str': selected_date_str,
            'parsed_date': selected_date,
            'is_today': selected_date == today,
            'is_future': selected_date > today,
            'is_past': selected_date < today,
            'formatted_date': selected_date.strftime('%Y-%m-%d'),
        }

        print(f"📋 DEBUG: Date info = {date_info}")

        extra_context = extra_context or {}
        extra_context.update({
            'student_data': student_data,
            'selected_date': selected_date,
            'date_info': date_info,
            'total_students': total_students,
            'room_present': room_present,
            'room_absent': room_absent,
            'room_not_marked': room_not_marked,
            'mess_present': mess_present_count,
            'mess_absent': mess_absent_count,
            'mess_not_marked': mess_not_marked,
            'title': 'Enhanced Student Attendance Management',
            'debug_info': {
                'raw_date_param': selected_date_str,
                'parsed_date': selected_date,
                'query_count': len(student_data),
            }
        })

        print(f"✅ DEBUG: Context prepared with selected_date = {selected_date}")
        return super().changelist_view(request, extra_context=extra_context)

    def calculate_mess_status_new_logic(self, breakfast, lunch, dinner):
        """Calculate overall mess status based on individual meals"""
        breakfast_status = breakfast.status if breakfast else None
        lunch_status = lunch.status if lunch else None
        dinner_status = dinner.status if dinner else None
        
        present_meals = 0
        absent_meals = 0
        marked_meals = 0
        
        for status in [breakfast_status, lunch_status, dinner_status]:
            if status is not None:
                marked_meals += 1
                if status == 'present':
                    present_meals += 1
                elif status == 'absent':
                    absent_meals += 1
        
        # Present if ANY meal present
        if present_meals > 0:
            return 'present'
        elif marked_meals > 0 and absent_meals == marked_meals:
            return 'absent'
        else:
            return 'not_marked'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('mark-attendance/', self.admin_site.admin_view(self.mark_attendance_view), 
                 name='mark_attendance'),
            path('bulk-attendance/', self.admin_site.admin_view(self.bulk_attendance_view), 
                 name='bulk_attendance'),
        ]
        return custom_urls + urls

    def mark_attendance_view(self, request):
        """Enhanced attendance marking with email notifications"""
        if request.method == 'POST':
            student_id = request.POST.get('student_id')
            attendance_type = request.POST.get('attendance_type')
            status = request.POST.get('status')
            date_str = request.POST.get('date')
            meal_type = request.POST.get('meal_type', 'lunch')

            print(f"🔍 DEBUG: mark_attendance_view called with date_str = '{date_str}'")

            try:
                student = Student.objects.get(id=student_id)
                
                # Parse date
                try:
                    attendance_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
                    print(f"✅ DEBUG: Parsed attendance_date = {attendance_date}")
                except (ValueError, TypeError) as e:
                    print(f"❌ DEBUG: Date parsing error: {e}")
                    return JsonResponse({
                        'success': False, 
                        'message': f'Invalid date format: {date_str}'
                    })

                # Validate date (not future date)
                if attendance_date > timezone.now().date():
                    return JsonResponse({
                        'success': False, 
                        'message': 'Cannot mark attendance for future dates'
                    })

                print(f"📅 DEBUG: Marking attendance for {student.full_name} on {attendance_date}")

                if attendance_type == 'room':
                    # Update or create room attendance
                    if status:  # If marking present/absent
                        attendance, created = RoomAttendance.objects.get_or_create(
                            student=student,
                            date=attendance_date,
                            defaults={
                                'status': status,
                                'marked_by': request.user
                            }
                        )
                        if not created:
                            attendance.status = status
                            attendance.marked_by = request.user
                            attendance.marked_at = timezone.now()
                            attendance.save()

                        # Send notification if marked absent
                        if status == 'absent':
                            self.send_absence_notification(student, 'room', attendance_date, request.user)

                    else:  # If resetting to "Not Marked"
                        RoomAttendance.objects.filter(
                            student=student,
                            date=attendance_date
                        ).delete()

                    print(f"✅ DEBUG: Room attendance updated")

                    # Update attendance stats
                    stats, created = AttendanceStats.objects.get_or_create(student=student)
                    stats.update_stats()

                    return JsonResponse({
                        'success': True, 
                        'message': f'Room attendance updated for {student.full_name}!',
                        'student_name': student.full_name,
                        'status': status or 'not-marked',
                        'marked_by': request.user.username,
                        'marked_at': timezone.now().strftime('%H:%M')
                    })

                elif attendance_type == 'mess':
                    # Update or create mess attendance
                    if status:  # If marking present/absent
                        attendance, created = MessAttendance.objects.get_or_create(
                            student=student,
                            date=attendance_date,
                            meal_type=meal_type,
                            defaults={
                                'status': status,
                                'marked_by': request.user
                            }
                        )
                        if not created:
                            attendance.status = status
                            attendance.marked_by = request.user
                            attendance.marked_at = timezone.now()
                            attendance.save()

                        # Send notification if marked absent for main meals
                        if status == 'absent' and meal_type in ['lunch', 'dinner']:
                            self.send_mess_absence_notification(student, meal_type, attendance_date)

                    else:  # If resetting to "Not Marked"
                        MessAttendance.objects.filter(
                            student=student,
                            date=attendance_date,
                            meal_type=meal_type
                        ).delete()

                    print(f"✅ DEBUG: Mess attendance updated")

                    # Calculate mess status
                    mess_records = MessAttendance.objects.filter(
                        student=student,
                        date=attendance_date
                    )
                    
                    if mess_records.exists():
                        if mess_records.filter(status='present').exists():
                            mess_status = 'present'
                        else:
                            mess_status = 'absent'
                    else:
                        mess_status = 'not-marked'

                    # Update attendance stats
                    stats, created = AttendanceStats.objects.get_or_create(student=student)
                    stats.update_stats()
                    
                    return JsonResponse({
                        'success': True, 
                        'message': f'Mess attendance updated for {student.full_name}!',
                        'student_name': student.full_name,
                        'status': status or 'not-marked',
                        'meal_type': meal_type,
                        'mess_status': mess_status,
                        'marked_by': request.user.username,
                        'marked_at': timezone.now().strftime('%H:%M')
                    })

            except Student.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Student not found'})
            except Exception as e:
                print(f"❌ ERROR in mark_attendance_view: {str(e)}")
                return JsonResponse({'success': False, 'message': str(e)})

        return JsonResponse({'success': False, 'message': 'Invalid request method'})

    def bulk_attendance_view(self, request):
        """Handle bulk attendance marking"""
        if request.method == 'POST':
            date_str = request.POST.get('date')
            attendance_type = request.POST.get('attendance_type')
            action = request.POST.get('action')

            print(f"🔍 DEBUG: bulk_attendance_view called with date_str = '{date_str}'")

            try:
                # Parse date
                try:
                    attendance_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
                    print(f"✅ DEBUG: Parsed bulk attendance_date = {attendance_date}")
                except (ValueError, TypeError) as e:
                    print(f"❌ DEBUG: Bulk date parsing error: {e}")
                    messages.error(request, f'Invalid date format: {date_str}')
                    return redirect(request.META.get('HTTP_REFERER', '/admin/'))

                students = Student.objects.filter(status='Approved')

                count = 0
                for student in students:
                    if attendance_type == 'room':
                        status = 'present' if action == 'mark_all_present' else 'absent'

                        attendance, created = RoomAttendance.objects.get_or_create(
                            student=student,
                            date=attendance_date,
                            defaults={
                                'status': status,
                                'marked_by': request.user
                            }
                        )
                        if not created:
                            attendance.status = status
                            attendance.marked_by = request.user
                            attendance.marked_at = timezone.now()
                            attendance.save()

                        if status == 'absent':
                            self.send_absence_notification(student, 'room', attendance_date, request.user)

                        # Update stats
                        stats, created = AttendanceStats.objects.get_or_create(student=student)
                        stats.update_stats()

                        count += 1

                messages.success(request, f'Bulk attendance updated for {count} students on {attendance_date}')
                return redirect(request.META.get('HTTP_REFERER', '/admin/'))

            except Exception as e:
                print(f"❌ ERROR in bulk_attendance_view: {str(e)}")
                messages.error(request, f'Error: {str(e)}')
                return redirect(request.META.get('HTTP_REFERER', '/admin/'))

        return redirect('/admin/')

    def send_absence_notification(self, student, attendance_type, date, marked_by):
        """Send absence notification with email"""
        try:
            message = f"You were marked absent for room attendance on {date.strftime('%d/%m/%Y')}. If this is incorrect, please contact the warden."

            notification, created = AttendanceNotification.objects.get_or_create(
                student=student,
                attendance_type=attendance_type,
                date=date,
                defaults={'message': message}
            )

            if created:
                self.send_absence_email(student, date, marked_by)
                notification.email_sent = True
                notification.save()

        except Exception as e:
            print(f"Error sending absence notification: {str(e)}")

    def send_mess_absence_notification(self, student, meal_type, date):
        """Send mess absence notification with email"""
        try:
            message = f"You were marked absent for {meal_type} on {date.strftime('%d/%m/%Y')}."

            notification, created = AttendanceNotification.objects.get_or_create(
                student=student,
                attendance_type='mess',
                date=date,
                defaults={'message': message}
            )

            # Send email notification
            if created:
                self.send_mess_absence_email(student, meal_type, date)
                notification.email_sent = True
                notification.save()

        except Exception as e:
            print(f"Error sending mess notification: {str(e)}")

    def send_absence_email(self, student, date, marked_by):
        """Send email notification to guardian when student is marked absent"""
        try:
            # Get email settings from Django settings
            email_settings = getattr(settings, 'HOSTELLO_EMAIL_SETTINGS', {})
            
            # Prepare email subject
            subject = email_settings.get(
                'ABSENCE_EMAIL_SUBJECT', 
                '[HOSTELLO ALERT] Student Absence Notification'
            )
            
            # Extract variables to avoid backslash in f-string
            email_signature = email_settings.get('EMAIL_SIGNATURE', 'Best regards,\nHOSTELLO Warden Team')
            warden_name = email_settings.get('WARDEN_NAME', 'HOSTELLO Warden')
            warden_phone = email_settings.get('WARDEN_PHONE', 'Contact hostel office')
            warden_email = email_settings.get('WARDEN_EMAIL', settings.EMAIL_HOST_USER)
            office_hours = email_settings.get('OFFICE_HOURS', '8:00 AM - 8:00 PM')
            hostel_name = email_settings.get('HOSTEL_NAME', 'HOSTELLO - Digital Hostel Management')
            hostel_address = email_settings.get('HOSTEL_ADDRESS', 'College Campus')
            emergency_contact = email_settings.get('EMERGENCY_CONTACT', 'Contact hostel office')
            portal_url = email_settings.get('PORTAL_URL', 'http://127.0.0.1:8000/login/')
            
            # Prepare comprehensive email message
            message = f"""
Dear {student.guardian_name},

This is an automated notification from HOSTELLO - Digital Hostel Management System.

We would like to inform you that your ward, {student.full_name}, was marked ABSENT for room attendance.

STUDENT DETAILS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Admission Number: {student.admission_number}
Full Name: {student.full_name}
Room Number: {student.room_number or 'Not assigned yet'}
Program: {student.program} - {student.discipline}
Room Type: {student.room_type} ({student.ac_type})

ABSENCE INFORMATION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Absence Date: {date.strftime('%A, %d %B %Y')}
Marked By: {marked_by.get_full_name() or marked_by.username}
Marked At: {timezone.now().strftime('%d %B %Y at %I:%M %p')}
Attendance Type: Room Attendance (Overnight Stay)

STUDENT CONTACT INFORMATION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Email: {student.email}
Mobile: {student.mobile}

IMPORTANT NOTES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• If this absence was planned and authorized, please disregard this email.
• If this is incorrect or unauthorized, please contact the warden immediately.
• Regular attendance is mandatory for hostel residents.
• Excessive absences may affect hostel privileges and mess fee calculations.

CONTACT WARDEN:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Warden Name: {warden_name}
Phone: {warden_phone}
Email: {warden_email}
Office Hours: {office_hours}

HOSTEL INFORMATION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{hostel_name}
{hostel_address}

For emergencies, please call: {emergency_contact}

Student Portal: {portal_url}

{email_signature}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This is an automated email. Please do not reply to this message.
For any queries, contact the warden at {warden_email}
            """
            
            # Send email to guardian
            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_list = [student.guardian_email]
            
            print(f"📧 Sending absence email to {student.guardian_name} ({student.guardian_email})")
            print(f"   Student: {student.full_name}")
            print(f"   Date: {date}")
            
            # Send the email
            send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=recipient_list,
                fail_silently=False,
            )
            
            # Also send to student email
            send_mail(
                subject=f"Attendance Alert - {date.strftime('%d %b %Y')}",
                message=f"""
Dear {student.full_name},

You have been marked ABSENT for room attendance on {date.strftime('%A, %d %B %Y')}.

Your guardian ({student.guardian_name}) has been notified via email at {student.guardian_email}.

If this is incorrect, please contact the warden immediately.

Marked by: {marked_by.get_full_name() or marked_by.username}
Time: {timezone.now().strftime('%d %B %Y at %I:%M %p')}

Best regards,
HOSTELLO Warden Team
                """,
                from_email=from_email,
                recipient_list=[student.email],
                fail_silently=True,
            )
            
            print(f"✅ Absence email sent successfully to guardian and student!")
            
            return True
            
        except Exception as e:
            print(f"❌ Error sending absence email: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def send_mess_absence_email(self, student, meal_type, date):
        """Send email notification to guardian for mess absence"""
        try:
            email_settings = getattr(settings, 'HOSTELLO_EMAIL_SETTINGS', {})
            
            # Extract variables to avoid backslash in f-string
            email_signature = email_settings.get('EMAIL_SIGNATURE', 'Best regards,\nHOSTELLO Warden Team')
            warden_phone = email_settings.get('WARDEN_PHONE', 'Contact hostel office')
            warden_email = email_settings.get('WARDEN_EMAIL', settings.EMAIL_HOST_USER)
            
            subject = f"[HOSTELLO] Mess Absence Alert - {student.full_name}"
            
            message = f"""
Dear {student.guardian_name},

This is a notification from HOSTELLO regarding mess attendance.

Your ward, {student.full_name}, was marked ABSENT for {meal_type.upper()} on {date.strftime('%A, %d %B %Y')}.

STUDENT DETAILS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Admission Number: {student.admission_number}
Room Number: {student.room_number or 'Not assigned'}
Program: {student.program} - {student.discipline}

ABSENCE INFORMATION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Date: {date.strftime('%A, %d %B %Y')}
Meal Type: {meal_type.upper()}
Marked At: {timezone.now().strftime('%d %B %Y at %I:%M %p')}

NOTE: Mess absences affect your monthly mess fee calculation. 
If your ward will be away for multiple days, please inform the warden in advance.

Contact Warden: {warden_phone}
Email: {warden_email}

{email_signature}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This is an automated email. Please do not reply.
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[student.guardian_email],
                fail_silently=False,
            )
            
            print(f"✅ Mess absence email sent to {student.guardian_email}")
            return True
            
        except Exception as e:
            print(f"❌ Error sending mess absence email: {str(e)}")
            return False


# Register the enhanced attendance management
admin.site.register(AttendanceStats, AttendanceManagementAdmin)


@admin.register(RoomAttendance)
class RoomAttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'date', 'status', 'marked_by', 'marked_at']
    list_filter = ['status', 'date', 'marked_at']
    search_fields = ['student__full_name', 'student__admission_number']
    readonly_fields = ['marked_by', 'marked_at']
    date_hierarchy = 'date'


@admin.register(MessAttendance)
class MessAttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'date', 'meal_type', 'status', 'marked_by', 'marked_at']
    list_filter = ['status', 'meal_type', 'date', 'marked_at']
    search_fields = ['student__full_name', 'student__admission_number']
    readonly_fields = ['marked_by', 'marked_at']
    date_hierarchy = 'date'


@admin.register(AttendanceNotification)
class AttendanceNotificationAdmin(admin.ModelAdmin):
    list_display = ['student', 'attendance_type', 'date', 'is_read', 'email_sent', 'created_at']
    list_filter = ['attendance_type', 'is_read', 'email_sent', 'date']
    search_fields = ['student__full_name', 'student__admission_number']
    readonly_fields = ['created_at']
    date_hierarchy = 'date'


admin.site.site_header = "HOSTELLO Enhanced Attendance Management"
admin.site.site_title = "HOSTELLO Admin"
admin.site.index_title = "Enhanced Attendance Management System"
