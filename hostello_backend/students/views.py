# students/views.py - UPDATED WITH ATTENDANCE INTEGRATION

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Q
import json
import datetime
from .models import Student, Room
from .forms import StudentRegistrationForm, StudentLoginForm
from django.contrib.auth.hashers import make_password, check_password
# Add to existing imports
from notices.models import Notice, NoticeReadStatus


# Import attendance models with error handling
try:
    from attendance.models import RoomAttendance, MessAttendance, AttendanceNotification
    ATTENDANCE_AVAILABLE = True
    print("Attendance models imported successfully")
except ImportError:
    ATTENDANCE_AVAILABLE = False
    print("Attendance models not available")

def home_view(request):
    return render(request, 'home.html')

def register_view(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            student = form.save(commit=False)
            student.password = make_password(form.cleaned_data['password'])
            student.save()

            messages.success(request, 'Registration submitted successfully! You will receive an email once approved.')
            return redirect('login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = StudentRegistrationForm()

    return render(request, 'index.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = StudentLoginForm(request.POST)
        if form.is_valid():
            admission_number = form.cleaned_data['admission_number']
            password = form.cleaned_data['password']

            try:
                student = Student.objects.get(admission_number=admission_number)
                if check_password(password, student.password) and student.status == 'Approved':
                    # Store additional session data for attendance tracking
                    request.session['student_id'] = student.id
                    request.session['student_name'] = student.full_name
                    request.session['student_admission'] = student.admission_number
                    request.session['student_status'] = student.status

                    messages.success(request, f'Welcome back, {student.full_name}!')
                    return redirect('dashboard')
                else:
                    if student.status != 'Approved':
                        messages.error(request, 'Your application is still pending approval.')
                    else:
                        messages.error(request, 'Invalid credentials.')
            except Student.DoesNotExist:
                messages.error(request, 'Student not found.')
    else:
        form = StudentLoginForm()

    return render(request, 'login.html', {'form': form})

def dashboard_view(request):
    """Enhanced dashboard with attendance integration and mess fee calculations"""
    if 'student_id' not in request.session:
        return redirect('login')

    student = get_object_or_404(Student, id=request.session['student_id'])

    # Initialize context with basic student info
    context = {
        'student': student,
        'room_attendance': [],
        'mess_attendance': [],
        'total_room_days': 0,
        'room_present': 0,
        'room_absent': 0,
        'room_percentage': 0,
        'total_mess_entries': 0,
        'mess_present': 0,
        'mess_absent': 0,
        'mess_percentage': 0,
        'notifications': [],
        'unread_count': 0,
        'today_room_attendance': None,
        'today_mess_attendance': [],
        # ✅ NEW: Mess fee calculation fields
        'mess_rebate_amount': 0,
        'final_mess_fee': 4500,
        'hostel_fee': 0,
        'total_monthly_fee': 0,
        'is_rebate_eligible': False,
    }

    # Add attendance data if available
    if ATTENDANCE_AVAILABLE and student.status == 'Approved':
        try:
            # Get current month data for mess fee calculation
            current_date = timezone.now().date()
            current_month = current_date.month
            current_year = current_date.year
            
            # Get first and last day of current month
            first_day = datetime.datetime(current_year, current_month, 1).date()
            import calendar
            last_day = datetime.datetime(current_year, current_month, calendar.monthrange(current_year, current_month)[1]).date()
            
            # Get current month mess attendance for rebate calculation
            current_month_mess = MessAttendance.objects.filter(
                student=student,
                date__range=[first_day, last_day]
            )
            
            # Count absent days in current month
            mess_absent_current_month = current_month_mess.filter(status='absent').count()
            
            # Get all-time attendance records
            room_attendance = RoomAttendance.objects.filter(student=student).order_by('-date')
            mess_attendance = MessAttendance.objects.filter(student=student).order_by('-date')

            # Calculate all-time statistics
            total_room_days = room_attendance.count()
            room_present = room_attendance.filter(status='present').count()
            room_absent = room_attendance.filter(status='absent').count()

            total_mess_entries = mess_attendance.count()
            mess_present = mess_attendance.filter(status='present').count()
            mess_absent = mess_attendance.filter(status='absent').count()

            # Calculate percentages
            room_percentage = round((room_present / total_room_days * 100), 2) if total_room_days > 0 else 0
            mess_percentage = round((mess_present / total_mess_entries * 100), 2) if total_mess_entries > 0 else 0

            # ✅ MESS FEE CALCULATION
            base_mess_fee = 4500
            is_rebate_eligible = mess_absent_current_month >= 4
            mess_rebate_amount = mess_absent_current_month * 150 if is_rebate_eligible else 0
            final_mess_fee = base_mess_fee - mess_rebate_amount
            
            # ✅ HOSTEL FEE CALCULATION
            hostel_fee = 2000  # Base fee for 4 seater
            
            # Room type increments
            if student.room_type == '1 Seater':
                hostel_fee += 1500
            elif student.room_type == '2 Seater':
                hostel_fee += 1000
            elif student.room_type == '3 Seater':
                hostel_fee += 500
            # 4 Seater remains at base price
            
            # A/C increment
            if student.ac_type and ('A/C' in student.ac_type or 'AC' in student.ac_type):
                hostel_fee += 1000
            
            # Total monthly fee
            total_monthly_fee = hostel_fee + final_mess_fee

            # Get recent records (last 30 days)
            thirty_days_ago = timezone.now().date() - datetime.timedelta(days=30)
            recent_room_attendance = room_attendance.filter(date__gte=thirty_days_ago)[:15]
            recent_mess_attendance = mess_attendance.filter(date__gte=thirty_days_ago)[:15]

            # Get notifications
            notifications = AttendanceNotification.objects.filter(student=student).order_by('-created_at')
            unread_notifications = notifications.filter(is_read=False)
            recent_notifications = notifications[:10]

            # Get today's attendance
            today = timezone.now().date()
            today_room_attendance = RoomAttendance.objects.filter(student=student, date=today).first()
            today_mess_attendance = MessAttendance.objects.filter(student=student, date=today)

            # Update context with all data
            context.update({
                'room_attendance': recent_room_attendance,
                'mess_attendance': recent_mess_attendance,
                'total_room_days': total_room_days,
                'room_present': room_present,
                'room_absent': room_absent,
                'room_percentage': room_percentage,
                'total_mess_entries': total_mess_entries,
                'mess_present': mess_present,
                'mess_absent': mess_absent_current_month,  # ✅ Current month absent days for rebate
                'mess_percentage': mess_percentage,
                'notifications': recent_notifications,
                'unread_count': unread_notifications.count(),
                'today_room_attendance': today_room_attendance,
                'today_mess_attendance': today_mess_attendance,
                # ✅ Mess fee calculation data
                'mess_rebate_amount': mess_rebate_amount,
                'final_mess_fee': final_mess_fee,
                'hostel_fee': hostel_fee,
                'total_monthly_fee': total_monthly_fee,
                'is_rebate_eligible': is_rebate_eligible,
                'base_mess_fee': base_mess_fee,
            })

            print(f"✅ Attendance data loaded for {student.full_name}")
            print(f"   Room: {total_room_days} days, {room_present} present, {room_absent} absent")
            print(f"   Current month mess absent: {mess_absent_current_month}")
            print(f"   Mess fee: ₹{final_mess_fee} (rebate: ₹{mess_rebate_amount})")
            print(f"   Hostel fee: ₹{hostel_fee}")
            print(f"   Total: ₹{total_monthly_fee}")

        except Exception as e:
            print(f"⚠️ Error loading attendance data: {e}")
            # Set default values for mess fee calculation
            context.update({
                'mess_absent': 0,
                'mess_rebate_amount': 0,
                'final_mess_fee': 4500,
                'hostel_fee': 2000,
                'total_monthly_fee': 6500,
                'is_rebate_eligible': False,
                'base_mess_fee': 4500,
            })
        # GET NOTICES FOR STUDENT
    try:
        # Get active notices for this student
        current_time = timezone.now()
        
        # Filter notices based on audience targeting
        student_notices = Notice.objects.filter(
            is_active=True,
            publish_date__lte=current_time
        ).filter(
            Q(expiry_date__isnull=True) | Q(expiry_date__gte=current_time)
        ).filter(
            Q(audience='all') |  # All students
            Q(audience='specific_room', target_room=student.room_number) |  # Specific room
            Q(audience='individual', target_student=student)  # Individual student
        ).order_by('-publish_date')[:10]
        
        # Get read status for each notice
        read_notice_ids = NoticeReadStatus.objects.filter(
            student=student,
            notice__in=student_notices
        ).values_list('notice_id', flat=True)
        
        # Prepare notices data with read status
        notices_data = []
        unread_notices_count = 0
        
        for notice in student_notices:
            is_read = notice.id in read_notice_ids
            if not is_read:
                unread_notices_count += 1
                
            notices_data.append({
                'notice': notice,
                'is_read': is_read,
                'is_new': (current_time - notice.publish_date).days < 3,  # New if posted within 3 days
            })
        
        # Add to context
        context.update({
            'notices': notices_data,
            'unread_notices_count': unread_notices_count,
            'total_unread': context.get('unread_count', 0) + unread_notices_count,  # Combine with attendance notifications
        })
        
        print(f"✅ Loaded {len(notices_data)} notices for {student.full_name}")
        print(f"   Unread notices: {unread_notices_count}")
        
    except Exception as e:
        print(f"⚠️ Error loading notices: {e}")
        import traceback
        traceback.print_exc()
        context.update({
            'notices': [],
            'unread_notices_count': 0,
            'total_unread': context.get('unread_count', 0),
        })

    return render(request, 'dashboard.html', context)     
        

   

def logout_view(request):
    request.session.flush()
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')

# ✅ NEW: API endpoints for attendance data
def get_attendance_data(request):
    """API endpoint for attendance data"""
    if 'student_id' not in request.session or not ATTENDANCE_AVAILABLE:
        return JsonResponse({'error': 'Not available'}, status=400)

    try:
        student = Student.objects.get(id=request.session['student_id'])

        # Get last 30 days attendance
        thirty_days_ago = timezone.now().date() - datetime.timedelta(days=30)
        room_attendance = RoomAttendance.objects.filter(
            student=student, 
            date__gte=thirty_days_ago
        ).order_by('date')

        mess_attendance = MessAttendance.objects.filter(
            student=student, 
            date__gte=thirty_days_ago
        ).order_by('date')

        # Format data for frontend
        attendance_data = []
        for attendance in room_attendance:
            mess_data = mess_attendance.filter(date=attendance.date)

            attendance_data.append({
                'date': attendance.date.strftime('%Y-%m-%d'),
                'date_formatted': attendance.date.strftime('%d %b'),
                'room_status': attendance.status,
                'breakfast_status': mess_data.filter(meal_type='breakfast').first().status if mess_data.filter(meal_type='breakfast').exists() else 'not_marked',
                'lunch_status': mess_data.filter(meal_type='lunch').first().status if mess_data.filter(meal_type='lunch').exists() else 'not_marked',
                'dinner_status': mess_data.filter(meal_type='dinner').first().status if mess_data.filter(meal_type='dinner').exists() else 'not_marked',
            })

        return JsonResponse({
            'success': True,
            'attendance_data': attendance_data,
            'stats': {
                'room_present': room_attendance.filter(status='present').count(),
                'room_absent': room_attendance.filter(status='absent').count(),
                'mess_present': mess_attendance.filter(status='present').count(),
                'mess_absent': mess_attendance.filter(status='absent').count(),
            }
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ✅ NEW: Get notifications for student
def get_notifications(request):
    """Get notifications for student"""
    if 'student_id' not in request.session or not ATTENDANCE_AVAILABLE:
        return JsonResponse({'error': 'Not available'}, status=400)

    try:
        student = Student.objects.get(id=request.session['student_id'])
        notifications = AttendanceNotification.objects.filter(student=student).order_by('-created_at')

        notifications_data = []
        for notification in notifications:
            notifications_data.append({
                'id': notification.id,
                'type': notification.attendance_type,
                'message': notification.message,
                'date': notification.date.strftime('%d %b, %Y'),
                'created_at': notification.created_at.strftime('%d %b, %Y %H:%M'),
                'is_read': notification.is_read,
                'email_sent': notification.email_sent,
            })

        return JsonResponse({
            'success': True,
            'notifications': notifications_data,
            'unread_count': notifications.filter(is_read=False).count()
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ✅ NEW: Mark notification as read
def mark_notification_read(request):
    """Mark notification as read"""
    if request.method != 'POST' or not ATTENDANCE_AVAILABLE:
        return JsonResponse({'error': 'Invalid request'}, status=400)

    if 'student_id' not in request.session:
        return JsonResponse({'error': 'Not authenticated'}, status=401)

    try:
        notification_id = request.POST.get('notification_id')
        student = Student.objects.get(id=request.session['student_id'])
        notification = AttendanceNotification.objects.get(id=notification_id, student=student)
        notification.is_read = True
        notification.save()

        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def send_approval_email(student):
    """Send email notification to student and guardian after approval"""
    subject = 'HOSTELLO - Registration Approved!'

    message_content = f"""
Dear {student.full_name},

Congratulations! Your hostel registration has been approved.

Your Login Details:
- Admission Number: {student.admission_number}
- Password: (Use the password you set during registration)
- Room Number: {student.room_number}
- Room Type: {student.room_type} ({student.ac_type})

Login Link: http://127.0.0.1:8000/login/

Please login to access your student dashboard where you can:
✅ View your attendance records
✅ Check notifications from the hostel administration
✅ Monitor your academic progress
✅ Access fee payment information

Welcome to HOSTELLO!

Best regards,
Hostel Management Team
    """

    try:
        send_mail(
            subject,
            message_content,
            settings.DEFAULT_FROM_EMAIL,
            [student.email, student.guardian_email],
            fail_silently=False,
        )
        print(f"✅ Approval email sent to {student.full_name}")
        return True
    except Exception as e:
        print(f"❌ Email sending failed: {e}")
        return False
    
# ✅ NEW: Get notices for student
def get_notices(request):
    """API endpoint to get notices for student"""
    if 'student_id' not in request.session:
        return JsonResponse({'error': 'Not authenticated'}, status=401)

    try:
        student = Student.objects.get(id=request.session['student_id'])
        current_time = timezone.now()
        
        # Get active notices for this student
        student_notices = Notice.objects.filter(
            is_active=True,
            publish_date__lte=current_time
        ).filter(
            Q(expiry_date__isnull=True) | Q(expiry_date__gte=current_time)
        ).filter(
            Q(audience='all') |
            Q(audience='specific_room', target_room=student.room_number) |
            Q(audience='individual', target_student=student)
        ).order_by('-publish_date')

        # Get read status
        read_notice_ids = NoticeReadStatus.objects.filter(
            student=student,
            notice__in=student_notices
        ).values_list('notice_id', flat=True)

        # Format notices data
        notices_data = []
        for notice in student_notices:
            is_read = notice.id in read_notice_ids
            notices_data.append({
                'id': notice.id,
                'title': notice.title,
                'message': notice.message,
                'priority': notice.priority,
                'priority_display': notice.get_priority_display(),
                'audience': notice.get_target_display(),
                'publish_date': notice.publish_date.strftime('%d %b, %Y %H:%M'),
                'expiry_date': notice.expiry_date.strftime('%d %b, %Y') if notice.expiry_date else None,
                'is_read': is_read,
                'is_new': (current_time - notice.publish_date).days < 3,
                'created_by': notice.created_by.get_full_name() or notice.created_by.username,
            })

        unread_count = len([n for n in notices_data if not n['is_read']])

        return JsonResponse({
            'success': True,
            'notices': notices_data,
            'unread_count': unread_count,
            'total_count': len(notices_data)
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ✅ NEW: Mark notice as read
def mark_notice_read(request):
    """Mark a notice as read"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request'}, status=400)

    if 'student_id' not in request.session:
        return JsonResponse({'error': 'Not authenticated'}, status=401)

    try:
        notice_id = request.POST.get('notice_id')
        student = Student.objects.get(id=request.session['student_id'])
        notice = Notice.objects.get(id=notice_id)

        # Create or get read status
        read_status, created = NoticeReadStatus.objects.get_or_create(
            notice=notice,
            student=student
        )

        return JsonResponse({
            'success': True,
            'message': 'Notice marked as read',
            'was_new': created
        })

    except Notice.DoesNotExist:
        return JsonResponse({'error': 'Notice not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ✅ NEW: Get combined notifications (attendance alerts + notices)
def get_combined_notifications(request):
    """Get both attendance notifications and notices combined"""
    if 'student_id' not in request.session:
        return JsonResponse({'error': 'Not authenticated'}, status=401)

    try:
        student = Student.objects.get(id=request.session['student_id'])
        current_time = timezone.now()
        combined_notifications = []

        # Get attendance notifications
        if ATTENDANCE_AVAILABLE:
            attendance_notifications = AttendanceNotification.objects.filter(
                student=student
            ).order_by('-created_at')[:20]

            for notif in attendance_notifications:
                combined_notifications.append({
                    'id': f'attendance_{notif.id}',
                    'type': 'attendance',
                    'category': notif.attendance_type,
                    'title': f'Attendance Alert - {notif.date.strftime("%d %b, %Y")}',
                    'message': notif.message,
                    'date': notif.created_at.strftime('%d %b, %Y %H:%M'),
                    'is_read': notif.is_read,
                    'priority': 'high',
                    'icon': 'calendar-x',
                })

        # Get notices
        student_notices = Notice.objects.filter(
            is_active=True,
            publish_date__lte=current_time
        ).filter(
            Q(expiry_date__isnull=True) | Q(expiry_date__gte=current_time)
        ).filter(
            Q(audience='all') |
            Q(audience='specific_room', target_room=student.room_number) |
            Q(audience='individual', target_student=student)
        ).order_by('-publish_date')[:20]

        read_notice_ids = NoticeReadStatus.objects.filter(
            student=student,
            notice__in=student_notices
        ).values_list('notice_id', flat=True)

        for notice in student_notices:
            is_read = notice.id in read_notice_ids
            combined_notifications.append({
                'id': f'notice_{notice.id}',
                'type': 'notice',
                'category': notice.audience,
                'title': notice.title,
                'message': notice.message,
                'date': notice.publish_date.strftime('%d %b, %Y %H:%M'),
                'is_read': is_read,
                'priority': notice.priority,
                'icon': 'bell',
                'created_by': notice.created_by.get_full_name() or notice.created_by.username,
            })

        # Sort by date (most recent first)
        combined_notifications.sort(key=lambda x: x['date'], reverse=True)

        # Count unread
        unread_count = len([n for n in combined_notifications if not n['is_read']])

        return JsonResponse({
            'success': True,
            'notifications': combined_notifications,
            'unread_count': unread_count,
            'total_count': len(combined_notifications)
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

    
    
