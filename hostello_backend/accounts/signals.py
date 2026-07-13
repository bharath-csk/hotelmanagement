from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, WardenProfile

@receiver(post_save, sender=User)
def create_warden_profile(sender, instance, created, **kwargs):
    """Auto-create warden profile when warden user is created"""
    if created and instance.user_type == 'warden':
        WardenProfile.objects.create(user=instance)
