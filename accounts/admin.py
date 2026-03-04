from django.contrib import admin
from .models import Profile, Appointment


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'unique_id',
        'user_type',
        'gender',
        'birthdate',
        'profession',
        'specialization',
        'experience',
        'consultation_fee',
    )


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        'client',
        'lawyer',
        'appointment_date',
        'appointment_time',
        'status',
    )
    list_filter = ('status',)