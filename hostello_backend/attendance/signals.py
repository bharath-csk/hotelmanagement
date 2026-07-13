# attendance/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import RoomAttendance, MessAttendance  # Adjust based on your models
from .utils import send_absence_notification_to_guardian
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=RoomAttendance)
def send_absence_email_for_room_attendance(sender, instance, created, **kwargs):
    """
    Send email notification to guardian when student is marked absent in room attendance
    """
    try:
        # Only send email for absent students and new records
        if created and not instance.is_present:  # Assuming is_present field exists
            student = instance.student
            
            # Check if absence email is enabled
            if settings.HOSTELLO_EMAIL_SETTINGS.get('SEND_ABSENCE_EMAIL', False):
                result = send_absence_notification_to_guardian(student, instance)
                
                if result:
                    logger.info(f"Room absence email sent for {student.name}")
                else:
                    logger.warning(f"Failed to send room absence email for {student.name}")
            else:
                logger.info("Absence email notifications are disabled in settings")
                
    except Exception as e:
        logger.error(f"Error in room attendance absence email signal: {str(e)}")

@receiver(post_save, sender=MessAttendance)
def send_absence_email_for_mess_attendance(sender, instance, created, **kwargs):
    """
    Send email notification to guardian when student is marked absent in mess attendance
    """
    try:
        # Only send email for absent students and new records
        if created and not instance.is_present:  # Assuming is_present field exists
            student = instance.student
            
            # Check if absence email is enabled
            if settings.HOSTELLO_EMAIL_SETTINGS.get('SEND_ABSENCE_EMAIL', False):
                result = send_absence_notification_to_guardian(student, instance)
                
                if result:
                    logger.info(f"Mess absence email sent for {student.name}")
                else:
                    logger.warning(f"Failed to send mess absence email for {student.name}")
            else:
                logger.info("Absence email notifications are disabled in settings")
                
    except Exception as e:
        logger.error(f"Error in mess attendance absence email signal: {str(e)}")
