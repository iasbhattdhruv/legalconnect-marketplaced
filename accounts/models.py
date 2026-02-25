from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    USER_TYPES = (
        ('client', 'Client'),
        ('lawyer', 'Lawyer'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='client')
    specialization = models.CharField(max_length=100, blank=True, null=True)
    experience = models.IntegerField(blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    is_approved = models.BooleanField(default=False)
    def __str__(self):
        return self.user.username


class Appointment(models.Model):
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name="client_appointments")
    lawyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="lawyer_appointments")
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.client.username} -> {self.lawyer.username}"