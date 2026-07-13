# requests/serializers.py - FIXED VERSION
from rest_framework import serializers
from .models import StudentRequest, RequestNotification
from students.models import Student

class StudentRequestSerializer(serializers.ModelSerializer):
    # Display fields
    request_type_display = serializers.CharField(source='get_request_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)

    # Student information
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    student_admission_no = serializers.CharField(source='student.admission_number', read_only=True)
    student_email = serializers.CharField(source='student.email', read_only=True)
    student_mobile = serializers.CharField(source='student.mobile', read_only=True)
    student_room_number = serializers.CharField(source='student.room_number', read_only=True)

    # Processor information
    processed_by_name = serializers.CharField(source='processed_by.username', read_only=True)

    class Meta:
        model = StudentRequest
        fields = [
            # Basic info
            'id', 'student', 'student_name', 'student_admission_no', 'student_email', 
            'student_mobile', 'student_room_number',

            # Request details
            'request_type', 'request_type_display', 'title', 'description', 
            'status', 'status_display', 'priority', 'priority_display',

            # Leave specific
            'from_date', 'to_date', 'leave_reason', 'emergency_contact',

            # Cleaning specific
            'cleaning_type', 'preferred_date', 'preferred_time',

            # Complaint specific
            'complaint_category', 'urgency_level', 'room_number',

            # Processing info
            'warden_response', 'processed_by', 'processed_by_name', 'processed_at',

            # Timestamps
            'created_at', 'updated_at'
        ]
        read_only_fields = ['student', 'processed_by', 'processed_at', 'created_at', 'updated_at']

    def create(self, validated_data):
        # Get student from request context
        request = self.context.get('request')
        if request and hasattr(request.user, 'student'):
            validated_data['student'] = request.user.student
        else:
            # Fallback for testing - get first approved student
            student = Student.objects.filter(status='Approved').first()
            if student:
                validated_data['student'] = student
            else:
                raise serializers.ValidationError("No approved student found")

        return super().create(validated_data)

class StudentRequestUpdateSerializer(serializers.ModelSerializer):
    """Serializer for warden to update request status"""

    class Meta:
        model = StudentRequest
        fields = ['status', 'warden_response']

    def update(self, instance, validated_data):
        # Get the user making the update (warden)
        request = self.context.get('request')

        new_status = validated_data.get('status', instance.status)
        warden_response = validated_data.get('warden_response', instance.warden_response)

        # Use the model methods to handle status updates and notifications
        if new_status == 'approved' and instance.status != 'approved':
            instance.approve(request.user if request else None, warden_response)
        elif new_status == 'rejected' and instance.status != 'rejected':
            instance.reject(request.user if request else None, warden_response)
        elif new_status == 'completed' and instance.status != 'completed':
            instance.complete(request.user if request else None, warden_response)
        else:
            # Regular update
            instance.status = new_status
            instance.warden_response = warden_response
            if request and request.user:
                instance.processed_by = request.user
                from django.utils import timezone
                instance.processed_at = timezone.now()
            instance.save()

        return instance

class RequestNotificationSerializer(serializers.ModelSerializer):
    """RENAMED from StudentNotificationSerializer"""
    # Request details if linked
    request_title = serializers.CharField(source='request.title', read_only=True)
    request_type = serializers.CharField(source='request.request_type', read_only=True)
    request_id = serializers.CharField(source='request.id', read_only=True)

    class Meta:
        model = RequestNotification
        fields = [
            'id', 'title', 'message', 'notification_type', 
            'is_read', 'created_at', 'read_at',
            'request_title', 'request_type', 'request_id'
        ]
        read_only_fields = ['created_at', 'read_at']

class StudentInfoSerializer(serializers.ModelSerializer):
    """Serializer for basic student info"""

    class Meta:
        model = Student
        fields = [
            'id', 'admission_number', 'full_name', 'email', 'mobile', 
            'room_number', 'status', 'created_at'
        ]
        read_only_fields = ['created_at']
