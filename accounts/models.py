from django.db import models
from django.contrib.auth.models import User


# =========================
# PROFILE MODEL
# =========================
class Profile(models.Model):

    USER_TYPE_CHOICES = (
        ('client', 'Client'),
        ('lawyer', 'Lawyer'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)

    # Lawyer extra fields
    specialization = models.CharField(max_length=100, blank=True, null=True)
    experience = models.IntegerField(blank=True, null=True)
    consultation_fee = models.IntegerField(blank=True, null=True)
    bio = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.user.username


# =========================
# APPOINTMENT MODEL
# =========================
class Appointment(models.Model):

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    )

    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='client_appointments')
    lawyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lawyer_appointments')

    message = models.TextField()
    appointment_date = models.DateField()
    appointment_time = models.TimeField()

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.client.username} → {self.lawyer.username} ({self.status})"