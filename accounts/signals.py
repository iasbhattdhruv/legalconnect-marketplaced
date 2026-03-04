from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Profile


# Create empty profile when user is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


# Generate unique ID safely using primary key
@receiver(post_save, sender=Profile)
def generate_unique_id(sender, instance, created, **kwargs):

    if created and not instance.unique_id:

        if instance.user_type == "lawyer":
            prefix = "LW"
        else:
            prefix = "CL"

        instance.unique_id = f"{prefix}-{instance.id:04d}"

        Profile.objects.filter(id=instance.id).update(unique_id=instance.unique_id)