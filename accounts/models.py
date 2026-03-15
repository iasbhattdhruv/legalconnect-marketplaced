from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta


# =========================
# PROFILE MODEL
# =========================
class Profile(models.Model):

    USER_TYPE_CHOICES = (
        ('client', 'Client'),
        ('lawyer', 'Lawyer'),
    )

    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    unique_id = models.CharField(max_length=20, unique=True, blank=True, null=True)

    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default="client")

    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True)
    birthdate = models.DateField(blank=True, null=True)
    profession = models.CharField(max_length=100, blank=True, null=True)

    specialization = models.CharField(max_length=100, blank=True, null=True)
    experience = models.IntegerField(blank=True, null=True)
    consultation_fee = models.IntegerField(blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)
    signature = models.ImageField(upload_to='signatures/', blank=True, null=True)
    def __str__(self):
        return f"{self.user.username} ({self.unique_id})"


# =========================
# APPOINTMENT MODEL
# =========================
class Appointment(models.Model):

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    )

    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='client_appointments')
    lawyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lawyer_appointments')

    message = models.TextField(blank=True, null=True)

    appointment_date = models.DateField()
    appointment_time = models.TimeField()

    meeting_link = models.URLField(blank=True, null=True)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('lawyer', 'appointment_date', 'appointment_time')
        ordering = ['-appointment_date', '-appointment_time']

    def appointment_datetime(self):
        return timezone.datetime.combine(self.appointment_date, self.appointment_time)

    def can_cancel(self):

        appointment_time = timezone.datetime.combine(self.appointment_date, self.appointment_time)
        appointment_time = timezone.make_aware(appointment_time)

        cancellation_limit = appointment_time - timedelta(hours=12)

        return timezone.now() < cancellation_limit

    def clean(self):

        if self.appointment_date < timezone.now().date():
            raise ValidationError("Cannot book past date.")

        if self.client == self.lawyer:
            raise ValidationError("Cannot book yourself.")

        if hasattr(self.client, 'profile'):
            if self.client.profile.user_type != "client":
                raise ValidationError("Only clients can book.")

    def __str__(self):
        return f"{self.client.username} → {self.lawyer.username} ({self.status})"