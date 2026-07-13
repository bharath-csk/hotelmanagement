# attendance/utils.py
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

def send_absence_notification_to_guardian(student, attendance_record):
    """
    Send absence notification email to student's guardian
    """
    try:
        # Check if student has guardian email
        guardian_email = getattr(student, 'guardian_email', None)
        
        if not guardian_email:
            logger.warning(f"No guardian email found for student: {student.name}")
            return False
            
        # Get settings
        email_settings = settings.HOSTELLO_EMAIL_SETTINGS
        
        # Email subject
        subject = email_settings['ABSENCE_EMAIL_SUBJECT']
        
        # Email content for absence notification
        message = f"""
Dear Guardian,

This is an urgent notification from {email_settings['HOSTEL_NAME']}.

🚨 ABSENCE ALERT 🚨

Student Details:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 Student Name: {student.name}
🏠 Room Number: {getattr(student, 'room_number', 'N/A')}
📅 Date: {attendance_record.date.strftime('%A, %d %B %Y')}
⏰ Time: {getattr(attendance_record, 'created_at', timezone.now()).strftime('%I:%M %p')}
📊 Status: ❌ ABSENT
✍️ Marked by: Hostel Warden

Contact Information:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📱 Warden Phone: {email_settings['WARDEN_PHONE']}
📧 Warden Email: {email_settings['WARDEN_EMAIL']}
🕐 Office Hours: {email_settings['OFFICE_HOURS']}
🌐 Student Portal: {email_settings['PORTAL_URL']}

Please contact the warden immediately if you have any concerns regarding your ward's absence.

{email_settings['EMAIL_SIGNATURE']}

═══════════════════════════════════
This is an automated notification from HOSTELLO.
Please save our contact information for future reference.
═══════════════════════════════════
        """
        
        # Send email
        result = send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[guardian_email],
            fail_silently=False,
        )
        
        if result:
            logger.info(f"Absence email sent successfully to {guardian_email} for student {student.name}")
            return True
        else:
            logger.error(f"Failed to send absence email to {guardian_email}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending absence notification: {str(e)}")
        return False
