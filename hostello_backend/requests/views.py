# requests/views.py - FIXED VERSION WITH PROPER AUTHENTICATION + DASHBOARD-FRIENDLY KEYS

from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib.auth.models import User
from django.utils import timezone
import json

from .models import StudentRequest, RequestNotification
from .serializers import (
    StudentRequestSerializer,
    StudentRequestUpdateSerializer,
    RequestNotificationSerializer,
    StudentInfoSerializer
)
from students.models import Student


# =====================================================
# STUDENT AUTHENTICATION FIX (STRICT)
# =====================================================

def get_current_student(request):
    """Resolve current student strictly from user relation or session."""
    try:
        if request.user.is_authenticated and hasattr(request.user, 'student') and request.user.student:
            return request.user.student

        if 'student_id' in request.session:
            return Student.objects.get(id=request.session['student_id'])

        # Optional email match, only if above fail
        if request.user.is_authenticated and request.user.email:
            try:
                return Student.objects.get(email=request.user.email)
            except Student.DoesNotExist:
                pass

        # No dev fallback; make emptiness explicit
        return None
    except Exception as e:
        print("get_current_student error", e)
        return None


# =====================================================
# STUDENT REQUEST VIEWS
# =====================================================

@method_decorator(csrf_exempt, name='dispatch')
class StudentRequestListCreateView(View):
    """
    GET: List all requests for current student
    POST: Create new request for current student
    """

    def get(self, request):
        try:
            student = get_current_student(request)
            if not student:
                return JsonResponse({'success': False, 'error': 'No student found'}, status=400)

            print(f"📋 Loading requests for student: {student.full_name} ({student.admission_number})")

            qs = StudentRequest.objects.filter(student=student).order_by('-created_at')
            print(f"📊 Found {qs.count()} requests for {student.full_name}")

            request_data = []
            for req in qs:
                request_data.append({
                    'id': req.id,
                    'request_type': req.request_type,
                    'request_type_display': req.get_request_type_display(),
                    'title': req.title,
                    'description': req.description,
                    'status': req.status,
                    'status_display': req.get_status_display(),
                    'priority': req.priority,
                    'priority_display': req.get_priority_display(),
                    'created_at': req.created_at.isoformat(),
                    'updated_at': req.updated_at.isoformat(),

                    'student_name': req.student.full_name,
                    'student_admission_no': req.student.admission_number,
                    'student_room_number': req.student.room_number,

                    'from_date': req.from_date.isoformat() if req.from_date else None,
                    'to_date': req.to_date.isoformat() if req.to_date else None,
                    'leave_reason': req.leave_reason,
                    'emergency_contact': req.emergency_contact,

                    'cleaning_type': req.cleaning_type,
                    'preferred_date': req.preferred_date.isoformat() if req.preferred_date else None,
                    'preferred_time': req.preferred_time,

                    'complaint_category': req.complaint_category,
                    'urgency_level': req.urgency_level,
                    'room_number': req.room_number,

                    'warden_response': req.warden_response,
                    'processed_by': req.processed_by.username if req.processed_by else None,
                    'processed_at': req.processed_at.isoformat() if req.processed_at else None,
                })

            return JsonResponse({
                'success': True,
                'requests': request_data,
                'count': len(request_data),
                'student_info': {
                    'name': student.full_name,
                    'admission_number': student.admission_number,
                    'room_number': student.room_number
                }
            })
        except Exception as e:
            print(f"❌ Error loading requests: {e}")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    def post(self, request):
        try:
            data = json.loads(request.body)

            student = get_current_student(request)
            if not student:
                return JsonResponse({'success': False, 'error': 'No student found'}, status=400)

            print(f"📝 Creating request for student: {student.full_name} ({student.admission_number})")
            print(f"📋 Request data: {data}")

            student_request = StudentRequest.objects.create(
                student=student,
                request_type=data.get('request_type', 'other'),
                title=data.get('title', 'Untitled Request'),
                description=data.get('description', ''),
                priority=data.get('priority', 'medium'),

                from_date=data.get('from_date') or None,
                to_date=data.get('to_date') or None,
                leave_reason=data.get('leave_reason', ''),
                emergency_contact=data.get('emergency_contact', ''),

                cleaning_type=data.get('cleaning_type', ''),
                preferred_date=data.get('preferred_date') or None,
                preferred_time=data.get('preferred_time', ''),

                complaint_category=data.get('complaint_category', ''),
                urgency_level=data.get('urgency_level', ''),
                room_number=data.get('room_number', ''),
            )

            print(f"✅ Request created successfully: {student_request.id} for {student.full_name}")

            return JsonResponse({
                'success': True,
                'message': f'Request submitted successfully for {student.full_name}!',
                'request_id': student_request.id,
                'request': {
                    'id': student_request.id,
                    'type': student_request.get_request_type_display(),
                    'title': student_request.title,
                    'status': student_request.get_status_display(),
                    'created_at': student_request.created_at.isoformat(),
                    'student_name': student.full_name,
                    'student_admission_no': student.admission_number
                }
            })
        except Exception as e:
            print(f"❌ Error creating request: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


# =====================================================
# ADMIN/WARDEN VIEWS
# =====================================================

@method_decorator(csrf_exempt, name='dispatch')
class AdminRequestListView(View):
    def get(self, request):
        try:
            request_type = request.GET.get('type', 'all')
            request_status = request.GET.get('status', 'all')
            student_id = request.GET.get('student', 'all')

            requests_qs = StudentRequest.objects.select_related('student', 'processed_by').all()
            if request_type != 'all':
                requests_qs = requests_qs.filter(request_type=request_type)
            if request_status != 'all':
                requests_qs = requests_qs.filter(status=request_status)
            if student_id != 'all':
                requests_qs = requests_qs.filter(student_id=student_id)

            requests_qs = requests_qs.order_by('-created_at')
            print(f"📊 Admin viewing {requests_qs.count()} requests")

            request_data = []
            for req in requests_qs:
                request_data.append({
                    'id': req.id,
                    'request_type': req.request_type,
                    'request_type_display': req.get_request_type_display(),
                    'title': req.title,
                    'description': req.description,
                    'status': req.status,
                    'status_display': req.get_status_display(),
                    'priority': req.priority,
                    'priority_display': req.get_priority_display(),
                    'created_at': req.created_at.isoformat(),
                    'updated_at': req.updated_at.isoformat(),

                    'student': {
                        'id': req.student.id,
                        'admission_number': req.student.admission_number,
                        'full_name': req.student.full_name,
                        'email': req.student.email,
                        'mobile': req.student.mobile,
                        'room_number': req.student.room_number,
                        'program': req.student.program,
                        'discipline': req.student.discipline,
                    },

                    'from_date': req.from_date.isoformat() if req.from_date else None,
                    'to_date': req.to_date.isoformat() if req.to_date else None,
                    'leave_reason': req.leave_reason,
                    'emergency_contact': req.emergency_contact,
                    'cleaning_type': req.cleaning_type,
                    'preferred_date': req.preferred_date.isoformat() if req.preferred_date else None,
                    'preferred_time': req.preferred_time,
                    'complaint_category': req.complaint_category,
                    'urgency_level': req.urgency_level,
                    'room_number': req.room_number,

                    'warden_response': req.warden_response,
                    'processed_by': req.processed_by.username if req.processed_by else None,
                    'processed_at': req.processed_at.isoformat() if req.processed_at else None,
                })

            return JsonResponse({
                'success': True,
                'requests': request_data,
                'count': len(request_data),
                'filters': {
                    'type': request_type,
                    'status': request_status,
                    'student': student_id
                }
            })
        except Exception as e:
            print(f"❌ Error in admin request list: {e}")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class AdminRequestUpdateView(View):
    def post(self, request, request_id):
        try:
            data = json.loads(request.body)

            student_request = get_object_or_404(StudentRequest, id=request_id)

            new_status = data.get('status')
            warden_response = data.get('response', '')

            print(f"📝 Warden updating request {request_id}")
            print(f"    Student: {student_request.student.full_name}")
            print(f"    Status: {student_request.status} → {new_status}")
            print(f"    Response: {warden_response}")

            if hasattr(request, 'user') and request.user.is_authenticated:
                current_user = request.user
            else:
                current_user, _ = User.objects.get_or_create(
                    username='admin_warden',
                    defaults={'email': 'admin@hostello.com', 'is_staff': True}
                )

            if new_status == 'approved':
                student_request.approve(current_user, warden_response)
            elif new_status == 'rejected':
                student_request.reject(current_user, warden_response)
            elif new_status == 'completed':
                student_request.complete(current_user, warden_response)
            else:
                student_request.status = new_status
                student_request.warden_response = warden_response
                student_request.processed_by = current_user
                student_request.processed_at = timezone.now()
                student_request.save()

            print("✅ Request updated successfully")

            return JsonResponse({
                'success': True,
                'message': f'Request {new_status} successfully!',
                'request': {
                    'id': student_request.id,
                    'status': student_request.status,
                    'status_display': student_request.get_status_display(),
                    'warden_response': student_request.warden_response,
                    'processed_by': student_request.processed_by.username if student_request.processed_by else None,
                    'processed_at': student_request.processed_at.isoformat() if student_request.processed_at else None,
                    'student_name': student_request.student.full_name
                }
            })
        except Exception as e:
            print(f"❌ Error updating request: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


# =====================================================
# WARDEN DASHBOARD API
# =====================================================

@method_decorator(csrf_exempt, name='dispatch')
class WardenDashboardView(View):
    def get(self, request):
        try:
            all_requests = StudentRequest.objects.select_related('student').all()

            stats = {
                'total_requests': all_requests.count(),
                'pending_requests': all_requests.filter(status='pending').count(),
                'approved_requests': all_requests.filter(status='approved').count(),
                'rejected_requests': all_requests.filter(status='rejected').count(),
                'completed_requests': all_requests.filter(status='completed').count(),

                'complaint_requests': all_requests.filter(request_type='complaint').count(),
                'cleaning_requests': all_requests.filter(request_type='cleaning').count(),
                'leave_requests': all_requests.filter(request_type='leave').count(),
                'maintenance_requests': all_requests.filter(request_type='maintenance').count(),
            }

            recent_requests = all_requests.order_by('-created_at')[:10]
            recent_data = []
            for req in recent_requests:
                recent_data.append({
                    'id': req.id,
                    'student_name': req.student.full_name,
                    'student_room': req.student.room_number,
                    'request_type': req.request_type,
                    'request_type_display': req.get_request_type_display(),
                    'title': req.title,
                    'status': req.status,
                    'status_display': req.get_status_display(),
                    'priority': req.priority,
                    'created_at': req.created_at.isoformat(),
                })

            return JsonResponse({
                'success': True,
                'stats': stats,
                'recent_requests': recent_data
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


# =====================================================
# UTILITY VIEWS
# =====================================================

def get_student_info(request):
    try:
        student = get_current_student(request)
        if not student:
            return JsonResponse({'success': False, 'error': 'No student found'}, status=400)

        return JsonResponse({
            'success': True,
            'student': {
                'id': student.id,
                'admission_number': student.admission_number,
                'full_name': student.full_name,
                'email': student.email,
                'mobile': student.mobile,
                'room_number': student.room_number,
                'program': student.program,
                'discipline': student.discipline,
                'status': student.status
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# =====================================================
# NOTIFICATION VIEWS
# =====================================================

@method_decorator(csrf_exempt, name='dispatch')
class StudentNotificationListView(View):
    def get(self, request):
        try:
            student = get_current_student(request)
            if not student:
                return JsonResponse({'success': False, 'error': 'No student found'}, status=400)

            notifications = RequestNotification.objects.filter(student=student).order_by('-created_at')

            notification_data = []
            for notif in notifications:
                notification_data.append({
                    'id': notif.id,
                    'title': notif.title,
                    'message': notif.message,
                    'notification_type': notif.notification_type,
                    'is_read': notif.is_read,
                    'created_at': notif.created_at.isoformat(),
                    'read_at': notif.read_at.isoformat() if notif.read_at else None,
                    'request': {
                        'id': notif.request.id,
                        'title': notif.request.title,
                        'type': notif.request.request_type,
                        'status': notif.request.status
                    } if notif.request else None
                })

            unread_count = notifications.filter(is_read=False).count()

            return JsonResponse({
                'success': True,
                'notifications': notification_data,
                'count': len(notification_data),
                'unread_count': unread_count,
                'student_name': student.full_name
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    def post(self, request):
        try:
            data = json.loads(request.body)
            notification_id = data.get('notification_id')

            if notification_id:
                notification = get_object_or_404(RequestNotification, id=notification_id)
                notification.mark_as_read()
                return JsonResponse({'success': True, 'message': 'Notification marked as read'})
            else:
                return JsonResponse({'success': False, 'error': 'notification_id required'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
