from django.contrib import admin
from .models import Profile, Appointment


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_type', 'specialization', 'experience', 'location')
    list_filter = ('user_type',)
    search_fields = ('user__username',)


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('client', 'lawyer', 'created_at')